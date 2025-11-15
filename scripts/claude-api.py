#!/usr/bin/env python3
"""
Claude Session-Based API Implementation with Conversation History
Uses Claude Pro browser session instead of API keys
Supports multi-turn conversations and context management
"""

import os
import sys
import json
import subprocess
import requests
import uuid
from datetime import datetime
from pathlib import Path

# Configuration
CONTEXT_DIR = Path("/ai/claude/context")
HISTORY_DIR = Path("/ai/claude/history")
SECRETS_FILE = CONTEXT_DIR / ".secrets.age"
AGE_KEY_FILE = Path.home() / ".age-key.txt"
CLAUDE_API_URL = "https://claude.ai/api"


def decrypt_session_token():
    """Decrypt Claude session token using age"""
    try:
        result = subprocess.run(
            ['age', '-d', '-i', str(AGE_KEY_FILE), str(SECRETS_FILE)],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: Cannot decrypt session token: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def get_organization_id(session_token):
    """Get the organization ID from Claude session"""
    try:
        headers = {
            "Cookie": f"sessionKey={session_token}",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "application/json"
        }

        response = requests.get(
            f"{CLAUDE_API_URL}/organizations",
            headers=headers,
            timeout=10
        )

        if response.status_code == 401:
            print("Error: Session token expired or invalid. Please re-extract from browser.", file=sys.stderr)
            sys.exit(1)

        response.raise_for_status()
        orgs = response.json()

        if not orgs or len(orgs) == 0:
            print("Error: No organizations found for this account.", file=sys.stderr)
            sys.exit(1)

        # Use first organization
        return orgs[0]['uuid']

    except requests.exceptions.RequestException as e:
        print(f"Error getting organization ID: {e}", file=sys.stderr)
        sys.exit(1)


def get_or_create_conversation(session_token, org_id, context_name):
    """Get existing conversation UUID or create new one for context"""
    context_path = HISTORY_DIR / context_name
    conversation_meta_file = context_path / "conversation_uuid.txt"

    # Check if we have a saved conversation UUID
    if conversation_meta_file.exists():
        conversation_uuid = conversation_meta_file.read_text().strip()
        return conversation_uuid

    # Create new conversation
    try:
        headers = {
            "Cookie": f"sessionKey={session_token}",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "name": f"Context: {context_name}",
            "uuid": str(uuid.uuid4())
        }

        response = requests.post(
            f"{CLAUDE_API_URL}/organizations/{org_id}/chat_conversations",
            headers=headers,
            json=payload,
            timeout=10
        )

        response.raise_for_status()
        conversation_data = response.json()
        conversation_uuid = conversation_data['uuid']

        # Save conversation UUID for future use
        context_path.mkdir(parents=True, exist_ok=True)
        conversation_meta_file.write_text(conversation_uuid)

        return conversation_uuid

    except requests.exceptions.RequestException as e:
        print(f"Error creating conversation: {e}", file=sys.stderr)
        sys.exit(1)


def send_message_to_claude(session_token, org_id, conversation_uuid, message):
    """Send message to Claude and get response via SSE stream"""
    try:
        headers = {
            "Cookie": f"sessionKey={session_token}",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "anthropic-client-sha": "unknown",
            "anthropic-client-version": "unknown"
        }

        payload = {
            "prompt": message,
            "timezone": "UTC",
            "attachments": [],
            "files": []
        }

        response = requests.post(
            f"{CLAUDE_API_URL}/organizations/{org_id}/chat_conversations/{conversation_uuid}/completion",
            headers=headers,
            json=payload,
            stream=True,
            timeout=120
        )

        if response.status_code == 401:
            print("Error: Session expired. Please re-extract sessionKey from browser.", file=sys.stderr)
            sys.exit(1)

        response.raise_for_status()

        # Parse Server-Sent Events (SSE) stream
        full_response = ""
        for line in response.iter_lines():
            if not line:
                continue

            line = line.decode('utf-8')

            # SSE format: "data: {json}"
            if line.startswith('data: '):
                data_str = line[6:]  # Remove "data: " prefix

                try:
                    data = json.loads(data_str)

                    # Extract completion text from different event types
                    if 'completion' in data:
                        full_response = data['completion']
                    elif 'delta' in data and 'text' in data['delta']:
                        full_response += data['delta']['text']

                except json.JSONDecodeError:
                    # Some SSE events might not be JSON
                    continue

        if not full_response:
            print("Error: No response received from Claude", file=sys.stderr)
            sys.exit(1)

        return full_response.strip()

    except requests.exceptions.Timeout:
        print("Error: Request timed out after 120 seconds", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error calling Claude API: {e}", file=sys.stderr)
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


def ensure_context_exists(context_name):
    """Create context directory and files if they don't exist"""
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


def chat(message, context_name=None, max_history=10):
    """Send message to Claude with conversation history (session-based)"""

    # Determine context
    if context_name is None:
        context_name = get_current_context()

    # Ensure context exists
    ensure_context_exists(context_name)
    set_current_context(context_name)

    # Get session token
    session_token = decrypt_session_token()

    # Get organization ID
    org_id = get_organization_id(session_token)

    # Get or create conversation for this context
    conversation_uuid = get_or_create_conversation(session_token, org_id, context_name)

    # Note: Claude web API maintains its own conversation history on the server
    # We still save locally for our records, but don't need to send history

    # Save user message locally
    save_message(context_name, "user", message)

    # Call Claude API
    try:
        assistant_message = send_message_to_claude(
            session_token,
            org_id,
            conversation_uuid,
            message
        )

        # Save assistant response locally
        save_message(context_name, "assistant", assistant_message)

        return assistant_message

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point"""

    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  claude-chat \"message\"                    # Use current context")
        print("  claude-chat --context NAME \"message\"      # Use specific context")
        print("  claude-chat --list                        # List contexts")
        print("  claude-chat --switch CONTEXT              # Switch context")
        sys.exit(1)

    # Handle special commands
    if sys.argv[1] == "--list":
        list_contexts()
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

    # Handle context flag
    context_name = None
    message_index = 1

    if sys.argv[1] == "--context":
        if len(sys.argv) < 4:
            print("Error: --context requires a name and message")
            sys.exit(1)
        context_name = sys.argv[2]
        message_index = 3

    # Get message
    message = sys.argv[message_index]

    # Chat
    response = chat(message, context_name)
    print(response)


if __name__ == "__main__":
    main()
