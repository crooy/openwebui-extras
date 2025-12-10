"""
title: DateTime Injector
author: crooy
description: Injects the current date and time into the chat on the first user message
author_url: https://github.com/crooy/openwebui-things
version: 0.1
required_open_webui_version: 0.5.0
"""

from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field


class Filter:
    class Valves(BaseModel):
        enabled: bool = Field(default=True, description="Enable/disable the datetime injector")
        timezone: str = Field(default="UTC", description="Timezone name, e.g. UTC or America/New_York")
        format: str = Field(default="%Y-%m-%d %H:%M:%S %Z", description="Datetime format string")

    class UserValves(BaseModel):
        show_status: bool = Field(default=False, description="Show status updates when injecting datetime")

    def __init__(self) -> None:
        self.valves = self.Valves()
        self._marker = "[datetime-injected]"

    def _safe_timezone(self, tz_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            return ZoneInfo("UTC")

    def _already_injected(self, messages: List[Dict[str, Any]]) -> bool:
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str) and self._marker in content:
                return True
        return False

    def _build_datetime_message(self) -> str:
        tz = self._safe_timezone(self.valves.timezone)
        now = datetime.now(tz)
        formatted_datetime = now.strftime(self.valves.format)
        weekday = now.strftime("%A")
        day_of_year = now.strftime("%j")
        week_number = now.strftime("%U")

        return (
            f"{self._marker} Current date/time: {formatted_datetime}\n"
            f"Day of week: {weekday}\n"
            f"Day of year: {day_of_year}\n"
            f"Week number: {week_number}\n"
            f"Timezone: {self.valves.timezone}"
        )

    def _inject_system_message(self, body: Dict[str, Any], content: str) -> None:
        messages = body.get("messages", [])
        if not messages:
            body["messages"] = [{"role": "system", "content": content}]
            return

        first = messages[0]
        if first.get("role") == "system":
            if self._marker not in first.get("content", ""):
                first["content"] = f"{first.get('content', '')}\n\n{content}"
        else:
            messages.insert(0, {"role": "system", "content": content})

    async def inlet(
        self,
        body: Dict[str, Any],
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __user__: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.valves.enabled:
            return body

        if not body or "messages" not in body:
            return body

        chat_id = body.get("chat_id")
        if not chat_id:
            return body

        messages: List[Dict[str, Any]] = body.get("messages", [])
        user_messages = [m for m in messages if m.get("role") == "user"]

        # Only inject on the first user message and avoid duplicates.
        if len(user_messages) != 1:
            return body
        if self._already_injected(messages):
            return body

        user_valves = __user__.get("valves") if __user__ else None
        show_status = bool(user_valves.show_status) if user_valves else self.UserValves().show_status

        if __event_emitter__ and show_status:
            await __event_emitter__({"type": "status", "data": {"description": "Adding current datetime", "done": False}})

        datetime_message = self._build_datetime_message()
        self._inject_system_message(body, datetime_message)

        if __event_emitter__ and show_status:
            await __event_emitter__({"type": "status", "data": {"description": "Datetime added", "done": True}})

        return body

    async def outlet(
        self,
        body: dict,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __user__: Optional[dict] = None,
    ) -> dict:
        return body
