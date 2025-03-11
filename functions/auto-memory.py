"""Auto-memory filter for OpenWebUI
"""

import json
import os
import traceback
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Literal, Optional, Set

from fastapi import Request
from open_webui.main import app as webui_app
from open_webui.models.memories import Memories, MemoryModel
from open_webui.models.users import Users
from open_webui.utils.chat import generate_chat_completion
from pydantic import BaseModel, Field, model_validator
from starlette.responses import JSONResponse

""""
title: Auto-memory
original author: caplescrest
author: crooy
repo: https://github.com/crooy/openwebui-extras  --> feel free to contribute or submit issues
version: 0.6
changelog:
 - v0.6: all coded has been linted, formatted, and type-checked
 - v0.5-beta: Added memory operations (NEW/UPDATE/DELETE), improved code structure, added datetime handling
 - v0.4: Added LLM-based memory relevance, improved memory deduplication, better context handling
 - v0.3: migrated to openwebui v0.5, updated to use openai api by default
 - v0.2: checks existing memories to update them if needed instead of continually adding memories.
to do:
 - offer confirmation before adding
 - consider more of chat history when making a memory
 - fine-tune memory relevance thresholds
 - improve memory tagging system, also for filtering relevant memories
 - maybe add support for vector-database for storing memories
 - maybe there should be an action to archive a chat, but summarize it's conclusions and store it as a memory,
   although it would be more of a logbook than an personal memory
"""


class MemoryOperation(BaseModel):
    """Model for memory operations"""

    operation: Literal["NEW", "UPDATE", "DELETE"]
    id: Optional[str] = None
    content: Optional[str] = None
    tags: List[str] = []

    @model_validator(mode="after")
    def validate_fields(self) -> "MemoryOperation":
        """Validate required fields based on operation"""
        if self.operation in ["UPDATE", "DELETE"] and not self.id:
            raise ValueError("id is required for UPDATE and DELETE operations")
        if self.operation in ["NEW", "UPDATE"] and not self.content:
            raise ValueError("content is required for NEW and UPDATE operations")
        return self


