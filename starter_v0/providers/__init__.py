from providers.openai_provider import OpenAIProvider
from providers.openrouter_provider import OpenRouterProvider
from providers.anthropic_provider import AnthropicProvider
from providers.gemini_provider import GeminiProvider
from providers.vilao_provider import VilaoProvider


PROVIDER_CHOICES = ["openrouter", "openai", "anthropic", "gemini", "vilao"]


def make_provider(name: str):
    if name == "openai":
        return OpenAIProvider()
    if name == "openrouter":
        return OpenRouterProvider()
    if name == "anthropic":
        return AnthropicProvider()
    if name == "gemini":
        return GeminiProvider()
    if name == "vilao":
        return VilaoProvider()
    raise ValueError(f"Unknown provider: {name}")
