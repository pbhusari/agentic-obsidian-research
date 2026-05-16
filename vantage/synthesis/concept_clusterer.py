from __future__ import annotations

import json
import logging
from pathlib import Path

from vantage.config import cfg
from vantage.extraction.prompts import CONCEPT_SYNTHESIS_SYSTEM, CONCEPT_SYNTHESIS_USER
from vantage.extraction.schema import ConceptNode, Paper
from vantage.llm.router import complete

logger = logging.getLogger(__name__)

_SYNTH_DIR = Path(cfg.obsidian.vault_path) / "synthesis"


async def cluster_concepts(papers: list[Paper], k: int = 15) -> list[ConceptNode]:
    """Synthesize cross-paper concept nodes from the full paper corpus."""
    _SYNTH_DIR.mkdir(parents=True, exist_ok=True)

    papers_json = json.dumps(
        [p.model_dump(mode="json") for p in papers], indent=2, default=str
    )

    prompt = CONCEPT_SYNTHESIS_USER.format(papers_json=papers_json, k=k)

    raw_text = await complete(prompt, role="synthesis", system=CONCEPT_SYNTHESIS_SYSTEM)
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = "\n".join(raw_text.split("\n")[1:])
    if raw_text.endswith("```"):
        raw_text = raw_text[: raw_text.rfind("```")]

    if cfg.output.emit_synthesis_log:
        (_SYNTH_DIR / "concept_synthesis_raw.json").write_text(raw_text)

    parsed = json.loads(raw_text)
    concepts: list[ConceptNode] = []
    for item in parsed:
        try:
            concepts.append(ConceptNode.model_validate(item))
        except Exception as e:
            logger.warning("Skipping invalid concept node: %s", e)

    return concepts
