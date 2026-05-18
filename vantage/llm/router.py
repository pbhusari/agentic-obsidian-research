from __future__ import annotations

import asyncio
import re

import litellm

from vantage.config import cfg
from vantage.llm.models import MODEL_ALIASES

litellm.set_verbose = False

_semaphore: asyncio.Semaphore | None = None

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _is_deepseek(model: str) -> bool:
    return "deepseek" in model.lower() or "r1" in model.lower()


def _strip_think(text: str) -> str:
    return _THINK_RE.sub("", text).strip()


def _build_messages(prompt: str, system: str, model: str) -> list[dict]:
    """For DeepSeek R1, fold the system prompt into the user turn."""
    if system and _is_deepseek(model):
        return [{"role": "user", "content": f"{system}\n\n{prompt}"}]
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(cfg.llm.max_concurrent)
    return _semaphore


async def complete(prompt: str, role: str = "fast", system: str = "") -> str:
    model = MODEL_ALIASES[role]
    messages = _build_messages(prompt, system, model)

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
                content = response.choices[0].message.content or ""
                return _strip_think(content)
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(2**attempt)
    raise RuntimeError("unreachable")
