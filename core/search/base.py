"""Abstract search provider interface.

Designed for easy extension to different search APIs.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    """A single search result."""
    title: str
    url: str
    snippet: str


class SearchProvider(ABC):
    """Abstract base class for search providers."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Perform a search and return results.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of SearchResult objects
        """
        pass

    @abstractmethod
    def search_sync(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Synchronous version of search."""
        pass


def get_search_provider(provider: str = "brave", **kwargs) -> SearchProvider:
    """Factory function to get a search provider.

    Args:
        provider: Provider name ("brave", "tavily", etc.)
        **kwargs: Provider-specific configuration

    Returns:
        SearchProvider instance
    """
    if provider == "brave":
        from .brave import BraveSearchProvider
        return BraveSearchProvider(**kwargs)
    else:
        raise ValueError(f"Unknown search provider: {provider}")
