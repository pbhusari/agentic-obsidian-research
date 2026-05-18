from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import httpx

from vantage.config import cfg
from vantage.retrieval.dedup import Deduplicator

_OAI = "https://oaipmh.arxiv.org/oai"
_NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
}


def _text(el: ET.Element, tag: str) -> str:
    found = el.find(tag, _NS)
    return found.text.strip() if found is not None and found.text else ""


def _fetch_oai_category(category: str, cutoff: datetime, n: int) -> list[dict]:
    """Fetch recent papers from an arXiv category via OAI-PMH ListRecords."""
    from_date = cutoff.strftime("%Y-%m-%d")
    # New OAI endpoint only supports top-level sets; filter by subject tag after
    top = category.split(".")[0].lower()
    params = {
        "verb": "ListRecords",
        "metadataPrefix": "oai_dc",
        "set": f"{top}:{top}",
        "from": from_date,
    }
    results = []
    with httpx.Client(timeout=30) as client:
        while True:
            resp = client.get(_OAI, params=params)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)

            for record in root.findall(".//oai:record", _NS):
                header = record.find("oai:header", _NS)
                if header is not None and header.get("status") == "deleted":
                    continue
                metadata = record.find(".//oai_dc:dc", _NS)
                if metadata is None:
                    continue

                identifier = _text(header, "oai:identifier")
                arxiv_id = identifier.replace("oai:arXiv.org:", "")

                date_str = _text(header, "oai:datestamp")
                try:
                    published = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    continue

                # filter to the requested sub-category via setSpec (e.g. cs:cs:CR)
                sub = category.split(".")[-1].upper()
                set_specs = [
                    el.text for el in header.findall("oai:setSpec", _NS) if el.text
                ]
                if not any(s.endswith(f":{sub}") for s in set_specs):
                    continue

                title = _text(metadata, "dc:title").replace("\n", " ")
                abstract = _text(metadata, "dc:description").replace("\n", " ")
                authors = [
                    el.text.strip()
                    for el in metadata.findall("dc:creator", _NS)
                    if el.text
                ]
                url = f"https://arxiv.org/abs/{arxiv_id}"

                results.append({
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "authors": authors,
                    "published": published,
                    "abstract": abstract,
                    "url": url,
                    "citation_count": 0,
                })

                if len(results) >= n:
                    return results

            # follow resumption token if present
            token_el = root.find(".//oai:resumptionToken", _NS)
            if token_el is None or not token_el.text:
                break
            params = {"verb": "ListRecords", "resumptionToken": token_el.text}

    return results


async def fetch_papers(n: int, months_back: int) -> list[dict]:
    cutoff = datetime.now() - timedelta(days=30 * months_back)
    dedup = Deduplicator()
    results: list[dict] = []
    loop = asyncio.get_event_loop()

    for category in cfg.pipeline.venues:
        batch = await loop.run_in_executor(
            None, _fetch_oai_category, category, cutoff, n * 2
        )
        for paper in batch:
            if not dedup.seen(paper["arxiv_id"]):
                results.append(paper)

    results.sort(key=lambda p: p["published"], reverse=True)
    return results[:n]
