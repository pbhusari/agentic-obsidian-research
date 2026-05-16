from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
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

    if not synthesis_only:
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            t1 = progress.add_task("Fetching papers from arXiv...", total=None)
            paper_metas = await fetch_papers(n, months)
            progress.update(t1, description=f"Fetched {len(paper_metas)} papers. Enriching citations...")
            paper_metas = await enrich_with_citations(paper_metas)
            progress.update(t1, description=f"Extracting intelligence from {len(paper_metas)} papers...")
            papers = await extract_all(paper_metas)
            progress.update(t1, description=f"Writing {len(papers)} paper nodes...", completed=1, total=1)

        for p in papers:
            writer.write_paper(p)
    else:
        # Load existing papers from vault
        import json
        papers_dir = Path(vault_path) / "papers"
        console.print("[yellow]synthesis-only: loading existing papers from vault...[/yellow]")
        # We can't reload full Paper objects from markdown easily, so we skip re-loading
        # and just re-synthesize with an empty list as a graceful degradation
        console.print("[yellow]Warning: synthesis-only without cached JSON is limited.[/yellow]")

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        t2 = progress.add_task("Synthesizing concept nodes...", total=None)
        concepts = await cluster_concepts(papers)
        progress.update(t2, description="Building threat taxonomy...")
        threats = await build_taxonomy(papers)
        progress.update(t2, description="Writing concept and threat nodes...", completed=1, total=1)

    for c in concepts:
        writer.write_concept(c)
    for t in threats:
        writer.write_threat(t)
    writer.write_dashboard(papers, concepts)

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
) -> None:
    """Copy the generated vault to a target Obsidian directory."""
    src = Path(cfg.obsidian.vault_path)
    dst = Path(vault)
    if not src.exists():
        console.print(f"[red]Source vault not found: {src}[/red]")
        raise typer.Exit(1)

    dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            shutil.copy2(item, target)

    console.print(f"[green]Vault synced to {dst}[/green]")


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
