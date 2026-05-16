from vantage.config import cfg

MODEL_ALIASES: dict[str, str] = {
    "fast": cfg.llm.fast_model,
    "synthesis": cfg.llm.synthesis_model,
}
