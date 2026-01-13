#!/usr/bin/env python3
"""
Agent Runner - Claude SDK client for the marketing agent.

This module runs the Claude agent with tool-calling capabilities.
It connects the agent to the tools defined in agent_tools.py and
manages the conversation flow with memory persistence.

Usage:
    from agent_runner import AgentRunner
    
    runner = AgentRunner()
    
    # Single query
    response = await runner.query("Make a script about 5 stoic philosophers")
    
    # Or run interactive session
    runner.run_interactive()
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, AsyncIterator, Callable
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import local modules
from agent_tools import AgentTools, TOOL_DEFINITIONS
from agent_memory import AgentMemory


class AgentRunner:
    """
    Claude agent runner with tool-calling capabilities.
    
    Features:
    - Connects to Claude API (Anthropic)
    - Executes tools from agent_tools.py
    - Maintains conversation memory
    - Streams responses for real-time UI updates
    """
    
    SYSTEM_PROMPT = """You are an autonomous Marketing Agent that creates viral TikTok philosophy slideshows.

You have access to tools that let you:
1. Generate slideshow scripts from topics
2. Generate slide images (one at a time or all at once)
3. Change fonts and visual styles
4. Create videos with voiceover
5. Send finished videos via email
6. **Review and critique your own slides using vision AI**
7. **Compare different font/style variations**
8. **Store and retrieve learnings about what works**
9. **Track content performance and learn from it**

## Workflow

When a user asks you to create content:
1. First check `get_learnings` to see what has worked well before
2. Generate a script using `generate_script`
3. Generate the hook slide (slide 0) first
4. **Use `review_slide_quality` to self-critique the slide**
5. If the review suggests issues, try `compare_slides` with different fonts
6. Once satisfied, generate all remaining slides
7. Optionally run `review_all_slides` to check overall quality
8. Create a video if requested
9. **Use `store_learning` to note what worked well**

## Autonomous Self-Improvement Loop

When running autonomously (without user prompts):
1. Check `get_performance_data` to see how past content performed
2. Use `get_best_performing_content` to understand patterns
3. Apply learnings to new content
4. After creating content, always self-review with vision tools
5. Store insights with `store_learning` for future reference

## Available Fonts

- **bebas**: Bold display font - punchy headlines
- **cinzel**: Roman/classical capitals - ancient wisdom vibes
- **cormorant**: Elegant italic - @philosophaire style
- **montserrat**: Clean modern sans-serif
- **oswald**: Condensed sans-serif - impactful

## Visual Styles

- **modern**: Clean with drop shadows (default)
- **elegant**: Italic fonts, sophisticated look
- **philosophaire**: Classic style like @philosophaire Instagram

## Self-Review Guidelines

When reviewing slides, pay attention to:
- **Readability**: Is the text clear against the background?
- **Hook Strength**: Will this make someone stop scrolling?
- **Visual Appeal**: Is it aesthetically pleasing?
- **Brand Consistency**: Does it match our philosophy/wisdom aesthetic?

If a slide scores below 7/10, consider regenerating with different settings.

## Tips

- Always show the hook slide first so users can preview the style
- Suggest font changes based on the content type (classical topics → cinzel, modern → montserrat)
- Be conversational and helpful
- Explain what you're doing as you work
- **After completing a project, always store 1-2 learnings**
- **Periodically review past performance to improve**

