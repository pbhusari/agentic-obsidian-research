from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from vantage.config import cfg

app = typer.Typer(help="VANTAGE — Agentic Security Research Pipeline for Obsidian")
console = Console()


@app.command()
def run(
    n: int = typer.Option(cfg.pipeline.top_n, "--n", help="Number of papers to retrieve"),
    months: int = typer.Option(cfg.pipeline.months_back, "--months", help="Lookback window in months"),
    synthesis_only: bool = typer.Option(False, "--synthesis-only", help="Skip paper extraction, re-synthesize only"),
    fast_model: Optional[str] = typer.Option(None, "--fast-model", help="Override fast model"),
    synthesis_model: Optional[str] = typer.Option(None, "--synthesis-model", help="Override synthesis model"),
    extra_query: Optional[str] = typer.Option(None, "--extra-query", help="Add a one-off query"),
) -> None:
    """Run the full VANTAGE pipeline."""
    from vantage.llm.models import MODEL_ALIASES

    if fast_model:
        MODEL_ALIASES["fast"] = fast_model
    if synthesis_model:
        MODEL_ALIASES["synthesis"] = synthesis_model
    if extra_query:
        cfg.pipeline.extra_queries.append(extra_query)

    asyncio.run(_run_pipeline(n, months, synthesis_only))


async def _run_pipeline(n: int, months: int, synthesis_only: bool) -> None:
    from vantage.extraction.paper_extractor import extract_all
    from vantage.obsidian.vault_init import init_vault
    from vantage.obsidian.writer import VaultWriter
    from vantage.retrieval.arxiv_client import fetch_papers
    from vantage.retrieval.s2_client import enrich_with_citations
    from vantage.synthesis.concept_clusterer import cluster_concepts
    from vantage.synthesis.taxonomy_builder import build_taxonomy

    vault_path = cfg.obsidian.vault_path
    init_vault(vault_path)
    writer = VaultWriter(vault_path)

    papers = []

    _spinner_cols = [
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
    ]
    _bar_cols = [
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
    ]

    if not synthesis_only:
        with Progress(*_spinner_cols, console=console) as progress:
            t_fetch = progress.add_task("[cyan]Fetching papers from arXiv...[/cyan]", total=None)
            paper_metas = await fetch_papers(n, months)
            progress.update(t_fetch, description=f"[cyan]Enriching {len(paper_metas)} papers with citations...[/cyan]")
            paper_metas = await enrich_with_citations(paper_metas)
            progress.update(t_fetch, description=f"[green]Fetched & enriched {len(paper_metas)} papers[/green]", completed=1, total=1)

        with Progress(*_bar_cols, console=console) as progress:
            t_extract = progress.add_task(
                "[cyan]Extracting intelligence...[/cyan]",
                total=len(paper_metas),
            )

            def _on_paper_done(paper):
                label = paper.title[:48] + "..." if paper and len(paper.title) > 48 else (paper.title if paper else "skipped")
                progress.update(
                    t_extract,
                    advance=1,
                    description=f"[cyan]Extracting:[/cyan] [dim]{label}[/dim]",
                )

            papers = await extract_all(paper_metas, on_done=_on_paper_done)
            progress.update(t_extract, description=f"[green]Extracted {len(papers)}/{len(paper_metas)} papers[/green]")

        for p in papers:
            writer.write_paper(p)
    else:
        console.print("[yellow]synthesis-only: skipping paper extraction[/yellow]")
        console.print("[yellow]Warning: synthesis-only without cached JSON is limited.[/yellow]")

    with Progress(*_spinner_cols, console=console) as progress:
        t_concepts = progress.add_task("[cyan]Synthesizing concept clusters...[/cyan]", total=None)
        concepts = await cluster_concepts(papers)
        progress.update(t_concepts, description=f"[green]Synthesized {len(concepts)} concept clusters[/green]", completed=1, total=1)

    with Progress(*_spinner_cols, console=console) as progress:
        t_tax = progress.add_task("[cyan]Building threat taxonomy...[/cyan]", total=None)
        threats = await build_taxonomy(papers)
        progress.update(t_tax, description=f"[green]Built {len(threats)} threat nodes[/green]", completed=1, total=1)

    for c in concepts:
        writer.write_concept(c)
    for t in threats:
        writer.write_threat(t)
    writer.write_dashboard(papers, concepts, threats)

    table = Table(title="VANTAGE Run Complete")
    table.add_column("Category", style="cyan")
    table.add_column("Count", style="green")
    table.add_row("Papers", str(len(papers)))
    table.add_row("Concepts", str(len(concepts)))
    table.add_row("Threat Nodes", str(len(threats)))
    table.add_row("Vault Path", vault_path)
    console.print(table)


@app.command()
def sync(
    vault: str = typer.Argument(..., help="Target Obsidian vault path"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite destination files even if they are newer"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be copied without writing anything"),
) -> None:
    """Incrementally sync the generated vault to an on-device Obsidian vault.

    Files that already exist in the destination and are newer than the source
    are skipped to protect manual edits. Use --force to overwrite unconditionally.
    """
    src = Path(cfg.obsidian.vault_path)
    dst = Path(vault)
    if not src.exists():
        console.print(f"[red]Source vault not found: {src}[/red]")
        raise typer.Exit(1)

    copied = skipped = 0
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        target = dst / rel

        if item.is_dir():
            if not dry_run:
                target.mkdir(parents=True, exist_ok=True)
            continue

        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)

        if not force and target.exists() and target.stat().st_mtime > item.stat().st_mtime:
            skipped += 1
            continue

        if dry_run:
            console.print(f"  [cyan]would copy[/cyan] {rel}")
        else:
            shutil.copy2(item, target)
        copied += 1

    prefix = "[dim](dry run)[/dim] " if dry_run else ""
    console.print(f"{prefix}[green]Synced {copied} file(s)[/green], [yellow]skipped {skipped} newer file(s)[/yellow] → {dst}")


@app.command("config")
def config_show() -> None:
    """Show the current VANTAGE configuration."""
    import json
    console.print_json(cfg.model_dump_json(indent=2))


@app.command("models")
def models_list() -> None:
    """List configured model aliases."""
    from vantage.llm.models import MODEL_ALIASES
    table = Table(title="Model Aliases")
    table.add_column("Role", style="cyan")
    table.add_column("Model", style="green")
    for role, model in MODEL_ALIASES.items():
        table.add_row(role, model)
    console.print(table)


if __name__ == "__main__":
    app()
