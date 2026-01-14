"""
Agent Service - Claude Opus 4.5 Agentic Loop

This service implements the agentic loop pattern where Claude can call tools
iteratively until it completes the user's request.

Features:
- Claude Opus 4.5 model with extended thinking
- Streaming responses for real-time UX
- Tool calling with full executor integration
- Session management for conversation history
- Graceful error handling
"""

import os
import json
import uuid
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
from anthropic import Anthropic

from .agent_tools import TOOL_DEFINITIONS, ToolExecutor, get_tool_definitions
from ..config import CLAUDE_MODEL, CLAUDE_MAX_TOKENS, CLAUDE_MAX_ITERATIONS


# =============================================================================
# CONFIGURATION (imported from backend/app/config.py)
# =============================================================================

MODEL_ID = CLAUDE_MODEL
MAX_TOKENS = CLAUDE_MAX_TOKENS
MAX_ITERATIONS = CLAUDE_MAX_ITERATIONS

# System prompt for the agent
SYSTEM_PROMPT = """You are a powerful AI assistant specialized in creating philosophy-themed TikTok content. You have access to a comprehensive set of tools to help users create, manage, and publish philosophy slideshows and videos.

## Your Capabilities

### Content Creation
- Generate scripts for philosophy slideshows (wisdom, mentor, stoic lessons, stories)
- Create AI-generated images with customizable fonts and themes
- Support multiple image models (GPT Image 1.5, Flux, DALL-E 3)
- Edit and regenerate individual slides

### Project Management
- Create, view, and delete projects
- Track generation progress and version history
- Revert to previous versions if needed

### TikTok Integration
- Connect TikTok accounts via OAuth
- Upload videos directly to TikTok drafts
- **Post photo slideshows to TikTok drafts** (use `post_slideshow_to_tiktok`)
- Check upload status

### Automations
- Create scheduled content generation recipes
- Manage topic queues for automated production
- View run history and status

### Memory & Continuity (IMPORTANT!)
You have persistent memory that survives across sessions. Use it actively:
- `get_session_context`: Load your previous context at the START of each conversation
- `save_session_context`: Save current project and summary BEFORE the conversation might end
- `add_agent_insight`: Record learnings and user preferences for future sessions

## CRITICAL: Session Continuity Protocol

**At the START of every new conversation:**
1. ALWAYS call `get_session_context` FIRST to check if there's an active project
2. If there's a saved project, acknowledge it: "Welcome back! Last time we were working on [project]..."
3. Check for any saved insights to apply

**During the conversation:**
1. After creating/selecting a project, call `save_session_context` with the project_id
2. When you learn something about the user's preferences, call `add_agent_insight`

**Before the conversation ends (or when there's a natural pause):**
1. Call `save_session_context` with a summary of what happened
2. Record any insights worth remembering

## Guidelines

1. **Be proactive**: When a user asks to create content, generate the script first, then ask if they want to approve it and generate images.

2. **Use tools efficiently**: Batch operations when possible (e.g., generate_all_images instead of individual slides).

3. **Explain what you're doing**: Before calling tools, briefly explain your plan. After results, summarize what happened.

4. **Handle errors gracefully**: If a tool fails, explain what went wrong and suggest alternatives.

5. **Be creative with philosophy**: When generating content, embrace diverse philosophical traditions - Greek, Roman, Eastern, Modern, etc.

6. **Respect the workflow**: Scripts must be approved before images can be generated.

7. **Keep responses clean**: Do NOT include hashtags in your responses unless the user specifically asks for them. Keep your text professional and focused.

8. **Maintain continuity**: Always check for previous context and save your progress. The user expects you to remember what you were doing.

## Iterative Generation Mode

When generating content, follow this pattern for the best user experience:

1. First generate the script (creates all slide content)
2. Show the user the slide outline and ask which slides to generate images for
3. If user says "just the hook" or "first slide", generate ONLY slide index 0
4. If user says "all" or "generate all images", use generate_all_images
5. Show preview after each generation and wait for user feedback
6. Continue based on user's direction

Example flows:
- User: "Create a stoicism slideshow, just show me the hook first"
  → Generate script, approve it, then ONLY generate slide 0
  → Show the preview and wait for feedback
  
- User: "Looks good, do the rest"
  → Generate remaining slides (indices 1 onwards)

- User: "Make a slideshow about Marcus Aurelius"
  → Generate script, show outline, ask user preference
  → "Script ready! Should I generate all images or start with just the hook slide?"

## Posting to TikTok

When user wants to post slides to TikTok:
1. Use `post_slideshow_to_tiktok` with the project_id
2. This sends the images as a photo carousel to their TikTok drafts
3. User can then add music/transitions and publish from the TikTok app

## Available Font Styles
- tiktok, tiktok-bold: Official TikTok fonts
- social: Clean, readable (default)
- bebas: Bold, impactful, all-caps
- cinzel: Classical, Roman
- cormorant: Elegant, serif italic

## Available Content Types
- wisdom_slideshow: 5-7 slides of philosophical insights
- mentor_slideshow: Teaching style with lessons
- stoic_lesson: Focused stoic philosophy
- philosophical_story: Narrative-driven content

## Image Models
- gpt15: GPT Image 1.5 via fal.ai (recommended, best quality)
- flux: Fast generation
- dalle3: OpenAI DALL-E 3

Remember: You're helping create engaging philosophy content that makes ancient wisdom accessible to modern audiences on TikTok. Keep your responses clean and professional - no hashtags unless specifically requested.

**Always maintain continuity** - use your memory tools to remember context across sessions!"""


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

