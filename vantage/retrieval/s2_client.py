from __future__ import annotations

import asyncio
import os

import httpx

_S2_BASE = "https://api.semanticscholar.org/graph/v1"
_API_KEY = os.getenv("S2_API_KEY", "")
_RATE_LIMIT = 1.0  # seconds between requests when authenticated; 5s unauthenticated
_DELAY = 1.1 if _API_KEY else 5.1


async def enrich_with_citations(papers: list[dict]) -> list[dict]:
    """Add citation_count from Semantic Scholar for each paper in-place."""
    headers = {"x-api-key": _API_KEY} if _API_KEY else {}

    async with httpx.AsyncClient(headers=headers, timeout=15) as client:
        for paper in papers:
            arxiv_id = paper.get("arxiv_id", "")
            try:
                resp = await client.get(
                    f"{_S2_BASE}/paper/arXiv:{arxiv_id}",
                    params={"fields": "citationCount"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    paper["citation_count"] = data.get("citationCount", 0)
            except Exception:
                pass
            await asyncio.sleep(_DELAY)

    return papers
