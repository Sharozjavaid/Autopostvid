#!/usr/bin/env python3
"""
Agent Memory - Persistent memory system for the Claude agent.

This module provides text-file based persistence for:
1. Conversation summary - Rolling summary of older context
2. Recent messages - Last N messages with full content
3. Current project - Active script, slides, paths
4. Insights - Learnings the agent notes for itself

Memory Structure:
    memory/
        conversation_summary.txt    # Rolling summary of older context
        recent_messages.json        # Last 20 messages (full content)
        current_project.json        # Active project state
        insights.txt                # Agent's self-improvement notes

Usage:
    from agent_memory import AgentMemory
    
    memory = AgentMemory()
    
    # Add a message
    memory.add_message("user", "Make a script about 5 stoic philosophers")
    memory.add_message("assistant", "I'll create that for you...")
    
    # Get context for the agent
    context = memory.get_context()
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime


class AgentMemory:
    """
    Text-file based memory system for the Claude agent.
    
    Features:
    - Automatic summarization of old messages
    - Project state persistence between sessions
    - Agent insights/notes storage
    - Context builder for prompts
    """
    
    DEFAULT_MAX_RECENT_MESSAGES = 20
    
    def __init__(self, memory_dir: str = "memory"):
        """
        Initialize memory system.
        
        Args:
            memory_dir: Directory to store memory files
        """
        self.memory_dir = memory_dir
        
        # File paths
        self.summary_file = os.path.join(memory_dir, "conversation_summary.txt")
        self.messages_file = os.path.join(memory_dir, "recent_messages.json")
        self.project_file = os.path.join(memory_dir, "current_project.json")
        self.insights_file = os.path.join(memory_dir, "insights.txt")
        
        # Create directory if needed
        os.makedirs(memory_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._init_files()
        
        print(f"🧠 AgentMemory initialized at {memory_dir}/")
    
    def _init_files(self):
        """Initialize memory files if they don't exist."""
        if not os.path.exists(self.summary_file):
            with open(self.summary_file, 'w') as f:
                f.write("# Conversation Summary\n\n(No conversation history yet)\n")
        
        if not os.path.exists(self.messages_file):
            with open(self.messages_file, 'w') as f:
                json.dump({"messages": [], "total_count": 0}, f)
        
        if not os.path.exists(self.project_file):
            with open(self.project_file, 'w') as f:
                json.dump({"active_project": None}, f)
        
        if not os.path.exists(self.insights_file):
            with open(self.insights_file, 'w') as f:
                f.write("# Agent Insights\n\n")
                f.write("## User Preferences\n\n")
                f.write("(None recorded yet)\n\n")
                f.write("## Learnings\n\n")
                f.write("(None recorded yet)\n")
    
    # ==================== MESSAGE MANAGEMENT ====================
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata (tool calls, etc.)
        """
        # Load current messages
        with open(self.messages_file, 'r') as f:
            data = json.load(f)
        
        messages = data.get("messages", [])
        total_count = data.get("total_count", 0)
        
        # Create new message
        message = {
            "id": total_count + 1,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        messages.append(message)
        total_count += 1
        
        # Check if we need to summarize
        if len(messages) > self.DEFAULT_MAX_RECENT_MESSAGES:
            # Summarize oldest messages
            messages_to_summarize = messages[:-self.DEFAULT_MAX_RECENT_MESSAGES]
            messages = messages[-self.DEFAULT_MAX_RECENT_MESSAGES:]
            
            self._add_to_summary(messages_to_summarize)
        
        # Save
        with open(self.messages_file, 'w') as f:
            json.dump({
                "messages": messages,
                "total_count": total_count
            }, f, indent=2)
    
    def get_recent_messages(self, limit: int = None) -> List[Dict]:
        """
        Get recent messages.
        
        Args:
            limit: Max number of messages to return
        
        Returns:
            List of message dictionaries
        """
        with open(self.messages_file, 'r') as f:
            data = json.load(f)
        
        messages = data.get("messages", [])
        
        if limit and limit < len(messages):
            return messages[-limit:]
        
        return messages
    
    def _add_to_summary(self, messages: List[Dict]) -> None:
        """
        Add summarized messages to the summary file.
        
        Args:
            messages: Messages to summarize
        """
        with open(self.summary_file, 'r') as f:
            current_summary = f.read()
        
        # Remove placeholder if present
        if "(No conversation history yet)" in current_summary:
            current_summary = "# Conversation Summary\n\n"
        
        # Create summary of messages
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        summary_block = f"\n## Session: {timestamp}\n\n"
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            # Truncate long content
            if len(content) > 200:
                content = content[:200] + "..."
            
            summary_block += f"- **{role}**: {content}\n"
        
        current_summary += summary_block
        
        with open(self.summary_file, 'w') as f:
            f.write(current_summary)
    
    # ==================== PROJECT STATE ====================
    
    def save_project(self, project_data: Dict) -> None:
        """
        Save current project state.
        
        Args:
            project_data: Project dictionary with script, slides, paths, etc.
        """
        with open(self.project_file, 'w') as f:
            json.dump({
                "active_project": project_data,
                "saved_at": datetime.now().isoformat()
            }, f, indent=2)
    
    def load_project(self) -> Optional[Dict]:
        """
        Load current project state.
        
        Returns:
            Project dictionary or None
        """
        try:
            with open(self.project_file, 'r') as f:
                data = json.load(f)
            return data.get("active_project")
        except:
            return None
    
    def clear_project(self) -> None:
        """Clear the current project."""
        with open(self.project_file, 'w') as f:
            json.dump({"active_project": None}, f)
    
    # ==================== INSIGHTS ====================
    
    def add_insight(self, category: str, insight: str) -> None:
        """
        Add an insight or learning.
        
        Args:
            category: Category (e.g., "User Preferences", "Learnings")
            insight: The insight text
        """
        with open(self.insights_file, 'r') as f:
            content = f.read()
        
        # Find the category section
        category_header = f"## {category}"
        if category_header not in content:
            # Add new category
            content += f"\n{category_header}\n\n"
        
        # Remove placeholder if present
        content = content.replace("(None recorded yet)", "")
        
        # Add insight with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d")
        new_insight = f"- [{timestamp}] {insight}\n"
        
        # Insert after category header
        parts = content.split(category_header)
        if len(parts) == 2:
            header_and_rest = parts[1].split("\n\n", 1)
            if len(header_and_rest) == 2:
                parts[1] = header_and_rest[0] + "\n\n" + new_insight + header_and_rest[1]
            else:
                parts[1] = header_and_rest[0] + "\n\n" + new_insight
            content = category_header.join(parts)
        
        with open(self.insights_file, 'w') as f:
            f.write(content)
    
    def get_insights(self) -> str:
        """
        Get all insights.
        
        Returns:
            Insights file content
        """
        with open(self.insights_file, 'r') as f:
            return f.read()
    
    # ==================== CONTEXT BUILDER ====================
    
    def get_context(self, include_summary: bool = True, include_insights: bool = True) -> str:
        """
        Build context string for the agent.
        
        This provides the agent with:
        - Conversation summary (older context)
        - Recent messages
        - Current project state
        - Insights/preferences
        
        Args:
            include_summary: Include conversation summary
            include_insights: Include agent insights
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add summary
        if include_summary:
            with open(self.summary_file, 'r') as f:
                summary = f.read()
            if "(No conversation history yet)" not in summary:
                context_parts.append("## Previous Context\n" + summary)
        
        # Add project state
        project = self.load_project()
        if project:
            project_summary = self._summarize_project(project)
            context_parts.append("## Current Project\n" + project_summary)
        
        # Add insights
        if include_insights:
            insights = self.get_insights()
            if "(None recorded yet)" not in insights:
                context_parts.append("## Agent Notes\n" + insights)
        
        return "\n\n---\n\n".join(context_parts) if context_parts else ""
    
    def _summarize_project(self, project: Dict) -> str:
        """Create a brief summary of the project state."""
        lines = []
        
        if project.get("title"):
            lines.append(f"- **Title**: {project['title']}")
        
        if project.get("topic"):
            lines.append(f"- **Topic**: {project['topic']}")
        
        slides = project.get("slides", [])
        if slides:
            lines.append(f"- **Slides**: {len(slides)} slides")
        
        image_paths = [p for p in project.get("image_paths", []) if p]
        if image_paths:
            lines.append(f"- **Generated Images**: {len(image_paths)}")
        
        if project.get("video_path"):
            lines.append(f"- **Video**: {project['video_path']}")
        
        return "\n".join(lines) if lines else "(No active project)"
    
    # ==================== SESSION MANAGEMENT ====================
    
    def clear_recent_messages(self) -> None:
        """Clear recent messages (keeps summary)."""
        with open(self.messages_file, 'w') as f:
            json.dump({"messages": [], "total_count": 0}, f)
    
    def clear_all(self) -> None:
        """Clear all memory (fresh start)."""
        self._init_files()
        with open(self.summary_file, 'w') as f:
            f.write("# Conversation Summary\n\n(No conversation history yet)\n")
        with open(self.messages_file, 'w') as f:
            json.dump({"messages": [], "total_count": 0}, f)
        with open(self.project_file, 'w') as f:
            json.dump({"active_project": None}, f)
        with open(self.insights_file, 'w') as f:
            f.write("# Agent Insights\n\n")
            f.write("## User Preferences\n\n")
            f.write("(None recorded yet)\n\n")
            f.write("## Learnings\n\n")
            f.write("(None recorded yet)\n")
    
    def get_stats(self) -> Dict:
        """Get memory statistics."""
        with open(self.messages_file, 'r') as f:
            data = json.load(f)
        
        return {
            "recent_messages": len(data.get("messages", [])),
            "total_messages": data.get("total_count", 0),
            "has_project": self.load_project() is not None,
            "memory_dir": self.memory_dir
        }


if __name__ == "__main__":
    # Test the memory system
    print("🧪 Testing AgentMemory")
    print("=" * 50)
    
    memory = AgentMemory()
    
    # Add some test messages
    memory.add_message("user", "Make a script about 5 stoic philosophers")
    memory.add_message("assistant", "I'll create a slideshow script about 5 influential Stoic philosophers...")
    memory.add_message("user", "Try the Cinzel font")
    memory.add_message("assistant", "I'll re-render the slides with the Cinzel font...")
    
    # Add an insight
    memory.add_insight("User Preferences", "User prefers classical fonts like Cinzel")
    
    # Get stats
    stats = memory.get_stats()
    print(f"\nMemory stats: {stats}")
    
    # Get context
    context = memory.get_context()
    print(f"\nContext preview:\n{context[:500]}...")
    
    print("\n✅ AgentMemory test complete")
