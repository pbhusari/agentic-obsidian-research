from __future__ import annotations

import os
from pathlib import Path

import toml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

_ROOT = Path(__file__).parent.parent


class PipelineConfig(BaseModel):
    top_n: int = 25
    months_back: int = 3
    min_citations: int = 0
    venues: list[str] = ["cs.CR", "cs.AI", "cs.LG"]
    extra_queries: list[str] = []


class LLMConfig(BaseModel):
    provider: str = "cerebras"
    fast_model: str = "cerebras/gemma2-9b-it"
    synthesis_model: str = "cerebras/deepseek-r1-distill-llama-70b"
    temperature: float = 0.2
    max_tokens_extraction: int = 1024
    max_tokens_synthesis: int = 2048
    max_concurrent: int = 10


class ObsidianConfig(BaseModel):
    vault_path: str = "./vault"
    use_dataview: bool = True
    use_callouts: bool = True
    tags_prefix: str = "vantage"
    link_style: str = "wikilink"


class OutputConfig(BaseModel):
    overwrite_existing: bool = False
    emit_synthesis_log: bool = True


class Config(BaseModel):
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    obsidian: ObsidianConfig = Field(default_factory=ObsidianConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)


def _load() -> Config:
    config_path = _ROOT / "config.toml"
    raw: dict = {}
    if config_path.exists():
        raw = toml.load(config_path)

    # env overrides
    llm_raw = raw.get("llm", {})
    if fast := os.getenv("VANTAGE_FAST_MODEL"):
        llm_raw["fast_model"] = fast
    if synth := os.getenv("VANTAGE_SYNTHESIS_MODEL"):
        llm_raw["synthesis_model"] = synth
    raw["llm"] = llm_raw

    return Config.model_validate(raw)


cfg = _load()
