# SENTINEL — Agentic Security Research Pipeline for Obsidian
**Project Spec v1.0 — For Claude Code / DeepSeek Code execution**

---

## Overview

SENTINEL is a local CLI pipeline that ingests the top **N papers** from the past **M months** across agentic security research venues, synthesizes them via a fast inference LLM (Gemma-4, DeepSeek-R2, or any Cerebras-compatible model), and emits a fully-linked Obsidian vault — concept nodes, paper nodes, threat taxonomy, and a dashboard MOC.

Target use case: **agentic security research at Cerebras-class speed** — go from zero to a navigable knowledge graph in under 5 minutes.

---

## Goals

1. Pull top-N papers over past M months from arXiv + Semantic Scholar (agentic security, LLM security, tool-use attacks, prompt injection, multi-agent, MCP exploits)
2. For each paper: extract metadata, abstract, key claims, threat primitives, mitigations
3. Synthesize cross-paper concept nodes (attack surfaces, taxonomies, open problems)
4. Write everything as Obsidian-flavored Markdown with `[[wikilinks]]`, tags, and dataview-compatible frontmatter
5. Generate a `_DASHBOARD.md` Master Map of Content (MOC) with graphable structure
6. LLM-agnostic — swap provider via a single env var / config key

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | async-first with `asyncio` |
| Paper retrieval | `arxiv` SDK + Semantic Scholar API | S2 for citation counts / influence scores |
| LLM inference | LiteLLM router | Supports Cerebras, OpenAI-compat, Ollama, OpenRouter |
| Default fast model | `cerebras/gemma2-9b-it` or `deepseek/deepseek-r1` | Sub-second TTFT on Cerebras |
| Fallback model | `claude-sonnet-4-20250514` | For synthesis / concept clustering |
| Output format | Obsidian Markdown | Frontmatter + wikilinks + dataview blocks |
| Config | `config.toml` + `.env` | All keys injectable |
| CLI | `typer` | `sentinel run`, `sentinel sync`, `sentinel config` |

---

## Directory Layout

```
sentinel/
├── sentinel/
│   ├── __init__.py
│   ├── cli.py                  # typer entrypoint
│   ├── config.py               # config.toml loader + env overlay
│   ├── retrieval/
│   │   ├── arxiv_client.py     # arxiv SDK wrapper, query builder
│   │   ├── s2_client.py        # Semantic Scholar, citation rank filter
│   │   └── dedup.py            # hash-based dedup across sources
│   ├── extraction/
│   │   ├── paper_extractor.py  # per-paper LLM extraction prompt chain
│   │   ├── prompts.py          # all prompt templates (string constants)
│   │   └── schema.py           # Pydantic models: Paper, Concept, ThreatNode
│   ├── synthesis/
│   │   ├── concept_clusterer.py  # cross-paper concept extraction
│   │   ├── taxonomy_builder.py   # threat taxonomy DAG construction
│   │   └── moc_generator.py      # _DASHBOARD.md + index nodes
│   ├── obsidian/
│   │   ├── writer.py           # renders Pydantic models -> .md files
│   │   ├── templates.py        # Jinja2 templates for each node type
│   │   └── vault_init.py       # creates folder structure, .obsidian stubs
│   └── llm/
│       ├── router.py           # LiteLLM wrapper, retry, rate limit
│       └── models.py           # model alias registry
├── vault/                      # OUTPUT — drop this into Obsidian
│   ├── _DASHBOARD.md
│   ├── papers/
│   ├── concepts/
│   ├── threats/
│   └── synthesis/
├── config.toml
├── .env.example
├── pyproject.toml
└── README.md
```

---

## Config Schema (`config.toml`)

```toml
[pipeline]
top_n = 25                        # papers to retrieve per run
months_back = 3                   # lookback window
min_citations = 0                 # filter; 0 = include preprints
venues = ["cs.CR", "cs.AI", "cs.LG"]  # arXiv categories
extra_queries = [
  "agentic security",
  "LLM tool use attack",
  "prompt injection multi-agent",
  "MCP model context protocol exploit",
  "jailbreak agent",
  "LLM orchestration security",
  "autonomous agent red team"
]

[llm]
provider = "cerebras"             # cerebras | openai | ollama | anthropic | openrouter
fast_model = "cerebras/gemma2-9b-it"   # extraction (speed)
synthesis_model = "cerebras/deepseek-r1-distill-llama-70b"  # clustering (quality)
temperature = 0.2
max_tokens_extraction = 1024
max_tokens_synthesis = 2048
max_concurrent = 10               # semaphore for parallel extraction

[obsidian]
vault_path = "./vault"
use_dataview = true
use_callouts = true               # Obsidian > callout blocks for threat ratings
tags_prefix = "sentinel"          # all auto-tags prefixed sentinel/
link_style = "wikilink"           # wikilink | markdown

[output]
overwrite_existing = false        # true = always re-extract; false = skip cached
emit_synthesis_log = true         # writes raw LLM outputs to vault/synthesis/
```

