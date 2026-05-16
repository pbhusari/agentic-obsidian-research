from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import arxiv

from vantage.config import cfg
from vantage.retrieval.dedup import Deduplicator


async def fetch_papers(n: int, months_back: int) -> list[dict]:
    """Fetch top-N papers by recency from configured queries, deduplicated."""
    cutoff = datetime.now() - timedelta(days=30 * months_back)
    dedup = Deduplicator()
    results: list[dict] = []

    client = arxiv.Client()

    for query in cfg.pipeline.extra_queries:
        search = arxiv.Search(
            query=query,
            max_results=n * 2,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )
        for r in client.results(search):
            if r.published.replace(tzinfo=None) < cutoff:
                continue
            arxiv_id = r.entry_id.split("/")[-1]
            if dedup.seen(arxiv_id):
                continue
            results.append(
                {
                    "arxiv_id": arxiv_id,
                    "title": r.title,
                    "authors": [a.name for a in r.authors],
                    "published": r.published.date(),
                    "abstract": r.summary.replace("\n", " "),
                    "url": r.entry_id,
                    "citation_count": 0,
                }
            )

        # small sleep to avoid hammering the API
        await asyncio.sleep(0.5)

    return results[:n]
