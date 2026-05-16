# VANTAGE

Agentic Security Research Pipeline for Obsidian. Pulls the top N papers from the past M months across agentic security venues, synthesizes them via a fast LLM, and emits a fully-linked Obsidian vault.

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
vantage run --n 25 --months 3                          # full pipeline
vantage run --synthesis-only                           # re-synthesize without re-extracting
vantage run --fast-model ollama/gemma3:27b             # override model for this run
vantage run --extra-query "MCP server exploit 2025"    # add a one-off query
vantage sync --vault ~/Documents/Obsidian/VANTAGE     # copy vault to Obsidian
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
