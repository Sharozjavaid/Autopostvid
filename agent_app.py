#!/usr/bin/env python3
"""
Agent Web App - Simple Flask interface for the Marketing Agent.

A clean, simple web UI with:
- Chat panel to talk with Claude
- Preview panel for generated images/videos
- Font selection buttons

Usage:
    python3 agent_app.py
    
    Then open http://localhost:5001 in your browser.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

# Import our agent modules
from agent_runner import AgentRunner
from agent_tools import AgentTools

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['JSON_AS_ASCII'] = False  # Fix Unicode encoding

# Global agent instance
agent_runner: Optional[AgentRunner] = None


def get_agent() -> AgentRunner:
    """Get or create the agent runner."""
    global agent_runner
    if agent_runner is None:
        agent_runner = AgentRunner()
        print("🤖 Agent initialized")
    return agent_runner


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Serve the main chat interface."""
    return render_template('agent_chat.html')


@app.route('/api/fonts', methods=['GET'])
def get_fonts():
    """Get available fonts."""
    agent = get_agent()
    result = agent.tools.list_available_fonts()
    return jsonify(result)


@app.route('/api/project', methods=['GET'])
def get_project():
    """Get current project state."""
    agent = get_agent()
    result = agent.tools.get_project_state()
    return jsonify(result)


@app.route('/api/memory/clear', methods=['POST'])
def clear_memory():
    """Clear conversation memory."""
    agent = get_agent()
    agent.clear_history()
    return jsonify({'success': True, 'message': 'Memory cleared'})


@app.route('/api/chat', methods=['POST'])
def chat():
    """Send a message to the agent."""
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        agent = get_agent()
        
        # Run async query in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(agent.query(message))
        finally:
            loop.close()
        
        # Get updated project state
        project = agent.tools.get_project_state()
        
        # Get image paths for preview
        image_paths = []
        if project.get('success') and project.get('project'):
            paths = project['project'].get('image_paths', [])
            image_paths = [p for p in paths if p]
        
        return jsonify({
            'success': True,
            'response': response,
            'project': project.get('project') if project.get('success') else None,
            'image_paths': image_paths,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/regenerate', methods=['POST'])
def regenerate_slide():
    """Regenerate a slide with different settings."""
    try:
        data = request.json
        slide_index = data.get('slide_index', 0)
        font_name = data.get('font_name')
        visual_style = data.get('visual_style', 'modern')
        
        agent = get_agent()
        
        if font_name:
            result = agent.tools.change_font_style(
                slide_index=slide_index,
                font_name=font_name,
                visual_style=visual_style
            )
        else:
            result = agent.tools.generate_single_slide(
                slide_index=slide_index,
                visual_style=visual_style
            )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Serve generated files
@app.route('/generated/<path:filename>')
def serve_generated(filename):
    """Serve generated images."""
    return send_from_directory('generated_slideshows', filename)


@app.route('/generated/backgrounds/<path:filename>')
def serve_backgrounds(filename):
    """Serve background images."""
    return send_from_directory('generated_slideshows/backgrounds', filename)


@app.route('/generated_videos/<path:filename>')
def serve_videos(filename):
    """Serve generated videos."""
    return send_from_directory('generated_videos', filename)


# ==================== MAIN ====================

if __name__ == '__main__':
    # Ensure output directories exist
    os.makedirs('generated_slideshows', exist_ok=True)
    os.makedirs('generated_slideshows/backgrounds', exist_ok=True)
    os.makedirs('generated_videos', exist_ok=True)
    os.makedirs('memory', exist_ok=True)
    os.makedirs('memory/learnings', exist_ok=True)
    
    print("\n" + "=" * 60)
    print("🚀 Marketing Agent Web Interface")
    print("=" * 60)
    print("Starting server at http://localhost:5001")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
