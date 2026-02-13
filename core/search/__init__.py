"""Search module for PaperGuide.

Provides decoupled search provider interface.
"""
from .base import SearchProvider, SearchResult, get_search_provider
from .brave import BraveSearchProvider

__all__ = [
    "SearchProvider",
    "SearchResult",
    "get_search_provider",
    "BraveSearchProvider",
]
