from __future__ import annotations

import os

from providers.openai_provider import OpenAIProvider


class VilaoProvider(OpenAIProvider):
    """Vilao OpenAI-compatible Chat Completions provider."""

    def __init__(self) -> None:
        super().__init__(
            api_key_env="VILAO_API_KEY",
            base_url=os.getenv("VILAO_BASE_URL", "https://api.vilao.ai/v1"),
            default_model=os.getenv("VILAO_MODEL", "occ/claude-sonnet-4-6"),
        )