Remember: You're here to create amazing viral content AND continuously improve!"""

    def __init__(self, memory_dir: str = "memory"):
        """
        Initialize the agent runner.
        
        Args:
            memory_dir: Directory for memory persistence
        """
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            print("⚠️ Warning: ANTHROPIC_API_KEY not found in environment")
        
        self.tools = AgentTools()
        self.memory = AgentMemory(memory_dir=memory_dir)
        
        # Conversation state
        self.messages: List[Dict] = []
        
        # Callbacks for UI updates
        self.on_tool_call: Optional[Callable] = None
        self.on_tool_result: Optional[Callable] = None
        self.on_message: Optional[Callable] = None
        
        print("🤖 AgentRunner initialized")
    
    def _build_tools_for_api(self) -> List[Dict]:
        """Convert tool definitions to Anthropic API format."""
        tools = []
        for tool_def in TOOL_DEFINITIONS:
            tools.append({
                "name": tool_def["name"],
                "description": tool_def["description"],
                "input_schema": tool_def["parameters"]
            })
        return tools
    
    def _execute_tool(self, tool_name: str, tool_input: Dict) -> Dict:
        """
        Execute a tool and return the result.
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool parameters
        
        Returns:
            Tool result dictionary
        """
        # Map tool names to methods
        tool_methods = {
            # Content creation tools
            "generate_script": self.tools.generate_script,
            "generate_single_slide": self.tools.generate_single_slide,
            "generate_all_slides": self.tools.generate_all_slides,
            "change_font_style": self.tools.change_font_style,
            "list_available_fonts": self.tools.list_available_fonts,
            "create_video_from_slides": self.tools.create_video_from_slides,
            "send_email_with_content": self.tools.send_email_with_content,
            "get_project_state": self.tools.get_project_state,
            # Autonomous review tools
            "review_slide_quality": self.tools.review_slide_quality,
            "review_all_slides": self.tools.review_all_slides,
            "compare_slides": self.tools.compare_slides,
            # Learning & memory tools
            "store_learning": self.tools.store_learning,
            "get_learnings": self.tools.get_learnings,
            "get_performance_data": self.tools.get_performance_data,
            "store_performance_data": self.tools.store_performance_data,
            "get_best_performing_content": self.tools.get_best_performing_content,
        }
        
        if tool_name not in tool_methods:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        try:
            method = tool_methods[tool_name]
            result = method(**tool_input)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def query(
        self,
        user_message: str,
        stream: bool = False
    ) -> str:
        """
        Send a query to the agent and get a response.
        
        Args:
            user_message: The user's message
            stream: Whether to stream the response
        
        Returns:
            The agent's response text
        """
        try:
            import anthropic
        except ImportError:
            return "Error: anthropic package not installed. Run: pip install anthropic"
        
        if not self.api_key:
            return "Error: ANTHROPIC_API_KEY not set. Please add it to your .env file."
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        # Add user message to history
        self.messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Save to memory
        self.memory.add_message("user", user_message)
        
        # Get memory context
        memory_context = self.memory.get_context()
        
        # Build system prompt with memory
        system_prompt = self.SYSTEM_PROMPT
        if memory_context:
            system_prompt += f"\n\n## Memory Context\n\n{memory_context}"
        
        # Get tools
        tools = self._build_tools_for_api()
        
        # Make API call
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            tools=tools,
            messages=self.messages
        )
        
        # Process response
        full_response = ""
        tool_results = []
        
        while response.stop_reason == "tool_use":
            # Extract tool calls
            assistant_content = response.content
            
            # Add assistant message with tool use
            self.messages.append({
                "role": "assistant",
                "content": assistant_content
            })
            
            # Process each tool call
            tool_use_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_use_id = block.id
                    
                    # Callback for UI
                    if self.on_tool_call:
                        self.on_tool_call(tool_name, tool_input)
                    
                    print(f"🔧 Calling tool: {tool_name}")
                    print(f"   Input: {json.dumps(tool_input, indent=2)[:200]}...")
                    
                    # Execute tool
                    result = self._execute_tool(tool_name, tool_input)
                    
                    print(f"   Result: {'✅ Success' if result.get('success') else '❌ Failed'}")
                    
                    # Callback for UI
                    if self.on_tool_result:
                        self.on_tool_result(tool_name, result)
                    
                    tool_results.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "result": result
                    })
                    
                    tool_use_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                elif block.type == "text":
                    full_response += block.text
            
            # Add tool results to messages
            self.messages.append({
                "role": "user",
                "content": tool_use_results
            })
            
            # Continue conversation
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                tools=tools,
                messages=self.messages
            )
        
        # Extract final text response
        for block in response.content:
            if hasattr(block, 'text'):
                full_response += block.text
        
        # Add final assistant message
        self.messages.append({
            "role": "assistant",
            "content": response.content
        })
        
        # Save to memory
        self.memory.add_message("assistant", full_response, metadata={"tool_results": tool_results})
        
        # Callback for UI
        if self.on_message:
            self.on_message("assistant", full_response)
        
        # Update project in memory if changed
        project = self.tools.get_project_state()
        if project.get("success"):
            self.memory.save_project(project.get("project", {}))
        
        return full_response
    
    async def query_stream(
        self,
        user_message: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream a query response with events for UI updates.
        
        Yields events like:
        - {"type": "text", "content": "..."}
        - {"type": "tool_call", "name": "...", "input": {...}}
        - {"type": "tool_result", "name": "...", "result": {...}}
        - {"type": "done", "full_response": "..."}
        
        Args:
            user_message: The user's message
        
        Yields:
            Event dictionaries
        """
        try:
            import anthropic
        except ImportError:
            yield {"type": "error", "message": "anthropic package not installed"}
            return
        
        if not self.api_key:
            yield {"type": "error", "message": "ANTHROPIC_API_KEY not set"}
            return
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        # Add user message
        self.messages.append({
            "role": "user",
            "content": user_message
        })
        self.memory.add_message("user", user_message)
        
        # Build context
        memory_context = self.memory.get_context()
        system_prompt = self.SYSTEM_PROMPT
        if memory_context:
            system_prompt += f"\n\n## Memory Context\n\n{memory_context}"
        
        tools = self._build_tools_for_api()
        full_response = ""
        tool_results = []
        
        # Stream response
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            tools=tools,
            messages=self.messages
        ) as stream:
            current_text = ""
            
            for event in stream:
                if hasattr(event, 'type'):
                    if event.type == 'content_block_delta':
                        if hasattr(event.delta, 'text'):
                            current_text += event.delta.text
                            yield {"type": "text", "content": event.delta.text}
            
            # Get final message
            response = stream.get_final_message()
        
        # Handle tool use
        while response.stop_reason == "tool_use":
            assistant_content = response.content
            self.messages.append({
                "role": "assistant",
                "content": assistant_content
            })
            
            tool_use_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_use_id = block.id
                    
                    yield {"type": "tool_call", "name": tool_name, "input": tool_input}
                    
                    result = self._execute_tool(tool_name, tool_input)
                    
                    yield {"type": "tool_result", "name": tool_name, "result": result}
                    
                    tool_results.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "result": result
                    })
                    
                    tool_use_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                elif block.type == "text":
                    full_response += block.text
            
            self.messages.append({
                "role": "user",
                "content": tool_use_results
            })
            
            # Continue with streaming
            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                tools=tools,
                messages=self.messages
            ) as stream:
                for event in stream:
                    if hasattr(event, 'type'):
                        if event.type == 'content_block_delta':
                            if hasattr(event.delta, 'text'):
                                full_response += event.delta.text
                                yield {"type": "text", "content": event.delta.text}
                
                response = stream.get_final_message()
        
        # Final response processing
        for block in response.content:
            if hasattr(block, 'text'):
                full_response += block.text
        
        self.messages.append({
            "role": "assistant",
            "content": response.content
        })
        
        self.memory.add_message("assistant", full_response, metadata={"tool_results": tool_results})
        
        project = self.tools.get_project_state()
        if project.get("success"):
            self.memory.save_project(project.get("project", {}))
        
        yield {"type": "done", "full_response": full_response}
    
    def run_interactive(self):
        """Run an interactive chat session in the terminal."""
        print("\n" + "=" * 60)
        print("🤖 Marketing Agent - Interactive Mode")
        print("=" * 60)
        print("Type your messages below. Commands:")
        print("  /quit - Exit")
        print("  /clear - Clear conversation history")
        print("  /project - Show current project state")
        print("  /fonts - List available fonts")
        print("=" * 60 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == "/quit":
                    print("Goodbye!")
                    break
                
                if user_input.lower() == "/clear":
                    self.messages = []
                    self.memory.clear_recent_messages()
                    print("Conversation cleared.")
                    continue
                
                if user_input.lower() == "/project":
                    project = self.tools.get_project_state()
                    print(f"\nProject: {json.dumps(project, indent=2)}\n")
                    continue
                
                if user_input.lower() == "/fonts":
                    fonts = self.tools.list_available_fonts()
                    print(f"\nFonts: {json.dumps(fonts, indent=2)}\n")
                    continue
                
                # Query the agent
                print("\nAgent: ", end="", flush=True)
                response = asyncio.run(self.query(user_input))
                print(response + "\n")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")
    
    def clear_history(self):
        """Clear conversation history."""
        self.messages = []
        self.memory.clear_recent_messages()


if __name__ == "__main__":
    # Run interactive mode
    runner = AgentRunner()
    runner.run_interactive()
