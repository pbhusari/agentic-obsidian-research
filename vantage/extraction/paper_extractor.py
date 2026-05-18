from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from pydantic import ValidationError

from vantage.config import cfg
from vantage.extraction.prompts import (
    PAPER_CORRECTION_USER,
    PAPER_EXTRACTION_SYSTEM,
    PAPER_EXTRACTION_USER,
)
from vantage.extraction.schema import Paper
from vantage.llm.router import complete

logger = logging.getLogger(__name__)

_ERROR_DIR = Path(cfg.obsidian.vault_path) / "synthesis" / "errors"


def _build_partial_paper(raw: dict) -> Paper:
    """Merge LLM-extracted fields into a Paper, coercing types where needed."""
    return Paper.model_validate(raw)


async def extract_paper(meta: dict) -> Paper | None:
    """Run LLM extraction for a single paper dict. Returns None on total failure."""
    _ERROR_DIR.mkdir(parents=True, exist_ok=True)

    user_prompt = PAPER_EXTRACTION_USER.format(
        title=meta["title"],
        authors=", ".join(meta.get("authors", [])),
        published=str(meta.get("published", "")),
        abstract=meta.get("abstract", ""),
    )

    last_error: str = ""
    for attempt in range(3):
        try:
            raw_text = await complete(user_prompt, role="fast", system=PAPER_EXTRACTION_SYSTEM)
            raw_text = raw_text.strip()
            # strip accidental markdown fences
            if raw_text.startswith("```"):
                raw_text = "\n".join(raw_text.split("\n")[1:])
            if raw_text.endswith("```"):
                raw_text = raw_text[: raw_text.rfind("```")]

            parsed = json.loads(raw_text)
            merged = {**meta, **parsed}
            return _build_partial_paper(merged)

        except (json.JSONDecodeError, ValidationError, Exception) as e:
            last_error = str(e)
            logger.warning("Attempt %d failed for %s: %s", attempt + 1, meta.get("arxiv_id"), e)
            if attempt < 2:
                user_prompt = PAPER_CORRECTION_USER.format(
                    error=last_error,
                    title=meta["title"],
                    abstract=meta.get("abstract", ""),
                )

    # Write failure log
    err_file = _ERROR_DIR / f"{meta.get('arxiv_id', 'unknown')}.json"
    err_file.write_text(
        json.dumps({"meta": meta, "error": last_error}, default=str, indent=2)
    )
    logger.error("Extraction failed for %s after 3 attempts", meta.get("arxiv_id"))
    return None


async def extract_all(
    paper_metas: list[dict],
    on_done=None,
) -> list[Paper]:
    """Parallel extraction of all papers respecting the semaphore in router.py."""
    async def _wrap(m: dict) -> Paper | None:
        result = await extract_paper(m)
        if on_done is not None:
            on_done(result)
        return result

    tasks = [_wrap(m) for m in paper_metas]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return [r for r in results if r is not None]
