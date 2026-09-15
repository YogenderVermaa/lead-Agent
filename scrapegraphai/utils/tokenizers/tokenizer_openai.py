"""
Tokenization utilities for OpenAI models
"""

import tiktoken

from ..logging import get_logger


def num_tokens_openai(text: str) -> int:
    """
    Estimate the number of tokens in a given text using OpenAI's tokenization method,
    with robust fallback if token encoding cannot be fetched.

    Args:
        text (str): The text to be tokenized and counted.

    Returns:
        int: The number of tokens in the text.
    """

    logger = get_logger()

    logger.debug(f"Counting tokens for text of {len(text)} characters")

    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text, disallowed_special=()))
    except Exception:
        try:
            encoding = tiktoken.encoding_for_model("gpt-4o")
            return len(encoding.encode(text))
        except Exception:
            return max(1, len(text) // 4)

