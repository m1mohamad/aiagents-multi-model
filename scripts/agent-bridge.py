#!/usr/bin/env python3
"""
Agent Bridge - Simple agent-to-agent communication
Allows one agent to invoke another for specific tasks
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration
SHARED_MSG_DIR = Path("/ai/shared/agent-messages")


def send_message_to_agent(target_agent, message, source_context=None):
    """
    Send a message to another agent and get response

    Args:
        target_agent: 'claude', 'grok', or 'gemini'
        message: The message to send
        source_context: Optional context info from source agent

    Returns:
        Response from target agent
    """

    if target_agent not in ['claude', 'grok', 'gemini']:
        return f"Error: Unknown agent '{target_agent}'. Valid: claude, grok, gemini"

    # Log the cross-agent request
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "target": target_agent,
        "message": message[:100],  # First 100 chars
        "source_context": source_context
    }

    log_file = SHARED_MSG_DIR / "agent-calls.log"
    SHARED_MSG_DIR.mkdir(parents=True, exist_ok=True)

    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

    # Execute the target agent CLI
    try:
        # Use a special context for cross-agent requests
        context_name = f"agent-requests"

        result = subprocess.run(
            ['python3', f'/home/agent/{target_agent}-api.py', '--context', context_name, message],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error calling {target_agent}: {result.stderr}"

    except subprocess.TimeoutExpired:
        return f"Error: {target_agent} request timed out"
    except Exception as e:
        return f"Error: {e}"


def main():
    """
    CLI for agent-to-agent communication

    Usage from within any agent container:
        python3 /home/agent/agent-bridge.py claude "What's the weather?"
        python3 /home/agent/agent-bridge.py grok "What's trending?"
    """

    if len(sys.argv) < 3:
        print("Usage: agent-bridge.py TARGET_AGENT \"message\"")
        print("  TARGET_AGENT: claude, grok, or gemini")
        print("  message: The message to send")
        print("")
        print("Example:")
        print("  agent-bridge.py claude \"Explain quantum computing\"")
        sys.exit(1)

    target_agent = sys.argv[1].lower()
    message = sys.argv[2]

    response = send_message_to_agent(target_agent, message)
    print(response)


if __name__ == "__main__":
    main()
