# VANTAGE

Agentic Security Research Pipeline for Obsidian. Pulls the top N papers from the past M months across agentic security venues, synthesizes them via a fast LLM, and emits a fully-linked Obsidian vault.

## Pipeline

Each `vantage run` executes these steps in order:

1. **Fetch** — queries arXiv for the top N papers matching configured venues and extra queries, then enriches each result with citation counts via Semantic Scholar
2. **Extract** — runs each paper through the fast LLM to pull out threat primitives, attack surfaces, mitigations, and key concepts; results are written to `vault/papers/`
3. **Concept clustering** — passes the full paper corpus to the synthesis LLM and collapses recurring ideas into up to 15 cross-paper concept nodes; written to `vault/concepts/`
4. **Threat taxonomy** — builds a DAG of threat nodes from the extracted primitives across all papers, classifying attack classes and linking mitigations; written to `vault/threats/`
5. **Dashboard** — generates `vault/_DASHBOARD.md`, a Dataview-powered Map of Content linking everything together

## Quickstart

```bash
# Install
pip install -e .

# Configure API keys
cp .env.example .env
# Edit .env with your CEREBRAS_API_KEY (or any other provider)

# Run
vantage run --n 25 --months 3

# Sync vault into Obsidian
vantage sync ~/Documents/Obsidian/VANTAGE
```

## Commands

```bash
vantage run --n 25 --months 3                          # full pipeline (fetch → extract → concepts → threats → dashboard)
vantage run --synthesis-only                           # skip fetch/extract, re-run concept clustering and threat taxonomy only
vantage run --fast-model ollama/gemma3:27b             # override fast model (used for per-paper extraction)
vantage run --synthesis-model ollama/deepseek-r1:32b   # override synthesis model (used for concept clustering and threat taxonomy)
vantage run --extra-query "MCP server exploit 2025"    # add a one-off arXiv query on top of configured venues
vantage sync ~/Documents/Obsidian/VANTAGE              # incrementally copy vault to Obsidian, skipping newer destination files
vantage sync ~/Documents/Obsidian/VANTAGE --force      # overwrite even newer destination files
vantage sync ~/Documents/Obsidian/VANTAGE --dry-run    # preview what would be copied
vantage config                                         # show current config
vantage models                                         # list model aliases
```

## Configuration

Edit `config.toml` to change defaults. All values can be overridden via `.env`:

```bash
VANTAGE_FAST_MODEL=ollama/gemma3:12b
VANTAGE_SYNTHESIS_MODEL=ollama/deepseek-r1:32b
CEREBRAS_API_KEY=your_key_here
```

## Output

The `vault/` directory is drop-in Obsidian compatible. Requires the [Dataview](https://github.com/blacksmithgu/obsidian-dataview) plugin for dashboard queries.

```
vault/
├── _DASHBOARD.md      # Master Map of Content
├── papers/            # one .md per paper
├── concepts/          # cross-paper concept nodes
├── threats/           # threat taxonomy DAG nodes
└── synthesis/         # raw LLM outputs + error logs
```

## Swapping Providers

Set one env var. LiteLLM handles the rest:

```bash
# Cerebras (default, sub-100ms TTFT)
VANTAGE_FAST_MODEL=cerebras/gemma2-9b-it

# Ollama (fully local)
VANTAGE_FAST_MODEL=ollama/gemma3:12b
VANTAGE_SYNTHESIS_MODEL=ollama/deepseek-r1:32b

# OpenAI
VANTAGE_FAST_MODEL=gpt-4o-mini
VANTAGE_SYNTHESIS_MODEL=gpt-4o
```
