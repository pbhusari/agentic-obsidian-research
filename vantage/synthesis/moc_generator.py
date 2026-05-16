from __future__ import annotations

from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from vantage.config import cfg
from vantage.extraction.schema import ConceptNode, Paper

_TEMPLATE_DIR = Path(__file__).parent.parent / "obsidian" / "templates"


def generate_dashboard(papers: list[Paper], concepts: list[ConceptNode]) -> str:
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=False)
    tmpl = env.get_template("dashboard.j2")

    open_problems: list[str] = []
    for p in papers:
        open_problems.extend(p.open_problems)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_problems: list[str] = []
    for op in open_problems:
        if op not in seen:
            seen.add(op)
            unique_problems.append(op)

    concept_cluster_lines = [f"- [[{c.name}]]" for c in concepts[:20]]

    return tmpl.render(
        run_date=str(date.today()),
        paper_count=len(papers),
        concept_count=len(concepts),
        open_problems_aggregated="\n".join(f"- {op}" for op in unique_problems[:20]),
        concept_cluster_summary="\n".join(concept_cluster_lines),
    )
