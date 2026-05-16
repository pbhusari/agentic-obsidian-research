from __future__ import annotations

import asyncio

import litellm

from vantage.config import cfg
from vantage.llm.models import MODEL_ALIASES

litellm.set_verbose = False

_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(cfg.llm.max_concurrent)
    return _semaphore


async def complete(prompt: str, role: str = "fast", system: str = "") -> str:
    model = MODEL_ALIASES[role]
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    max_tokens = (
        cfg.llm.max_tokens_extraction if role == "fast" else cfg.llm.max_tokens_synthesis
    )

    async with _get_semaphore():
        for attempt in range(3):
            try:
                response = await litellm.acompletion(
                    model=model,
                    messages=messages,
                    temperature=cfg.llm.temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(2**attempt)
    raise RuntimeError("unreachable")