---

## Pydantic Schemas (`extraction/schema.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class ThreatPrimitive(BaseModel):
    name: str                         # e.g. "Indirect Prompt Injection"
    category: str                     # Attack | Defense | Mitigation | Open Problem
    severity: str                     # Critical | High | Medium | Low
    description: str
    related_concepts: list[str]       # wikilink targets

class Paper(BaseModel):
    arxiv_id: str
    title: str
    authors: list[str]
    published: date
    abstract: str
    url: str
    citation_count: int
    # LLM-extracted fields
    one_liner: str                    # one sentence summary
    key_contributions: list[str]      # bullet list, max 5
    threat_primitives: list[ThreatPrimitive]
    attack_surfaces: list[str]        # e.g. ["tool-call interface", "system prompt", "memory"]
    mitigations: list[str]
    open_problems: list[str]
    related_papers: list[str]         # arXiv IDs if mentioned
    concepts: list[str]               # concept node names to link
    tags: list[str]                   # obsidian tags

class ConceptNode(BaseModel):
    name: str                         # canonical concept name
    aliases: list[str]                # alternate names/spellings
    definition: str                   # 2-3 sentence synthesis
    threat_relevance: str             # how this concept manifests as a threat
    source_papers: list[str]          # arXiv IDs
    child_concepts: list[str]         # DAG children
    parent_concepts: list[str]        # DAG parents
    open_questions: list[str]
    tags: list[str]

class ThreatTaxonomyNode(BaseModel):
    id: str                           # slug, e.g. "indirect-prompt-injection"
    name: str
    layer: str                        # Attack Surface | Attack Vector | Impact | Mitigation
    description: str
    examples: list[str]               # paper-grounded examples
    mitigations: list[str]
    child_ids: list[str]
    paper_references: list[str]
```

---

## Prompt Templates (`extraction/prompts.py`)

### Paper Extraction Prompt

```
SYSTEM:
You are a senior agentic AI security researcher. Extract structured intelligence from the paper below.
Respond ONLY with valid JSON matching the schema. No preamble, no markdown fences.

USER:
Title: {title}
Authors: {authors}
Published: {published}
Abstract: {abstract}

Extract:
- one_liner: one sentence (<20 words) capturing the core contribution
- key_contributions: list of 3-5 bullet strings
- threat_primitives: list of ThreatPrimitive objects (name, category, severity, description, related_concepts)
- attack_surfaces: list of strings (e.g. "tool-call interface", "retrieval memory", "system prompt")
- mitigations: list of actionable mitigation strings
- open_problems: list of unsolved problems the paper surfaces
- concepts: list of canonical concept names this paper touches (for wikilinks)
- tags: list of lowercase kebab-case tags

JSON ONLY:
```

### Concept Synthesis Prompt

```
SYSTEM:
You are a senior agentic AI security researcher performing a meta-synthesis across a corpus of papers.
Respond ONLY with a JSON array of ConceptNode objects. No preamble, no fences.

USER:
Below is a JSON array of extracted papers. 

{papers_json}

Identify the {k} most important emergent concepts across this corpus.
For each concept:
- Give a canonical name (title-case)
- List aliases
- Write a 2-3 sentence synthesis definition grounded in the papers
- Describe threat relevance in one paragraph
- List source arXiv IDs
- Map parent/child concept relationships
- List 2-3 open questions the community has not resolved

JSON array ONLY:
```

---

## LLM Router (`llm/router.py`)

```python
import litellm
import asyncio
from sentinel.config import cfg

litellm.set_verbose = False

MODEL_ALIASES = {
    "fast": cfg.llm.fast_model,
    "synthesis": cfg.llm.synthesis_model,
}

async def complete(prompt: str, role: str = "fast", system: str = "") -> str:
    """Single completion with retry and semaphore."""
    model = MODEL_ALIASES[role]
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    for attempt in range(3):
        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=cfg.llm.temperature,
                max_tokens=cfg.llm.max_tokens_extraction if role == "fast" 
                           else cfg.llm.max_tokens_synthesis,
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt == 2:
                raise
            await asyncio.sleep(2 ** attempt)

# To swap providers: set LITELLM_MODEL_FAST=ollama/gemma:27b in .env
# LiteLLM handles provider routing transparently
```

---

## Paper Retrieval (`retrieval/arxiv_client.py`)

```python
import arxiv
from datetime import datetime, timedelta
from sentinel.config import cfg
from sentinel.extraction.schema import Paper

