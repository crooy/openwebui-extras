"""
title: Add to Memory Action Button
author: Peter De-Ath
author_url: https://github.com/Peter-De-Ath
funding_url: https://github.com/open-webui
version: 0.3.0
changelog:
 - v0.2.0: migrated to openwebui v0.5
required_open_webui_version: 0.5 or above
"""

from pydantic import BaseModel, Field
from typing import Optional
from fastapi.requests import Request
from open_webui.models.users import Users
from open_webui.models.memories import Memories, MemoryModel
import uuid
import time


class Action:
    class Valves(BaseModel):
        enabled: bool = Field(
            default=True,
            description="Enable/disable the add memories action"
        )

    class UserValves(BaseModel):
        show_status: bool = Field(
            default=True,
            description="Show status of memory processing"
        )

    def __init__(self):
        self.valves = self.Valves()

    async def action(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
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
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": "Adding to Memories", "done": False},
                })

            memory_content = f"User: {last_user_message['content']}\nAssistant: {last_assistant_message['content']}"

            # add the assistant response to memories
            try:
                memory_model = MemoryModel(
                    id=str(uuid.uuid4()),
                    content=memory_content,
                    user_id=user.id,
                    created_at=int(time.time()),
                    updated_at=int(time.time())
                )
                memory_obj = await Memories.insert_new_memory(user, memory_model)
                print(f"Memory Added: {memory_obj}")
            except Exception as e:
                print(f"Error adding memory {str(e)}")
                if user_valves.show_status:
                    await __event_emitter__({
                        "type": "status",
                        "data": {
                            "description": "Error Adding Memory",
                            "done": True,
                        },
                    })

                    # add a citation to the message with the error
                    await __event_emitter__({
                        "type": "citation",
                        "data": {
                            "source": {"name": "Error:adding memory"},
                            "document": [str(e)],
                            "metadata": [{"source": "Add to Memory Action Button"}],
                        },
                    })

            if user_valves.show_status:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": "Memory Saved", "done": True},
                })
