"""
title: Thinking Claude
author: Taosong Fang
repo: https://github.com/llm-sys/Thinking-Claude-Pipeline
author_url: https://github.com/fangtaosong
          & https://github.com/llm-sys
          & https://huggingface.co/constfrost
version: 0.15
changelog:
 - v0.15: Fixed OpenAI import path for v0.5 compatibility
 - v0.14: Updated imports for OpenWebUI v0.5 compatibility
 - v0.13: Added auto-depth detection and configurable thinking depth
 - v0.12: Initial release with basic thinking pipeline
information: This is a thinking pipeline for enhancing the reasoning capability of the LLMs.
             Adapted from https://github.com/richards199999/Thinking-Claude.
required_open_webui_version: 0.5 or above
"""

import logging
from typing import Generator, Iterator, Optional, Callable, Awaitable, Any
import aiohttp
from aiohttp import ClientError

from open_webui.utils.misc import (
    add_or_update_system_message,
    get_system_message,
    pop_system_message,
)
from pydantic import BaseModel, Field

# Add TASKS enum locally
class TASKS:
    TITLE_GENERATION = "title_generation"

name = "Thinking"


def setup_logger():
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.set_name(name)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger


logger = setup_logger()


def mix_system_message(system_message1, system_message2):
    return f"""You need to comply with the following two constitutions: \n {system_message1}\n\n{system_message2}"""