async def fetch_papers(n: int, months_back: int) -> list[dict]:
    """Fetch top-N papers by relevance+recency from configured queries."""
    cutoff = datetime.now() - timedelta(days=30 * months_back)
    seen = set()
    results = []

    client = arxiv.Client()
    
    for query in cfg.pipeline.extra_queries:
        search = arxiv.Search(
            query=query,
            max_results=n * 2,  # oversample, then rank
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )
        for r in client.results(search):
            if r.published.replace(tzinfo=None) < cutoff:
                continue
            if r.entry_id in seen:
                continue
            seen.add(r.entry_id)
            results.append({
                "arxiv_id": r.entry_id.split("/")[-1],
                "title": r.title,
                "authors": [a.name for a in r.authors],
                "published": r.published.date(),
                "abstract": r.summary.replace("\n", " "),
                "url": r.entry_id,
            })
    
    # Re-rank by Semantic Scholar citation count (see s2_client.py)
    # Then return top-n
    return results[:n]
```

---

## Obsidian Writer (`obsidian/writer.py`)

### Paper Node Output Format

```markdown
---
title: "{{title}}"
arxiv_id: "{{arxiv_id}}"
published: {{published}}
authors: [{{authors_csv}}]
citation_count: {{citation_count}}
tags: [sentinel/paper, {{tags_csv}}]
type: paper
---

# {{title}}

> [!abstract]+ Abstract
> {{abstract}}

**One-liner:** {{one_liner}}

## Key Contributions
{{key_contributions_bullets}}

## Attack Surfaces
{{attack_surfaces_bullets}}

## Threat Primitives
| Primitive | Category | Severity |
|---|---|---|
{{threat_primitives_table}}

## Mitigations
{{mitigations_bullets}}

## Open Problems
{{open_problems_bullets}}

## Concepts
{{concept_wikilinks}}

## Related Papers
{{related_paper_wikilinks}}

---
*Auto-generated by SENTINEL on {{run_date}}}*
```

### Concept Node Output Format

```markdown
---
title: "{{name}}"
aliases: [{{aliases_csv}}]
tags: [sentinel/concept, {{tags_csv}}]
type: concept
---

# {{name}}

{{definition}}

## Threat Relevance
{{threat_relevance}}

## Concept Map
**Parents:** {{parent_wikilinks}}
**Children:** {{child_wikilinks}}

## Grounding Papers
{{paper_wikilinks}}

## Open Questions
{{open_questions_bullets}}
```

---

## Dashboard MOC (`_DASHBOARD.md`)

```markdown
---
title: SENTINEL Dashboard
tags: [sentinel/dashboard]
type: moc
updated: {{run_date}}
---

# SENTINEL — Agentic Security Research

> [!info] Last run: {{run_date}} | Papers: {{paper_count}} | Concepts: {{concept_count}}

## 🗺️ Threat Taxonomy
[[Indirect Prompt Injection]] · [[Tool-Call Hijacking]] · [[Memory Poisoning]] · [[Agent Impersonation]] · [[Orchestrator Compromise]]

## 📄 Recent Papers ({{paper_count}})
```dataview
TABLE published, citation_count, one_liner
FROM "papers"
SORT published DESC
LIMIT 25
```

## 🔵 Concept Nodes ({{concept_count}})
```dataview
TABLE length(file.inlinks) as "Paper Links"
FROM "concepts"
SORT length(file.inlinks) DESC
```

## 🔴 Critical Threats
```dataview
TABLE threat_primitives
FROM "papers"
WHERE contains(tags, "sentinel/critical")
SORT published DESC
```

## 🟡 Open Problems
{{open_problems_aggregated}}

## 📊 Coverage Map
{{concept_cluster_summary}}
```

---

## CLI Interface (`cli.py`)

```bash
# Full pipeline run
sentinel run --n 25 --months 3

# Only re-synthesize concepts (skip paper re-extraction)
sentinel run --synthesis-only

# Use a different model for this run
sentinel run --fast-model ollama/gemma3:27b --synthesis-model ollama/deepseek-r1:32b

# Add a one-off query to the corpus
sentinel run --extra-query "MCP server exploit 2025"

# Sync vault path into Obsidian
sentinel sync --vault ~/Documents/Obsidian/SENTINEL

# Check config
sentinel config show

# List available models via LiteLLM
sentinel models list
```

---

## `.env.example`

```bash
# Provider keys — only set the ones you use
CEREBRAS_API_KEY=your_key_here
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=...

# Override model aliases at runtime
SENTINEL_FAST_MODEL=cerebras/gemma2-9b-it
SENTINEL_SYNTHESIS_MODEL=cerebras/deepseek-r1-distill-llama-70b

# For fully local runs (no keys needed)
# SENTINEL_FAST_MODEL=ollama/gemma3:12b
# SENTINEL_SYNTHESIS_MODEL=ollama/deepseek-r1:32b