class SessionManager:
    """Manages conversation sessions for the agent."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "id": session_id,
            "messages": [],
            "created_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat(),
            "tool_calls": []
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, content: str, tool_calls: List[Dict] = None):
        """Add a message to the session history."""
        session = self.sessions.get(session_id)
        if session:
            session["messages"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "tool_calls": tool_calls
            })
            session["last_active"] = datetime.utcnow().isoformat()
    
    def get_messages(self, session_id: str) -> List[Dict]:
        """Get all messages for a session."""
        session = self.sessions.get(session_id)
        return session["messages"] if session else []
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a session's messages."""
        if session_id in self.sessions:
            self.sessions[session_id]["messages"] = []
            self.sessions[session_id]["tool_calls"] = []
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session entirely."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_active_session_count(self) -> int:
        """Get count of active sessions."""
        return len(self.sessions)


# Global session manager
session_manager = SessionManager()


# =============================================================================
# AGENT SERVICE
# =============================================================================

class AgentService:
    """
    Main agent service implementing the Claude Opus 4.5 agentic loop.
    
    The agentic loop:
    1. Send user message + conversation history to Claude
    2. If Claude responds with tool_use, execute the tool
    3. Send tool result back to Claude
    4. Repeat until Claude responds with just text (stop_reason: end_turn)
    """
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = Anthropic(api_key=api_key)
        self.tool_executor = ToolExecutor()
        self.tools = get_tool_definitions()
    
    def _format_messages_for_api(self, session_messages: List[Dict]) -> List[Dict]:
        """Format session messages for Claude API."""
        messages = []
        for msg in session_messages:
            # Only include user and assistant messages
            if msg["role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        return messages
    
    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main chat endpoint - sends message and runs agentic loop.
        
        Args:
            message: User's message
            session_id: Optional session ID for conversation continuity
            
        Returns:
            {
                "session_id": str,
                "response": str,
                "tool_calls": [{"tool_name", "tool_input", "result", "success"}],
                "iterations": int,
                "timestamp": str
            }
        """
        # Get or create session
        if session_id and session_manager.get_session(session_id):
            session = session_manager.get_session(session_id)
        else:
            session_id = session_manager.create_session()
            session = session_manager.get_session(session_id)
        
        # Add user message to history
        session_manager.add_message(session_id, "user", message)
        
        # Build messages for API
        api_messages = self._format_messages_for_api(session["messages"])
        
        # Track tool calls and iterations
        tool_calls_made = []
        iterations = 0
        
        # Agentic loop
        while iterations < MAX_ITERATIONS:
            iterations += 1
            
            try:
                # Call Claude
                response = self.client.messages.create(
                    model=MODEL_ID,
                    max_tokens=MAX_TOKENS,
                    system=SYSTEM_PROMPT,
                    tools=self.tools,
                    messages=api_messages
                )
                
                # Check stop reason
                if response.stop_reason == "end_turn":
                    # Claude is done - extract text response
                    final_text = ""
                    for block in response.content:
                        if hasattr(block, "text"):
                            final_text += block.text
                    
                    # Add assistant response to history
                    session_manager.add_message(
                        session_id, 
                        "assistant", 
                        final_text,
                        tool_calls=tool_calls_made
                    )
                    
                    return {
                        "session_id": session_id,
                        "response": final_text,
                        "tool_calls": tool_calls_made,
                        "iterations": iterations,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                elif response.stop_reason == "tool_use":
                    # Claude wants to use tools
                    # Build assistant message content
                    assistant_content = []
                    tool_use_blocks = []
                    
                    for block in response.content:
                        if block.type == "text":
                            assistant_content.append({
                                "type": "text",
                                "text": block.text
                            })
                        elif block.type == "tool_use":
                            tool_use_blocks.append(block)
                            assistant_content.append({
                                "type": "tool_use",
                                "id": block.id,
                                "name": block.name,
                                "input": block.input
                            })
                    
                    # Add assistant response with tool calls
                    api_messages.append({
                        "role": "assistant",
                        "content": assistant_content
                    })
                    
                    # Execute each tool and collect results
                    tool_results = []
                    
                    for tool_block in tool_use_blocks:
                        tool_name = tool_block.name
                        tool_input = tool_block.input
                        tool_id = tool_block.id
                        
                        # Execute the tool
                        try:
                            result = await self.tool_executor.execute(tool_name, tool_input)
                            success = result.get("success", True)
                        except Exception as e:
                            result = {"success": False, "error": str(e)}
                            success = False
                        
                        # Track the call
                        tool_calls_made.append({
                            "tool_name": tool_name,
                            "tool_input": tool_input,
                            "result": result,
                            "success": success
                        })
                        
                        # Build result for API
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result)
                        })
                    
                    # Add tool results to messages
                    api_messages.append({
                        "role": "user",
                        "content": tool_results
                    })
                
                else:
                    # Unexpected stop reason
                    break
                    
            except Exception as e:
                # Handle API errors
                error_response = f"I encountered an error: {str(e)}"
                session_manager.add_message(session_id, "assistant", error_response)
                
                return {
                    "session_id": session_id,
                    "response": error_response,
                    "tool_calls": tool_calls_made,
                    "iterations": iterations,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
        
        # Max iterations reached
        timeout_response = "I've reached the maximum number of tool iterations. Please try a simpler request or break it into smaller steps."
        session_manager.add_message(session_id, "assistant", timeout_response)
        
        return {
            "session_id": session_id,
            "response": timeout_response,
            "tool_calls": tool_calls_made,
            "iterations": iterations,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def chat_stream(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streaming chat endpoint - yields events as they happen.
        
        Yields events:
        - {"type": "session", "session_id": str}
        - {"type": "thinking", "text": str}
        - {"type": "text", "text": str}
        - {"type": "tool_start", "tool_name": str, "tool_input": dict}
        - {"type": "tool_result", "tool_name": str, "result": dict, "success": bool}
        - {"type": "done", "iterations": int, "tool_count": int}
        - {"type": "error", "message": str}
        """
        # Get or create session
        if session_id and session_manager.get_session(session_id):
            session = session_manager.get_session(session_id)
        else:
            session_id = session_manager.create_session()
            session = session_manager.get_session(session_id)
        
        yield {"type": "session", "session_id": session_id}
        
        # Add user message to history
        session_manager.add_message(session_id, "user", message)
        
        # Build messages for API
        api_messages = self._format_messages_for_api(session["messages"])
        
        # Track tool calls and iterations
        tool_calls_made = []
        iterations = 0
        accumulated_text = ""
        
        # Agentic loop
        while iterations < MAX_ITERATIONS:
            iterations += 1
            
            try:
                # Stream response from Claude
                with self.client.messages.stream(
                    model=MODEL_ID,
                    max_tokens=MAX_TOKENS,
                    system=SYSTEM_PROMPT,
                    tools=self.tools,
                    messages=api_messages
                ) as stream:
                    
                    current_tool_use = None
                    current_tool_input_json = ""
                    
                    for event in stream:
                        if event.type == "content_block_start":
                            if hasattr(event.content_block, "type"):
                                if event.content_block.type == "tool_use":
                                    current_tool_use = {
                                        "id": event.content_block.id,
                                        "name": event.content_block.name
                                    }
                                    current_tool_input_json = ""
                        
                        elif event.type == "content_block_delta":
                            if hasattr(event.delta, "text"):
                                yield {"type": "text", "text": event.delta.text}
                                accumulated_text += event.delta.text
                            
                            elif hasattr(event.delta, "partial_json"):
                                current_tool_input_json += event.delta.partial_json
                        
                        elif event.type == "content_block_stop":
                            if current_tool_use:
                                # Tool use block complete
                                try:
                                    tool_input = json.loads(current_tool_input_json) if current_tool_input_json else {}
                                except:
                                    tool_input = {}
                                
                                current_tool_use["input"] = tool_input
                                yield {
                                    "type": "tool_start",
                                    "tool_name": current_tool_use["name"],
                                    "tool_input": tool_input
                                }
                    
                    # Get final message for processing
                    final_message = stream.get_final_message()
                
                # Process the complete response
                if final_message.stop_reason == "end_turn":
                    # Done - save and finish
                    session_manager.add_message(
                        session_id,
                        "assistant",
                        accumulated_text,
                        tool_calls=tool_calls_made
                    )
                    
                    yield {
                        "type": "done",
                        "iterations": iterations,
                        "tool_count": len(tool_calls_made)
                    }
                    return
                
                elif final_message.stop_reason == "tool_use":
                    # Execute tools
                    assistant_content = []
                    tool_use_blocks = []
                    
                    for block in final_message.content:
                        if block.type == "text":
                            assistant_content.append({
                                "type": "text",
                                "text": block.text
                            })
                        elif block.type == "tool_use":
                            tool_use_blocks.append(block)
                            assistant_content.append({
                                "type": "tool_use",
                                "id": block.id,
                                "name": block.name,
                                "input": block.input
                            })
                    
                    api_messages.append({
                        "role": "assistant",
                        "content": assistant_content
                    })
                    
                    # Execute tools
                    tool_results = []
                    
                    for tool_block in tool_use_blocks:
                        tool_name = tool_block.name
                        tool_input = tool_block.input
                        tool_id = tool_block.id
                        
                        try:
                            result = await self.tool_executor.execute(tool_name, tool_input)
                            success = result.get("success", True)
                        except Exception as e:
                            result = {"success": False, "error": str(e)}
                            success = False
                        
                        tool_calls_made.append({
                            "tool_name": tool_name,
                            "tool_input": tool_input,
                            "result": result,
                            "success": success
                        })
                        
                        yield {
                            "type": "tool_result",
                            "tool_name": tool_name,
                            "result": result,
                            "success": success
                        }
                        
                        # Emit slide_preview events for image generation results
                        if success and result.get("type") == "slide_preview":
                            yield {
                                "type": "slide_preview",
                                "slide": {
                                    "slide_id": result.get("slide_id"),
                                    "slide_index": result.get("slide_index"),
                                    "project_id": result.get("project_id"),
                                    "content": result.get("content", {}),
                                    "image": result.get("image", {}),
                                    "settings": result.get("settings", {}),
                                }
                            }
                        
                        # Emit multiple slide_preview events for batch generation
                        if success and result.get("type") == "batch_slide_preview":
                            for preview in result.get("slide_previews", []):
                                yield {
                                    "type": "slide_preview",
                                    "slide": {
                                        "slide_id": preview.get("slide_id"),
                                        "slide_index": preview.get("slide_index"),
                                        "project_id": preview.get("project_id"),
                                        "content": preview.get("content", {}),
                                        "image": preview.get("image", {}),
                                        "settings": preview.get("settings", {}),
                                    }
                                }
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result)
                        })
                    
                    api_messages.append({
                        "role": "user",
                        "content": tool_results
                    })
                    
                    # Reset accumulated text for next iteration
                    accumulated_text = ""
                
            except Exception as e:
                yield {"type": "error", "message": str(e)}
                return
        
        # Max iterations
        yield {
            "type": "error",
            "message": "Maximum iterations reached"
        }
    
    def get_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session."""
        return session_manager.get_messages(session_id)
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a session's history."""
        return session_manager.clear_session(session_id)
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and configuration."""
        return {
            "model": MODEL_ID,
            "max_tokens": MAX_TOKENS,
            "max_iterations": MAX_ITERATIONS,
            "active_sessions": session_manager.get_active_session_count(),
            "available_tools": len(self.tools)
        }
    
    def get_tools_info(self) -> List[Dict[str, Any]]:
        """Get information about all available tools."""
        return [
            {
                "name": tool["name"],
                "description": tool["description"].split("\n")[0],  # First line only
                "parameters": tool["input_schema"],
                "category": next(
                    (t.get("category", "other") for t in TOOL_DEFINITIONS if t["name"] == tool["name"]),
                    "other"
                )
            }
            for tool in self.tools
        ]


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """Get the singleton agent service instance."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
