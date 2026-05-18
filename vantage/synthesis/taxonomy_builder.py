from __future__ import annotations

import json
import logging
from pathlib import Path

from vantage.config import cfg
from vantage.extraction.prompts import TAXONOMY_SYSTEM, TAXONOMY_USER
from vantage.extraction.schema import Paper, ThreatTaxonomyNode
from vantage.llm.router import complete

logger = logging.getLogger(__name__)

_SYNTH_DIR = Path(cfg.obsidian.vault_path) / "synthesis"


async def build_taxonomy(papers: list[Paper]) -> list[ThreatTaxonomyNode]:
    """Build a threat taxonomy DAG from extracted paper primitives."""
    slim_papers = [
        {
            "arxiv_id": p.arxiv_id,
            "title": p.title,
            "threat_primitives": [t.model_dump(mode="json") for t in p.threat_primitives],
            "attack_surfaces": p.attack_surfaces,
            "mitigations": p.mitigations,
        }
        for p in papers
    ]
    papers_json = json.dumps(slim_papers, indent=2, default=str)

    prompt = TAXONOMY_USER.format(papers_json=papers_json)
    raw_text = await complete(prompt, role="synthesis", system=TAXONOMY_SYSTEM)
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = "\n".join(raw_text.split("\n")[1:])
    if raw_text.endswith("```"):
        raw_text = raw_text[: raw_text.rfind("```")]

    if cfg.output.emit_synthesis_log:
        (_SYNTH_DIR / "taxonomy_raw.json").write_text(raw_text)

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        last_close = raw_text.rfind("}")
        if last_close == -1:
            raise
        inner = raw_text[: last_close + 1].lstrip().lstrip("[").rstrip().rstrip(",")
        parsed = json.loads(f"[{inner}]")
        logger.warning("LLM response was truncated; recovered %d taxonomy nodes", len(parsed))

    nodes: list[ThreatTaxonomyNode] = []
    for item in parsed:
        try:
            nodes.append(ThreatTaxonomyNode.model_validate(item))
        except Exception as e:
            logger.warning("Skipping invalid taxonomy node: %s", e)

    return nodes