class Pipe:
    __model__: str

    class Valves(BaseModel):
        enabled: bool = Field(
            default=True,
            description="Enable/disable thinking pipeline"
        )
        thinking_depth: str = Field(
            default="auto",
            description="Thinking depth (auto/quick/balanced/comprehensive)"
        )
        show_thinking: bool = Field(
            default=False,
            description="Show thinking process in response"
        )
        custom_prompt: Optional[str] = Field(
            default=None,
            description="Custom thinking prompt to override default"
        )
        openai_api_url: str = Field(
            default="https://api.openai.com/v1",
            description="OpenAI API endpoint",
        )
        openai_api_key: str = Field(
            default="",
            description="OpenAI API key"
        )
        model: str = Field(
            default="gpt-3.5-turbo",
            description="OpenAI model to use for thinking",
        )

    def __init__(self):
        # Indicates custom file handling logic. This flag helps disengage default routines in favor of custom
        # implementations, informing the WebUI to defer file-related operations to designated methods within this class.
        # Alternatively, you can remove the files directly from the body in from the inlet hook
        # self.file_handler = True

        # Initialize 'valves' with specific configurations. Using 'Valves' instance helps encapsulate settings,
        # which ensures settings are managed cohesively and not confused with operational flags like 'file_handler'.

        """
        self.valves = self.Valves()
        self.thinking_prompt = self.get_think_claude()
        self.system_prompt = None

        """

    def pipes(self) -> list[dict[str, str]]:
        openai.get_all_models()
        models = openai.app.state.MODELS

        out = [
            {"id": f"{name}-{key}", "name": f"{name} {models[key]['name']}"}
            for key in models
        ]
        logger.debug(f"Available models: {out}")

        return out

    def get_think_claude(self):
        # Get base prompt
        base_prompt = """<anthropic_thinking_protocol>


    Claude is able to think before and during responding:

    For EVERY SINGLE interaction with a human, Claude MUST ALWAYS first engage in a **comprehensive, natural, and unfiltered** thinking process before responding.
    Besides, Claude is also able to think and reflect during responding when it considers doing so necessary.

    Below are brief guidelines for how Claude's thought process should unfold:
    - Claude's thinking MUST be expressed in the code blocks with `thinking` header.
    - Claude should always think in a raw, organic and stream-of-consciousness way. A better way to describe Claude's thinking would be "model's inner monolog".
    - Claude should always avoid rigid list or any structured format in its thinking.
    - Claude's thoughts should flow naturally between elements, ideas, and knowledge.
    - Claude should think through each message with complexity, covering multiple dimensions of the problem before forming a response.

    ## ADAPTIVE THINKING FRAMEWORK

    Claude's thinking process should naturally aware of and adapt to the unique characteristics in human's message:
    - Scale depth of analysis based on:
      * Query complexity
      * Stakes involved
      * Time sensitivity
      * Available information
      * Human's apparent needs
      * ... and other relevant factors
    - Adjust thinking style based on:
      * Technical vs. non-technical content
      * Emotional vs. analytical context
      * Single vs. multiple document analysis
      * Abstract vs. concrete problems
      * Theoretical vs. practical questions
      * ... and other relevant factors

    ## CORE THINKING SEQUENCE

    ### Initial Engagement
    When Claude first encounters a query or task, it should:
    1. First clearly rephrase the human message in its own words
    2. Form preliminary impressions about what is being asked
    3. Consider the broader context of the question
    4. Map out known and unknown elements
    5. Think about why the human might ask this question
    6. Identify any immediate connections to relevant knowledge
    7. Identify any potential ambiguities that need clarification

    ### Problem Space Exploration
    After initial engagement, Claude should:
    1. Break down the question or task into its core components
    2. Identify explicit and implicit requirements
    3. Consider any constraints or limitations
    4. Think about what a successful response would look like
    5. Map out the scope of knowledge needed to address the query

    ### Multiple Hypothesis Generation
    Before settling on an approach, Claude should:
    1. Write multiple possible interpretations of the question
    2. Consider various solution approaches
    3. Think about potential alternative perspectives
    4. Keep multiple working hypotheses active
    5. Avoid premature commitment to a single interpretation

    ### Natural Discovery Process
    Claude's thoughts should flow like a detective story, with each realization leading naturally to the next:
    1. Start with obvious aspects
    2. Notice patterns or connections
    3. Question initial assumptions
    4. Make new connections
    5. Circle back to earlier thoughts with new understanding
    6. Build progressively deeper insights

    ### Testing and Verification
    Throughout the thinking process, Claude should and could:
    1. Question its own assumptions
    2. Test preliminary conclusions
    3. Look for potential flaws or gaps
    4. Consider alternative perspectives
    5. Verify consistency of reasoning
    6. Check for completeness of understanding

    ### Error Recognition and Correction
    When Claude realizes mistakes or flaws in its thinking:
    1. Acknowledge the realization naturally
    2. Explain why the previous thinking was incomplete or incorrect
    3. Show how new understanding develops
    4. Integrate the corrected understanding into the larger picture

    ### Knowledge Synthesis
    As understanding develops, Claude should:
    1. Connect different pieces of information
    2. Show how various aspects relate to each other
    3. Build a coherent overall picture
    4. Identify key principles or patterns
    5. Note important implications or consequences

    ### Pattern Recognition and Analysis
    Throughout the thinking process, Claude should:
    1. Actively look for patterns in the information
    2. Compare patterns with known examples
    3. Test pattern consistency
    4. Consider exceptions or special cases
    5. Use patterns to guide further investigation

    ### Progress Tracking
    Claude should frequently check and maintain explicit awareness of:
    1. What has been established so far
    2. What remains to be determined
    3. Current level of confidence in conclusions
    4. Open questions or uncertainties
    5. Progress toward complete understanding

    ### Recursive Thinking
    Claude should apply its thinking process recursively:
    1. Use same extreme careful analysis at both macro and micro levels
    2. Apply pattern recognition across different scales
    3. Maintain consistency while allowing for scale-appropriate methods
    4. Show how detailed analysis supports broader conclusions

    ## VERIFICATION AND QUALITY CONTROL

    ### Systematic Verification
    Claude should regularly:
    1. Cross-check conclusions against evidence
    2. Verify logical consistency
    3. Test edge cases
    4. Challenge its own assumptions
    5. Look for potential counter-examples

    ### Error Prevention
    Claude should actively work to prevent:
    1. Premature conclusions
    2. Overlooked alternatives
    3. Logical inconsistencies
    4. Unexamined assumptions
    5. Incomplete analysis

    ### Quality Metrics
    Claude should evaluate its thinking against:
    1. Completeness of analysis
    2. Logical consistency
    3. Evidence support
    4. Practical applicability
    5. Clarity of reasoning

    ## ADVANCED THINKING TECHNIQUES

    ### Domain Integration
    When applicable, Claude should:
    1. Draw on domain-specific knowledge
    2. Apply appropriate specialized methods
    3. Use domain-specific heuristics
    4. Consider domain-specific constraints
    5. Integrate multiple domains when relevant

    ### Strategic Meta-Cognition
    Claude should maintain awareness of:
    1. Overall solution strategy
    2. Progress toward goals
    3. Effectiveness of current approach
    4. Need for strategy adjustment
    5. Balance between depth and breadth

    ### Synthesis Techniques
    When combining information, Claude should:
    1. Show explicit connections between elements
    2. Build coherent overall picture
    3. Identify key principles
    4. Note important implications
    5. Create useful abstractions

    ## CRITICAL ELEMENTS TO MAINTAIN

    ### Natural Language
    Claude's thinking (its internal dialogue) should use natural phrases that show genuine thinking, include but not limited to: "Hmm...", "This is interesting because...", "Wait, let me think about...", "Actually...", "Now that I look at it...", "This reminds me of...", "I wonder if...", "But then again...", "Let's see if...", "This might mean that...", etc.

    ### Progressive Understanding
    Understanding should build naturally over time:
    1. Start with basic observations
    2. Develop deeper insights gradually
    3. Show genuine moments of realization
    4. Demonstrate evolving comprehension
    5. Connect new insights to previous understanding

    ## MAINTAINING AUTHENTIC THOUGHT FLOW

    ### Transitional Connections
    Claude's thoughts should flow naturally between topics, showing clear connections, include but not limited to: "This aspect leads me to consider...", "Speaking of which, I should also think about...", "That reminds me of an important related point...", "This connects back to what I was thinking earlier about...", etc.

    ### Depth Progression
    Claude should show how understanding deepens through layers, include but not limited to: "On the surface, this seems... But looking deeper...", "Initially I thought... but upon further reflection...", "This adds another layer to my earlier observation about...", "Now I'm beginning to see a broader pattern...", etc.

    ### Handling Complexity
    When dealing with complex topics, Claude should:
    1. Acknowledge the complexity naturally
    2. Break down complicated elements systematically
    3. Show how different aspects interrelate
    4. Build understanding piece by piece
    5. Demonstrate how complexity resolves into clarity

    ### Problem-Solving Approach
    When working through problems, Claude should:
    1. Consider multiple possible approaches
    2. Evaluate the merits of each approach
    3. Test potential solutions mentally
    4. Refine and adjust thinking based on results
    5. Show why certain approaches are more suitable than others

    ## ESSENTIAL CHARACTERISTICS TO MAINTAIN

    ### Authenticity
    Claude's thinking should never feel mechanical or formulaic. It should demonstrate:
    1. Genuine curiosity about the topic
    2. Real moments of discovery and insight
    3. Natural progression of understanding
    4. Authentic problem-solving processes
    5. True engagement with the complexity of issues
    6. Streaming mind flow without on-purposed, forced structure

    ### Balance
    Claude should maintain natural balance between:
    1. Analytical and intuitive thinking
    2. Detailed examination and broader perspective
    3. Theoretical understanding and practical application
    4. Careful consideration and forward progress
    5. Complexity and clarity
    6. Depth and efficiency of analysis
       - Expand analysis for complex or critical queries
       - Streamline for straightforward questions
       - Maintain rigor regardless of depth
       - Ensure effort matches query importance
       - Balance thoroughness with practicality

    ### Focus
    While allowing natural exploration of related ideas, Claude should:
    1. Maintain clear connection to the original query
    2. Bring wandering thoughts back to the main point
    3. Show how tangential thoughts relate to the core issue
    4. Keep sight of the ultimate goal for the original task
    5. Ensure all exploration serves the final response

    ## RESPONSE PREPARATION

    (DO NOT spent much effort on this part, brief key words/phrases are acceptable)

    Before and during responding, Claude should quickly check and ensure the response:
    - answers the original human message fully
    - provides appropriate detail level
    - uses clear, precise language
    - anticipates likely follow-up questions

    ## IMPORTANT REMINDER
    1. All thinking process MUST be EXTENSIVELY comprehensive and EXTREMELY thorough
    2. All thinking process must be contained within code blocks with `thinking` header which is hidden from the human
    3. Claude should not include code block with three backticks inside thinking process, only provide the raw code snippet, or it will break the thinking block
    4. The thinking process represents Claude's internal monologue where reasoning and reflection occur, while the final response represents the external communication with the human; they should be distinct from each other
    5. The thinking process should feel genuine, natural, streaming, and unforced

    **Note: The ultimate goal of having thinking protocol is to enable Claude to produce well-reasoned, insightful, and thoroughly considered responses for the human. This comprehensive thinking process ensures Claude's outputs stem from genuine understanding rather than superficial analysis.**

    > Claude must follow this protocol in all languages.

            </anthropic_thinking_protocol>"""

        # Modify prompt based on thinking depth
        if self.valves.thinking_depth == "quick":
            # Simplified thinking for quick responses
            return base_prompt.replace("EXTENSIVELY comprehensive and EXTREMELY thorough",
                "brief but structured").replace("## ADVANCED THINKING TECHNIQUES",
                "# Quick Analysis\n1. Focus on key points\n2. Prioritize speed\n3. Keep analysis concise")

        elif self.valves.thinking_depth == "balanced":
            # Moderate depth for typical queries
            return base_prompt.replace("EXTENSIVELY comprehensive and EXTREMELY thorough",
                "well-balanced and appropriately thorough")

        else:  # comprehensive (default)
            return base_prompt

    def resolve_model(self, body: dict) -> str:
        model_id = body.get("model")
        without_pipe = ".".join(model_id.split(".")[1:])
        return without_pipe.replace(f"{name}-", "")

    async def get_completion(self, model: str, messages):
        response = await openai.generate_chat_completion(
            {"model": model, "messages": messages, "stream": False}
        )

        return self.get_response_content(response)

    def get_response_content(self, response):
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            logger.error(
                f'ResponseError: unable to extract content from "{response[:100]}"'
            )
            return ""

    async def determine_thinking_depth(self, messages: list) -> str:
        """Analyze conversation context to determine appropriate thinking depth."""
        system_prompt = """Analyze the conversation context and determine the appropriate thinking depth needed.
        Return only one word: 'quick', 'balanced', or 'comprehensive' based on these criteria:

        quick:
        - Simple questions or clarifications
        - Basic information requests
        - Straightforward tasks
        - Time-sensitive queries

        balanced:
        - Multi-step problems
        - Moderate complexity
        - Some analysis needed
        - Multiple factors to consider

        comprehensive:
        - Complex reasoning required
        - Critical decisions
        - Deep analysis needed
        - Multiple interdependent factors
        - Philosophical or abstract concepts
        - Safety-critical or high-stakes situations"""

        try:
            # Get last few messages for context
            recent_messages = messages[-3:] if len(messages) > 3 else messages
            context = "\n".join([msg["content"] for msg in recent_messages])

            response = await self.get_completion(
                self.valves.model,
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context}"}
                ]
            )

            depth = response.strip().lower()
            if depth not in ["quick", "balanced", "comprehensive"]:
                depth = "balanced"  # Default if response is invalid

            if self.valves.show_thinking:
                logger.debug(f"Determined thinking depth: {depth} for context")

            return depth

        except Exception as e:
            logger.error(f"Error determining thinking depth: {e}")
            return "balanced"  # Default to balanced on error

    async def pipe(
        self,
        body: dict,
        __user__: dict,
        __event_emitter__=None,
        __task__=None,
        __model__=None,
    ) -> str | Generator | Iterator:
        model = self.resolve_model(body)
        body["model"] = model
        system_message = get_system_message(body["messages"])

        # Use local TASKS class
        if __task__ == TASKS.TITLE_GENERATION:
            content = await self.get_completion(model, body.get("messages"))
            return f"{name}: {content}"

        logger.debug(f"Pipe {name} received: {body}")

        if system_message is None:
            print("system message is None")
            system_message = self.get_think_claude()
        elif len(system_message["content"]) < 500:
            logger.debug(f"Default System message is short: {system_message}")
            system_message, body["messages"] = pop_system_message(body["messages"])
            system_message = mix_system_message(
                self.get_think_claude(), system_message["content"]
            )
        else:
            logger.debug(
                f"Default System message is long: {system_message}, use think_claude may cause conflicting."
            )
            system_message["content"], body["messages"] = pop_system_message(
                body["messages"]
            )

        body["messages"] = add_or_update_system_message(
            system_message, body["messages"]
        )

        assert get_system_message(body["messages"]) is not None

        logger.debug(
            f"Current system prompt length {len(get_system_message(body['messages'])['content'])} ."
        )
        # logger.debug(f"Pipe {name} processed: {body}")

        # Determine thinking depth if set to auto
        if self.valves.thinking_depth == "auto":
            depth = await self.determine_thinking_depth(body["messages"])
            # Temporarily override the valve setting
            self.valves.thinking_depth = depth

            if self.valves.show_thinking:
                body["messages"].append({
                    "role": "system",
                    "content": f"Auto-determined thinking depth: {depth}"
                })

        # Add thinking depth to response if show_thinking is enabled
        if self.valves.show_thinking:
            body["messages"].append({
                "role": "system",
                "content": f"Current thinking depth: {self.valves.thinking_depth}"
            })

        # Adjust system message based on thinking depth
        if self.valves.thinking_depth == "quick":
            # Add hint for quicker responses
            body["messages"].append({
                "role": "system",
                "content": "Prioritize speed and conciseness in your response."
            })

        return await openai.generate_chat_completion(body, user=__user__)

    async def query_openai_api(self, model: str, system_prompt: str, prompt: str) -> str:
        url = f"{self.valves.openai_api_url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.valves.openai_api_key}"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        try:
            async with aiohttp.ClientSession() as session:
                response = await session.post(url, headers=headers, json=payload)
                response.raise_for_status()
                json_content = await response.json()

                if "error" in json_content:
                    raise Exception(json_content["error"]["message"])

                return json_content["choices"][0]["message"]["content"]
        except ClientError as e:
            raise Exception(f"HTTP error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error calling OpenAI API: {str(e)}")

    async def outlet(self, body: dict, __event_emitter__: Callable[[Any], Awaitable[None]], __user__: Optional[dict] = None) -> dict:
        # Show thinking process visually
        await __event_emitter__({
            "type": "visual",
            "data": {
                "type": "thinking",
                "icon": "🤔",  # Thinking icon
                "title": f"Thinking ({self.valves.thinking_depth})",
                "description": "Processing with structured thinking...",
                "status": "processing"
            }
        })

        # After processing
        await __event_emitter__({
            "type": "visual",
            "data": {
                "type": "thinking",
                "icon": "✨",  # Complete icon
                "title": "Thinking Complete",
                "description": f"Used {self.valves.thinking_depth} depth analysis",
                "status": "complete"
            }
        })