# Semantic Scholar (optional, increases rate limits)
S2_API_KEY=
```

---

## Implementation Phases

### Phase 1 — Retrieval + Extraction (Day 1)
- [ ] `config.py` — load `config.toml` + env overlay into a frozen Pydantic settings object
- [ ] `retrieval/arxiv_client.py` — async paper fetch with date filter + dedup
- [ ] `retrieval/s2_client.py` — citation count enrichment via Semantic Scholar
- [ ] `llm/router.py` — LiteLLM async wrapper with semaphore + retry
- [ ] `extraction/paper_extractor.py` — per-paper JSON extraction with schema validation
- [ ] `obsidian/writer.py` — render Paper → `vault/papers/*.md`
- [ ] `cli.py` — `sentinel run` wires all of the above

**Acceptance test:** `sentinel run --n 5 --months 1` produces 5 valid paper `.md` files in `vault/papers/`

### Phase 2 — Synthesis + Concept Graph (Day 2)
- [ ] `synthesis/concept_clusterer.py` — batch synthesis prompt over all extracted papers
- [ ] `synthesis/taxonomy_builder.py` — build threat taxonomy DAG from extracted primitives
- [ ] `obsidian/writer.py` — render ConceptNode → `vault/concepts/*.md`, ThreatNode → `vault/threats/*.md`
- [ ] Wikilink resolution — ensure all `[[links]]` point to real files

**Acceptance test:** Concept nodes appear in Obsidian graph view with edges to papers

### Phase 3 — Dashboard + Polish (Day 3)
- [ ] `synthesis/moc_generator.py` — render `_DASHBOARD.md`
- [ ] Dataview frontmatter audit — all fields present and typed correctly
- [ ] `vault_init.py` — `.obsidian/` stub with graph color groups by node type
- [ ] `sentinel sync` — copy vault to user-specified Obsidian path
- [ ] README with quickstart

### Phase 4 — Stretch Goals
- [ ] Incremental runs — skip already-extracted papers via content hash cache
- [ ] Embedding-based concept dedup — use `sentence-transformers` to merge near-duplicate concepts
- [ ] PDF ingestion — for papers with full-text PDFs available on arXiv
- [ ] Daily cron mode — `sentinel watch --interval 24h`
- [ ] Obsidian canvas export — visual threat map as `.canvas` file
- [ ] Discord/Slack webhook — post new papers summary on each run

---

## Key Design Decisions

**LLM-agnostic via LiteLLM:** Every model call goes through `llm/router.py`. Swapping from Cerebras to Ollama to Anthropic requires changing one env var. No provider SDK is imported outside the router.

**Two-tier model strategy:** Use the fast model (Gemma-4 / DeepSeek on Cerebras = sub-100ms TTFT) for per-paper extraction with a tight JSON schema. Use the synthesis model (larger, slightly slower) only once for cross-paper concept clustering. This keeps total wall-clock time low even at N=50.

**Obsidian-native output:** Everything is `.md` with dataview-compatible frontmatter. No plugins required except Dataview. The vault is portable and human-readable even without SENTINEL.

**Strict JSON extraction:** All LLM outputs are parsed against Pydantic models. Malformed outputs trigger a retry with an error-correction prompt. Papers that fail after 3 attempts are written to `vault/synthesis/errors/` for manual review.

**Incremental by default:** Paper nodes are never overwritten unless `overwrite_existing = true`. Re-runs add new papers and re-synthesize concepts over the full corpus.

---

## Dependencies (`pyproject.toml`)

```toml
[project]
name = "sentinel"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
  "typer>=0.12",
  "litellm>=1.40",
  "arxiv>=2.1",
  "httpx>=0.27",
  "pydantic>=2.7",
  "jinja2>=3.1",
  "toml>=0.10",
  "rich>=13",
  "python-dotenv>=1.0",
  "tenacity>=8.3",
  "tqdm>=4.66",
]

[project.scripts]
sentinel = "sentinel.cli:app"
```

---

## Notes for Code Agent

- All async — use `asyncio.gather` with a `Semaphore(cfg.llm.max_concurrent)` for parallel paper extraction
- Never hardcode model strings outside `llm/models.py` and `config.toml`
- Pydantic v2 throughout — use `model_validate_json()` for LLM output parsing
- Jinja2 templates live in `obsidian/templates/` as `.j2` files — do not inline template strings in Python
- `rich` for all CLI output — progress bars on paper extraction, summary table on completion
- Wikilink targets must be sanitized: strip special chars, title-case, replace spaces with spaces (Obsidian handles this)
- The `vault/` directory is the only output — nothing writes outside it
- Respect Semantic Scholar rate limits: 100 req/5min unauthenticated, 1 req/sec authenticated
