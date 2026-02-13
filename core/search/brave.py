"""Brave Search API implementation."""
import asyncio
import requests
from .base import SearchProvider, SearchResult


BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


class BraveSearchProvider(SearchProvider):
    """Brave Search API provider."""

    def __init__(self, api_key: str | None = None):
        """Initialize with API key.

        Args:
            api_key: Brave Search API key. If None, reads from config.
        """
        if api_key is None:
            from config import get_settings
            api_key = get_settings().brave_api_key
        self.api_key = api_key

    def _make_request(self, query: str, max_results: int) -> list[SearchResult]:
        """Make HTTP request to Brave Search API."""
        if not self.api_key:
            raise ValueError("Brave API key not configured")

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key,
        }
        params = {
            "q": query,
            "count": min(max_results, 20),  # Brave max is 20
        }

        response = requests.get(
            BRAVE_SEARCH_URL,
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        results = []
        web_results = data.get("web", {}).get("results", [])
        for item in web_results[:max_results]:
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("description", "")
            ))
        return results

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Async search using Brave Search API."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._make_request, query, max_results)

    def search_sync(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Synchronous search using Brave Search API."""
        return self._make_request(query, max_results)