class Filter:
    """Auto-memory filter class"""

    class Valves(BaseModel):
        """Configuration valves for the filter"""

        model: str = Field(
            default="gpt-3.5-turbo",
            description="Model name for memory processing",
        )
        related_memories_n: int = Field(
            default=10,
            description="Number of related memories to consider",
        )
        enabled: bool = Field(default=True, description="Enable/disable the auto-memory filter")

    class UserValves(BaseModel):
        show_status: bool = Field(default=True, description="Show status of memory processing")

    SYSTEM_PROMPT = """
    You are a memory manager. Analyze the user's message and existing memories to determine necessary operations.

    Rules:
    1. UPDATE if new information modifies existing memory (e.g. address change, preference update)
    2. GROUP related memories (e.g. combine "likes coffee" and "prefers lattes" into single memory)
    3. DELETE only if information is contradicted or obsolete
    4. NEW for completely novel information

    Memory Format:
    [
        {
            "operation": "NEW|UPDATE|DELETE",
            "id": "required_for_update_delete",
            "content": "full context with details",
            "tags": ["category", "specifics"]
        }
    ]

    Examples:
    User: "I now prefer almond milk over regular milk"
    Existing: [{"id": "123", "content": "User drinks milk daily", "tags": ["diet"]}]
    → [{"operation": "UPDATE", "id": "123", "content": "User prefers almond milk instead of regular milk", "tags": ["diet", "preferences"]}]

    User: "My coffee order is a double shot latte with oat milk"
    Existing: [
        {"id": "456", "content": "User likes lattes", "tags": ["coffee"]},
        {"id": "789", "content": "User prefers oat milk", "tags": ["diet"]}
    ]
    → [{"operation": "UPDATE", "id": "456", "content": "User's standard coffee order: double shot latte with oat milk", "tags": ["coffee", "preferences"]}]

    """

    def __init__(self) -> None:
        """Initialize the filter."""
        self.valves = self.Valves()
        self.stored_memories: Optional[List[Dict[str, Any]]] = None

    async def _process_user_message(self, message: str, user_id: str, user: Any) -> tuple[str, List[str]]:
        """Process a single user message and return memory context"""
        # Get relevant memories for context
        relevant_memories = await self.get_relevant_memories(message, user)

        # Identify and store new memories
        memories = await self.identify_memories(message, user, relevant_memories)
        memory_context = ""

        if memories:
            self.stored_memories = memories
            if user and await self.process_memories(memories, user):
                memory_context = "\nRecently stored memory: " + str(memories)

        return memory_context, relevant_memories

    def _update_message_context(self, body: dict, memory_context: str, relevant_memories: List[str]) -> None:
        """Update the message context with memory information"""
        if not memory_context and not relevant_memories:
            return

        context = memory_context
        if relevant_memories:
            context += "\nRelevant memories for current context:\n"
            context += "\n".join(f"- {mem}" for mem in relevant_memories)

        if "messages" in body:
            if body["messages"] and body["messages"][0]["role"] == "system":
                body["messages"][0]["content"] += context
            else:
                body["messages"].insert(0, {"role": "system", "content": context})

    async def inlet(
        self,
        body: Dict[str, Any],
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __user__: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process incoming messages and manage memories."""
        self.stored_memories = None
        if not body or not isinstance(body, dict) or not __user__:
            return body

        try:
            if "messages" in body and body["messages"]:
                user_messages = [m for m in body["messages"] if m["role"] == "user"]
                if user_messages:
                    user = Users.get_user_by_id(__user__["id"])
                    memory_context, relevant_memories = await self._process_user_message(user_messages[-1]["content"], __user__["id"], user)
                    self._update_message_context(body, memory_context, relevant_memories)
        except Exception as e:
            print(f"Error in inlet: {e}\n{traceback.format_exc()}\n")

        return body

    async def outlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __user__: Optional[dict] = None,
    ) -> dict:
        if not self.valves.enabled:
            return body

        # Add memory storage confirmation if memories were stored
        if self.stored_memories:
            try:
                # stored_memories is already a list of dicts
                if isinstance(self.stored_memories, list):
                    if "messages" in body:
                        confirmation = "I've stored the following information in my memory:\n"
                        for memory in self.stored_memories:
                            if memory["operation"] in ["NEW", "UPDATE"]:
                                confirmation += f"- {memory['content']}\n"
                        body["messages"].append({"role": "assistant", "content": confirmation})
                    self.stored_memories = None  # Reset after confirming

            except Exception as e:
                print(f"Error adding memory confirmation: {e}\n")

        return body

    def _validate_memory_operation(self, op: dict) -> bool:
        """Validate a single memory operation"""
        if not isinstance(op, dict):
            return False
        if "operation" not in op:
            return False
        if op["operation"] not in ["NEW", "UPDATE", "DELETE"]:
            return False
        if op["operation"] in ["UPDATE", "DELETE"] and "id" not in op:
            return False
        if op["operation"] in ["NEW", "UPDATE"] and "content" not in op:
            return False
        return True

    async def identify_memories(self, input_text: str, user: Any, existing_memories: Optional[List[str]] = None) -> List[dict]:
        """Improved memory identification with structured context"""
        try:

            print(f"\n input_text: {input_text}\n")

            # Get existing memories with IDs
            existing = [
                f"ID: {mem.id} | Content: {mem.content} | Tags: {', '.join(self._parse_memory_tags(mem.content))}"
                for mem in Memories.get_memories_by_user_id(user.id)
            ][:10]  # Limit to recent 10 for context

            print(f"\n existing: {existing}\n")

            promptAddendum = """

    Current datetime: {current_datetime}
    Existing memories:
    {existing_memories}

    User input: {user_input}
    """

            # Build dynamic prompt
            prompt = self.SYSTEM_PROMPT + promptAddendum.format(
                current_datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                existing_memories="\n".join(existing) if existing else "No existing memories",
                user_input=input_text
            )

            print(f"\n prompt: {prompt}\n")

            # Get and validate response
            response = await self.query_openai_api(self.valves.model, prompt, input_text, user)
            print(f"\n identify_memories: {response}\n")
            return self._validate_operations(response, user)

        except Exception as e:
            print(f"Memory identification error: {e}")
            return []

    def _validate_operations(self, response: str, user: Any) -> List[dict]:
        """Strict validation of memory operations"""
        valid_ops = []
        existing_ids = {str(mem.id) for mem in Memories.get_memories_by_user_id(user.id)}

        try:
            operations = json.loads(response)
            for op in operations:
                # Validate operation structure
                if not self._validate_memory_operation(op):
                    continue

                # Check ID existence for UPDATE/DELETE
                if op["operation"] in ["UPDATE", "DELETE"] and op["id"] not in existing_ids:
                    print(f"Invalid ID {op['id']} for {op['operation']}")
                    continue

                valid_ops.append(op)

        except Exception as e:
            print(f"Validation failed: {e}")

        return valid_ops

    async def query_openai_api(self, model: str, system_prompt: str, prompt: str, user: Any) -> str:
        """Use OpenWebUI's built-in chat completion with proper interface"""
        try:

            request = Request(scope={"type": "http", "app": webui_app})

            # Build form_data according to OpenWebUI spec
            form_data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": False
            }

            # Get response using official interface
            response = await generate_chat_completion(
                request=request,
                form_data=form_data,
                user=user,
                bypass_filter=True
            )

            # Handle response formats per OpenWebUI spec
            if isinstance(response, JSONResponse):
                content = response.body.decode("utf-8")
                return json.loads(content)["choices"][0]["message"]["content"]

            if isinstance(response, dict):  # Direct response case
                return response["choices"][0]["message"]["content"]

            raise ValueError(f"Unexpected response type: {type(response)}")

        except Exception as e:
            print(f"Error in chat completion: {str(e)}\n")
            raise Exception(f"API Error: {str(e)}")

    async def process_memories(self, memories: List[dict], user: Any) -> bool:
        """Process a list of memory operations"""
        try:
            for memory_dict in memories:
                try:
                    operation = MemoryOperation(**memory_dict)
                except ValueError as e:
                    print(f"Invalid memory operation: {e} {memory_dict}\n")
                    continue

                await self._execute_memory_operation(operation, user)
            return True

        except Exception as e:
            print(f"Error processing memories: {e}\n{traceback.format_exc()}\n")
            return False

    async def _execute_memory_operation(self, operation: MemoryOperation, user: Any) -> None:
        """Execute a single memory operation"""
        formatted_content = self._format_memory_content(operation)

        if operation.operation == "NEW":
            result = Memories.insert_new_memory(user_id=str(user.id), content=formatted_content)
            print(f"NEW memory result: {result}\n")

        elif operation.operation == "UPDATE" and operation.id:
            old_memory = Memories.get_memory_by_id(operation.id)
            if old_memory:
                Memories.delete_memory_by_id(operation.id)
            result = Memories.insert_new_memory(user_id=str(user.id), content=formatted_content)
            print(f"UPDATE memory result: {result}\n")

        elif operation.operation == "DELETE" and operation.id:
            deleted = Memories.delete_memory_by_id(operation.id)
            print(f"DELETE memory result: {deleted}\n")

    def _format_memory_content(self, operation: MemoryOperation) -> str:
        """Format memory content with tags if present"""
        if not operation.tags:
            return operation.content or ""
        return f"[Tags: {', '.join(operation.tags)}] {operation.content}"

    async def store_memory(
        self,
        memory: str,
        user: Any,
    ) -> str:
        try:
            # Validate inputs
            if not memory or not user:
                return "Invalid input parameters"

            print(f"Processing memory: {memory}\n")
            print(f"For user: {getattr(user, 'id', 'Unknown')}\n")

            # Insert memory using correct method signature
            try:
                result = Memories.insert_new_memory(user_id=str(user.id), content=str(memory))
                print(f"Memory insertion result: {result}\n")

            except Exception as e:
                print(f"Memory insertion failed: {e}\n")
                return f"Failed to insert memory: {e}"

            # Get existing memories by user ID (non-critical)
            try:
                existing_memories = Memories.get_memories_by_user_id(user_id=str(user.id))
                if existing_memories:
                    print(f"Found {len(existing_memories)} existing memories\n")
            except Exception as e:
                print(f"Failed to get existing memories: {e}\n")
                # Continue anyway as this is not critical

            return "Success"

        except Exception as e:
            print(f"Error in store_memory: {e}\n")
            print(f"Full error traceback: {traceback.format_exc()}\n")
            return f"Error storing memory: {e}"

    async def get_relevant_memories(self, current_message: str, user: Any) -> List[str]:
        """Tag-based relevance with LLM tag matching"""
        try:
            # Get all unique tags from memories
            all_tags = await self._get_all_memory_tags(user)
            if not all_tags:
                return []

            # Get relevant tags for query via LLM
            relevant_tags = await self._get_relevant_tags_for_query(current_message, list(all_tags), user)

            # Score memories by tag matches
            scored_memories = []
            for mem in Memories.get_memories_by_user_id(user_id=str(user.id)):
                mem_tags = self._parse_memory_tags(mem.content)
                score = len(set(mem_tags) & set(relevant_tags))
                scored_memories.append((mem.content, score))

            # Sort and filter
            sorted_memories = sorted(scored_memories, key=lambda x: (-x[1], x[0]))
            return [mem[0] for mem in sorted_memories if mem[1] > 0][:self.valves.related_memories_n]

        except Exception as e:
            print(f"Tag-based relevance error: {e}")
            return []

    async def _get_all_memory_tags(self, user: Any) -> Set[str]:
        """Extract all unique tags from user's memories"""
        tags = set()
        for mem in Memories.get_memories_by_user_id(user_id=str(user.id)):
            tags.update(self._parse_memory_tags(mem.content))
        return tags

    def _parse_memory_tags(self, content: str) -> List[str]:
        """Extract tags from memory content string"""
        if "[Tags:" in content:
            tag_part = content.split("]")[0].replace("[Tags:", "")
            return [t.strip().lower() for t in tag_part.split(",")]
        return []

    async def _get_relevant_tags_for_query(self, query: str, all_tags: List[str], user: Any) -> List[str]:
        """LLM-based tag selection from available memory tags"""
        prompt = f"""Select relevant tags from this list for the query: "{query}"

        Available tags: {', '.join(all_tags)}

        Return ONLY JSON in the following format: {{"relevant_tags": ["tag1", "tag2"]}}"""

        try:
            response = await self.query_openai_api(
                model=self.valves.model,
                system_prompt="You are a tag matching expert",
                prompt=prompt,
                user=user
            )
            result = json.loads(response)
            return [tag.lower() for tag in result.get("relevant_tags", [])]
        except Exception as e:
            print(f"Tag selection error: {e}")
            return []
