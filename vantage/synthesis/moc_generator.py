from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from vantage.config import cfg
from vantage.extraction.schema import ConceptNode, Paper, ThreatTaxonomyNode

_TEMPLATE_DIR = Path(__file__).parent.parent / "obsidian" / "templates"

OWASP_LABELS = {
    "AA01": "Prompt Injection",
    "AA02": "Sensitive Information Disclosure",
    "AA03": "Excessive Agency",
    "AA04": "Memory Poisoning",
    "AA05": "Insecure Tool Usage",
    "AA06": "Insufficient Access Controls",
    "AA07": "Agent Communication Vulnerabilities",
    "AA08": "Inadequate Monitoring and Logging",
    "AA09": "Insecure Output Handling",
    "AA10": "Uncontrolled Recursion and Loops",
}


def _owasp_index(threats: list[ThreatTaxonomyNode]) -> str:
    """Build a markdown section organizing threat nodes by OWASP category."""
    by_cat: dict[str, list[ThreatTaxonomyNode]] = defaultdict(list)
    for node in threats:
        for cat in node.owasp_categories:
            by_cat[cat].append(node)

    lines: list[str] = []
    for cat_id, label in OWASP_LABELS.items():
        nodes = by_cat.get(cat_id, [])
        count = len(nodes)
        lines.append(f"\n### {cat_id} — {label} ({count} nodes)")
        if nodes:
            for n in sorted(nodes, key=lambda x: x.severity or ""):
                sev = f"**{n.severity}**" if n.severity else ""
                lines.append(f"- [[{n.id}|{n.name}]] {sev}")
        else:
            lines.append("- *No nodes mapped yet*")

    return "\n".join(lines)


def generate_dashboard(
    papers: list[Paper],
    concepts: list[ConceptNode],
    threats: list[ThreatTaxonomyNode] | None = None,
) -> str:
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=False)
    tmpl = env.get_template("dashboard.j2")

    open_problems: list[str] = []
    for p in papers:
        open_problems.extend(p.open_problems)
    seen: set[str] = set()
    unique_problems: list[str] = []
    for op in open_problems:
        if op not in seen:
            seen.add(op)
            unique_problems.append(op)

    concept_cluster_lines = [f"- [[{c.name}]]" for c in concepts[:20]]

    owasp_taxonomy_index = _owasp_index(threats or [])

    # severity breakdown for threats
    sev_counts: dict[str, int] = defaultdict(int)
    for t in (threats or []):
        sev_counts[t.severity or "Unknown"] += 1

    return tmpl.render(
        run_date=str(date.today()),
        paper_count=len(papers),
        concept_count=len(concepts),
        threat_count=len(threats or []),
        open_problems_aggregated="\n".join(f"- {op}" for op in unique_problems[:20]),
        concept_cluster_summary="\n".join(concept_cluster_lines),
        owasp_taxonomy_index=owasp_taxonomy_index,
        sev_critical=sev_counts.get("Critical", 0),
        sev_high=sev_counts.get("High", 0),
        sev_medium=sev_counts.get("Medium", 0),
        sev_low=sev_counts.get("Low", 0),
    )
