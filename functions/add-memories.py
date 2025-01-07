"""
title: Add to Memory Action Button
original_author: Peter De-Ath
original_author_url: https://github.com/Peter-De-Ath
repo: https://github.com/crooy/openwebui-extras/tree/main
description: Adds a button to manually save conversations to memory with LLM-generated summaries
version: 0.3.0
changelog:
 - v0.3.2: Added conversation summary using LLM and configurable message history length
 - v0.3.1: Store both user message and assistant response in memory for better context
 - v0.2.0: migrated to openwebui v0.5
required_open_webui_version: 0.5 or above
features:
 - Stores conversations with timestamps
 - Uses LLM to generate concise summaries
 - Configurable message history length
 - Status notifications during processing
 - Error handling with user feedback
"""

import os
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

import aiohttp
from open_webui.models.memories import Memories
from open_webui.models.users import Users
from pydantic import BaseModel, Field


class Action:
    class Valves(BaseModel):
        enabled: bool = Field(default=True, description="Enable/disable the add memories action")
        openai_api_url: str = Field(
            default="https://api.openai.com/v1",
            description="OpenAI API endpoint",
        )
        openai_api_key: str = Field(default=os.getenv("OPENAI_API_KEY", ""), description="OpenAI API key")
        model: str = Field(
            default="gpt-3.5-turbo",
            description="OpenAI model to use for memory processing",
        )
        history_length: int = Field(
            default=10,
            description="Number of recent messages to include in summary",
        )

    class UserValves(BaseModel):
        show_status: bool = Field(default=True, description="Show status of memory processing")

    def __init__(self) -> None:
        self.valves = self.Valves()

    async def query_openai_api(
        self,
        messages: List[Dict[str, str]],
    ) -> str:
        """Query OpenAI API for conversation summary."""
        url = f"{self.valves.openai_api_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.valves.openai_api_key}",
        }
        system_prompt = """Summarize the conversation in one short paragraph. Focus on the main topic and key points discussed.
        Format: "Conversation summary: [your summary here]"
        Example: "Conversation summary: discussed different wood types suitable for sauna construction, focusing on cedar and hemlock's properties"
        Keep it concise but informative."""

        # Format conversation history
        conversation = "\n".join([f"{msg['role'].title()}: {msg['content']}" for msg in messages])

        payload = {
            "model": self.valves.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Conversation history:\n{conversation}"},
            ],
            "temperature": 0.7,
            "max_tokens": 200,
        }

        try:
            async with aiohttp.ClientSession() as session:
                response = await session.post(url, headers=headers, json=payload)
                response.raise_for_status()
                json_content = await response.json()
                return str(json_content["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"Error getting summary: {e}")
            return ""

    async def action(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __event_call__: Optional[Callable[..., Awaitable[Any]]] = None,
    ) -> Optional[dict]:
        if not self.valves.enabled:
            return None

        if not __user__ or "id" not in __user__:
            return None

        user_valves = __user__.get("valves")
        if not user_valves:
            user_valves = self.UserValves()

        if __event_emitter__:
            if not body or "messages" not in body or not body["messages"]:
                return None

            last_assistant_message = body["messages"][-1]
            last_user_message = body["messages"][-2]
            user = Users.get_user_by_id(__user__["id"])
            if not user:
                return None

            if user_valves.show_status:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "Adding to Memories", "done": False},
                    }
                )

            # Get recent message history
            messages = body["messages"]
            recent_messages = messages[-min(self.valves.history_length, len(messages)) :]

            # Format memory content
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            memory_content = f"Conversation on {timestamp}:\n"

            # Add summary only if OpenAI API key is available
            if self.valves.openai_api_key:
                try:
                    summary = await self.query_openai_api(recent_messages)
                    if summary:
                        memory_content += f"{summary}\n"
                except Exception as e:
                    print(f"Error getting summary, continuing without it: {e}")

            # Add the rest of the content
            memory_content += f"last user message: {last_user_message['content']}\n" f"last assistant message: {last_assistant_message['content']}" + "\n".join(
                [f"{msg['role'].title()}: {msg['content']}" for msg in recent_messages]
            )

            # Add the memory
            try:
                result = Memories.insert_new_memory(user_id=str(user.id), content=str(memory_content))
                print(f"Memory Added: {result}")
            except Exception as e:
                print(f"Error adding memory {str(e)}")
                if user_valves.show_status:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "Error Adding Memory",
                                "done": True,
                            },
                        }
                    )

                    await __event_emitter__(
                        {
                            "type": "citation",
                            "data": {
                                "source": {"name": "Error:adding memory"},
                                "document": [str(e)],
                                "metadata": [{"source": "Add to Memory Action Button"}],
                            },
                        }
                    )

            if user_valves.show_status:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "Memory Saved", "done": True},
                    }
                )

            return body

        return None
