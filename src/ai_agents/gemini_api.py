#!/usr/bin/env python3
"""
Gemini Full API Implementation with Conversation History
Supports multi-turn conversations and context management
Phase 4.5: Adds project-level organization
"""

import os
import sys
import json
import subprocess
import google.generativeai as genai
from datetime import datetime
from pathlib import Path

from ai_agents.core.project_manager import ProjectManager

# Configuration
CONTEXT_DIR = Path("/ai/gemini/context")
HISTORY_DIR = Path("/ai/gemini/history")
SECRETS_FILE = CONTEXT_DIR / ".secrets.age"
AGE_KEY_FILE = Path.home() / ".age-key.txt"


def decrypt_api_key():
    """Decrypt Gemini API key using age"""
    try:
        result = subprocess.run(
            ['age', '-d', '-i', str(AGE_KEY_FILE), str(SECRETS_FILE)],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: Cannot decrypt API key: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def get_current_context():
    """Get the current active context, default to 'default'"""
    current_file = HISTORY_DIR / ".current"
    if current_file.exists():
        return current_file.read_text().strip()
    return "default"


def set_current_context(context_name):
    """Set the current active context"""
    current_file = HISTORY_DIR / ".current"
    current_file.write_text(context_name)


def ensure_context_exists(context_name, project_name=None):
    """Create context directory and files if they don't exist

    Args:
        context_name: Name of the conversation context
        project_name: Optional project to associate with this context
    """
    context_path = HISTORY_DIR / context_name
    context_path.mkdir(parents=True, exist_ok=True)

    conversation_file = context_path / "conversation.jsonl"
    metadata_file = context_path / "metadata.json"

    if not metadata_file.exists():
        metadata = {
            "name": context_name,
            "created": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "message_count": 0
        }
        # Add project field if specified
        if project_name:
            metadata["project"] = project_name

        metadata_file.write_text(json.dumps(metadata, indent=2))

    if not conversation_file.exists():
        conversation_file.touch()

    return context_path


def load_conversation_history(context_name, max_messages=20):
    """Load conversation history from context"""
    context_path = HISTORY_DIR / context_name
    conversation_file = context_path / "conversation.jsonl"

    if not conversation_file.exists():
        return []

    messages = []
    with open(conversation_file, 'r') as f:
        for line in f:
            if line.strip():
                messages.append(json.loads(line))

    # Return last N messages to stay within context window
    return messages[-max_messages:]


def save_message(context_name, role, content):
    """Append message to conversation history"""
    context_path = HISTORY_DIR / context_name
    conversation_file = context_path / "conversation.jsonl"
    metadata_file = context_path / "metadata.json"

    # Append message
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    with open(conversation_file, 'a') as f:
        f.write(json.dumps(message) + '\n')

    # Update metadata
    if metadata_file.exists():
        metadata = json.loads(metadata_file.read_text())
        metadata["last_used"] = datetime.now().isoformat()
        metadata["message_count"] = metadata.get("message_count", 0) + 1
        metadata_file.write_text(json.dumps(metadata, indent=2))


def list_contexts():
    """List all available contexts"""
    if not HISTORY_DIR.exists():
        print("No contexts found.")
        return

    current = get_current_context()
    contexts = []

    for context_path in HISTORY_DIR.iterdir():
        if context_path.is_dir():
            metadata_file = context_path / "metadata.json"
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
                contexts.append({
                    "name": context_path.name,
                    "is_current": context_path.name == current,
                    "messages": metadata.get("message_count", 0),
                    "last_used": metadata.get("last_used", "unknown")
                })

    if contexts:
        print("\nAvailable Contexts:")
        print("-" * 80)
        for ctx in sorted(contexts, key=lambda x: x["last_used"], reverse=True):
            marker = "* " if ctx["is_current"] else "  "
            print(f"{marker}{ctx['name']:<20} {ctx['messages']:>3} messages  Last: {ctx['last_used'][:19]}")
        print("-" * 80)
    else:
        print("No contexts found.")


def list_projects_display():
    """List all projects with statistics"""
    pm = ProjectManager(HISTORY_DIR)
    projects = pm.list_projects()

    if not projects:
        print("No projects found.")
        return

    print("\nAvailable Projects:")
    print("-" * 80)
    print(f"{'Project':<20} {'Convs':>5}  {'Last Activity':<19}  {'Description':<30}")
    print("-" * 80)

    for project in projects:
        name = project['name']
        conv_count = len(project.get('conversations', []))
        last_activity = project.get('last_activity', 'unknown')[:19]
        description = project.get('description', '')

        # Truncate description if too long
        if len(description) > 30:
            description = description[:27] + "..."

        print(f"{name:<20} {conv_count:>5}  {last_activity:<19}  {description:<30}")

    print("-" * 80)


def chat(message, context_name=None, project_name=None, max_history=10):
    """Send message to Gemini with conversation history

    Args:
        message: User message to send
        context_name: Optional conversation context name
        project_name: Optional project to associate with context
        max_history: Maximum number of historical messages to load
    """

    # Determine context
    if context_name is None:
        context_name = get_current_context()

    # Ensure context exists
    ensure_context_exists(context_name, project_name)
    set_current_context(context_name)

    # Link conversation to project if project specified
    if project_name:
        pm = ProjectManager(HISTORY_DIR)
        pm.add_conversation(project_name, context_name)

    # Get API key
    api_key = decrypt_api_key()
    genai.configure(api_key=api_key)

    # Load history
    history = load_conversation_history(context_name, max_history)

    # Build history for Gemini format
    gemini_history = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({
            "role": role,
            "parts": [msg["content"]]
        })

    # Save user message
    save_message(context_name, "user", message)

    # Call Gemini API
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Start chat with history
        chat_session = model.start_chat(history=gemini_history)

        # Send message
        response = chat_session.send_message(message)
        assistant_message = response.text

        # Save assistant response
        save_message(context_name, "assistant", assistant_message)

        return assistant_message

    except Exception as e:
        print(f"Error calling Gemini API: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point"""

    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  gemini-chat \"message\"                    # Use current context")
        print("  gemini-chat --context NAME \"message\"      # Use specific context")
        print("  gemini-chat --project NAME \"message\"      # Use project context")
        print("  gemini-chat --list                        # List contexts")
        print("  gemini-chat --projects                    # List projects")
        print("  gemini-chat --switch CONTEXT              # Switch context")
        sys.exit(1)

    # Handle special commands
    if sys.argv[1] == "--list":
        list_contexts()
        sys.exit(0)

    if sys.argv[1] == "--projects":
        list_projects_display()
        sys.exit(0)

    if sys.argv[1] == "--switch":
        if len(sys.argv) < 3:
            print("Error: --switch requires a context name")
            sys.exit(1)
        context_name = sys.argv[2]
        ensure_context_exists(context_name)
        set_current_context(context_name)
        print(f"Switched to context: {context_name}")
        sys.exit(0)

    # Handle context and project flags
    context_name = None
    project_name = None
    message_index = 1

    if sys.argv[1] == "--context":
        if len(sys.argv) < 4:
            print("Error: --context requires a name and message")
            sys.exit(1)
        context_name = sys.argv[2]
        message_index = 3

    elif sys.argv[1] == "--project":
        if len(sys.argv) < 4:
            print("Error: --project requires a name and message")
            sys.exit(1)
        project_name = sys.argv[2]
        message_index = 3

        # Create project if it doesn't exist
        pm = ProjectManager(HISTORY_DIR)
        if pm.create_project(project_name, f"Project created via CLI"):
            print(f"Created new project: {project_name}", file=sys.stderr)

        # Auto-generate context name from project (can be customized later)
        # For now, use project name as context name
        context_name = project_name

    # Get message (join all remaining args for multi-word messages)
    message = ' '.join(sys.argv[message_index:])

    # Chat
    response = chat(message, context_name, project_name)
    print(response)


if __name__ == "__main__":
    main()
