from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from vantage.config import cfg
from vantage.extraction.schema import ConceptNode, Paper, ThreatTaxonomyNode
from vantage.obsidian.templates import get_env
from vantage.synthesis.moc_generator import generate_dashboard


def _safe_filename(name: str) -> str:
    """Sanitize a string for use as a filesystem filename."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip()


class VaultWriter:
    def __init__(self, vault_path: str | None = None) -> None:
        self.vault = Path(vault_path or cfg.obsidian.vault_path)
        self.env = get_env()
        self.run_date = str(date.today())

    def write_paper(self, paper: Paper) -> Path:
        dest = self.vault / "papers" / f"{paper.arxiv_id}.md"
        if dest.exists() and not cfg.output.overwrite_existing:
            return dest

        tmpl = self.env.get_template("paper.j2")
        content = tmpl.render(
            **paper.model_dump(mode="json"),
            run_date=self.run_date,
        )
        dest.write_text(content, encoding="utf-8")
        return dest

    def write_concept(self, concept: ConceptNode) -> Path:
        fname = _safe_filename(concept.name) + ".md"
        dest = self.vault / "concepts" / fname
        if dest.exists() and not cfg.output.overwrite_existing:
            return dest

        tmpl = self.env.get_template("concept.j2")
        content = tmpl.render(**concept.model_dump(mode="json"))
        dest.write_text(content, encoding="utf-8")
        return dest

    def write_threat(self, node: ThreatTaxonomyNode) -> Path:
        fname = _safe_filename(node.id) + ".md"
        dest = self.vault / "threats" / fname
        if dest.exists() and not cfg.output.overwrite_existing:
            return dest

        tmpl = self.env.get_template("threat.j2")
        content = tmpl.render(**node.model_dump(mode="json"))
        dest.write_text(content, encoding="utf-8")
        return dest

    def write_dashboard(self, papers: list[Paper], concepts: list[ConceptNode]) -> Path:
        dest = self.vault / "_DASHBOARD.md"
        content = generate_dashboard(papers, concepts)
        dest.write_text(content, encoding="utf-8")
        return dest

    def write_all(
        self,
        papers: list[Paper],
        concepts: list[ConceptNode],
        threats: list[ThreatTaxonomyNode],
    ) -> dict[str, int]:
        paper_count = sum(1 for p in papers if self.write_paper(p))
        concept_count = sum(1 for c in concepts if self.write_concept(c))
        threat_count = sum(1 for t in threats if self.write_threat(t))
        self.write_dashboard(papers, concepts)
        return {"papers": paper_count, "concepts": concept_count, "threats": threat_count}
