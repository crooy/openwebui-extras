"""URL scraping filter for OpenWebUI
Automatically detects URLs in user messages and appends scraped content to context
Requirements:
- aiohttp
- pydantic
- starlette
- BeautifulSoup
"""

import re
from typing import Any, Awaitable, Callable, Dict, Optional

import aiohttp
from bs4 import BeautifulSoup
from fastapi import Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse


class Filter:
    """URL Scraping filter class"""

    class Valves(BaseModel):
        """Configuration valves for the filter"""
        enabled: bool = Field(default=True, description="Enable/disable URL scraping")
        max_content_length: int = Field(
            default=2000,
            description="Maximum characters of scraped content to include"
        )
        timeout: int = Field(
            default=10,
            description="Timeout in seconds for URL requests"
        )

    class UserValves(BaseModel):
        show_scraped_status: bool = Field(
            default=True,
            description="Show status of URL scraping"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.url_regex = re.compile(
            r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
        )

    async def inlet(
        self,
        body: Dict[str, Any],
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __user__: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process incoming messages to detect and scrape URLs"""
        if not self.valves.enabled or not body.get("messages"):
            return body

        try:
            user_message = next((m for m in reversed(body["messages"]) if m["role"] == "user"), None)
            if user_message:
                urls = self.url_regex.findall(user_message["content"])
                if urls:
                    scraped_content = await self._scrape_urls(urls)
                    self._add_scraped_content(body, ", ".join(urls), scraped_content)

        except Exception as e:
            print(f"URL scraping error: {str(e)}")

        return body

    async def _scrape_urls(self, urls: list) -> str:
        """Scrape content from multiple URLs"""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.valves.timeout)) as session:
            results = []
            for url in urls:
                try:
                    async with session.get(url) as response:
                        html = await response.text()
                        content = self._clean_html(html)
                        results.append(f"URL: {url}\nCONTENT: {content[:self.valves.max_content_length]}")
                except Exception as e:
                    results.append(f"URL: {url}\nERROR: {str(e)}")
            return "\n\n".join(results)

    def _clean_html(self, html: str) -> str:
        """Clean and extract text from HTML"""
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()

        # Get clean text with proper spacing
        text = soup.get_text(separator=' ', strip=True)

        # Collapse multiple whitespaces
        return ' '.join(text.split())

    def _add_scraped_content(self, body: dict, urls: str, content: str) -> None:
        """Add scraped content to system message"""
        system_message = next((m for m in body["messages"] if m["role"] == "system"), None)

        if system_message:
            system_message["content"] += f"\n\n[SCRAPED WEB CONTENT for URL: {urls}]\n{content}"
        else:
            body["messages"].insert(0, {
                "role": "system",
                "content": f"[SCRAPED WEB CONTENT for URL: {urls}]\n{content}"
            })

    async def outlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __user__: Optional[dict] = None,
    ) -> dict:
        """Optional post-processing"""
        return body
