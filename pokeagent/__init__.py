"""
PokeAgent - A Pokemon Showdown client with LLM-based battle AI
"""

__version__ = "0.1.0"
__author__ = "PokeAgent Team"

from .agents import BaseAgent, LLMAgent

__all__ = [
    "BaseAgent",
    "LLMAgent",
    "__version__",
]
