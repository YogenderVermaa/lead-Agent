"""
Configuration module for ScrapeGraphAI with Ollama and Gemini LLM integration.
Supports local free Ollama (http://localhost:11434) and cloud LLM providers.
"""

import importlib.metadata
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from dotenv import find_dotenv, load_dotenv

logger = logging.getLogger("lead_scraper.config")


def get_scrapegraphai_version() -> str:
    """Retrieve the installed ScrapeGraphAI package version."""
    try:
        return importlib.metadata.version("scrapegraphai")
    except Exception:
        import scrapegraphai
        return getattr(scrapegraphai, "__version__", "unknown")


def get_available_ollama_models(base_url: str = "http://localhost:11434") -> List[str]:
    """
    Fetch the list of installed models from the local Ollama instance.

    Args:
        base_url: Ollama base server URL.

    Returns:
        List[str]: List of available model tags.
    """
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            return models
    except Exception as exc:
        logger.debug(f"Could not connect to Ollama at {base_url}: {exc}")
    return []


def load_environment() -> Optional[str]:
    """
    Find and load .env file, retrieving the Gemini API Key if configured.

    Returns:
        Optional[str]: The Gemini API Key if present, or None.
    """
    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path)
    else:
        project_root = Path(__file__).resolve().parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        else:
            load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
    return api_key


# Disable ScrapeGraphAI external telemetry
os.environ["SCRAPEGRAPHAI_TELEMETRY_ENABLED"] = "false"


def get_graph_config(
    model_name: Optional[str] = None,
    base_url: str = "http://localhost:11434",
    headless: bool = True,
    verbose: bool = False,
    timeout: int = 300,
    api_key: Optional[str] = None,
    model_tokens: Optional[int] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Build ScrapeGraphAI configuration dictionary.
    Prioritizes local free Ollama or Gemini based on model_name.

    Args:
        model_name: Model identifier (e.g. 'ollama/qwen3:8b', 'google_genai/gemini-3.5-flash-lite').
                    If None, auto-detects local Ollama models.
        base_url: Local Ollama base URL (default: http://localhost:11434).
        headless: Whether to run Playwright in headless mode.
        verbose: Enable verbose logging during graph execution.
        timeout: Scraping timeout in seconds per page (default: 300s).
        api_key: Optional explicit API key for cloud models.
        model_tokens: Context window token limit (default: 4000 for Ollama, 1000000 for Gemini).
        **kwargs: Additional ScrapeGraphAI configuration options.

    Returns:
        Dict[str, Any]: Graph configuration for ScrapeGraphAI.
    """
    # Auto-detect model if not provided
    if model_name is None:
        ollama_models = get_available_ollama_models(base_url)
        if ollama_models:
            model_name = f"ollama/{ollama_models[0]}"
            logger.info(f"Auto-detected local Ollama model: {model_name}")
        else:
            model_name = "ollama/qwen3:8b"

    is_ollama = model_name.startswith("ollama") or ("/" not in model_name and "gemini" not in model_name and "gpt" not in model_name)

    if is_ollama:
        clean_model = model_name if model_name.startswith("ollama/") else f"ollama/{model_name}"
        tokens = model_tokens if model_tokens is not None else 4000
        llm_config = {
            "model": clean_model,
            "base_url": base_url,
            "temperature": 0.0,
            "format": "json",
            "model_tokens": tokens,
        }
    else:
        resolved_api_key = api_key or load_environment()
        if not resolved_api_key:
            raise ValueError(
                "GEMINI_API_KEY not found for cloud model. "
                "For free local scraping without API keys, use Ollama (e.g. --model ollama/qwen3:8b)."
            )
        tokens = model_tokens if model_tokens is not None else 1000000
        llm_config = {
            "api_key": resolved_api_key,
            "model": model_name,
            "temperature": 0.0,
            "model_tokens": tokens,
        }

    config = {
        "llm": llm_config,
        "headless": headless,
        "verbose": verbose,
        "timeout": timeout,
    }

    config.update(kwargs)
    return config
