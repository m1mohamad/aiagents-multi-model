#!/usr/bin/env python3
"""
Project Manager for Phase 4.5
Manages project-level organization of conversations
"""

import json
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ProjectManager:
    """Manages projects and their associated conversations"""

    def __init__(self, history_dir: Path):
        """
        Initialize ProjectManager

        Args:
            history_dir: Path to agent's history directory (e.g., /ai/claude/history)
        """
        self.history_dir = Path(history_dir)
        self.projects_file = self.history_dir / "projects.json"
        self._ensure_projects_file()

    def _ensure_projects_file(self):
        """Create projects.json if it doesn't exist"""
        if not self.projects_file.exists():
            self.history_dir.mkdir(parents=True, exist_ok=True)
            initial_data = {"projects": {}}
            self._write_projects(initial_data)

    def _read_projects(self) -> dict:
        """
        Read projects.json with file locking

        Returns:
            Dictionary containing all projects
        """
        try:
            with open(self.projects_file, 'r') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            # Reinitialize if corrupted or missing
            return {"projects": {}}

    def _write_projects(self, data: dict):
        """
        Write projects.json with file locking

        Args:
            data: Dictionary to write to projects.json
        """
        with open(self.projects_file, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def create_project(self, name: str, description: str = "") -> bool:
        """
        Create a new project

        Args:
            name: Project name (used as identifier)
            description: Optional project description

        Returns:
            True if created, False if already exists
        """
        data = self._read_projects()

        if name in data["projects"]:
            return False

        data["projects"][name] = {
            "created": datetime.now().isoformat(),
            "description": description,
            "conversations": [],
            "last_activity": datetime.now().isoformat()
        }

        self._write_projects(data)
        return True

    def get_project(self, name: str) -> Optional[Dict]:
        """
        Get project details

        Args:
            name: Project name

        Returns:
            Project dict or None if not found
        """
        data = self._read_projects()
        return data["projects"].get(name)

    def list_projects(self) -> List[Dict]:
        """
        List all projects

        Returns:
            List of project dicts with name included
        """
        data = self._read_projects()
        projects = []

        for name, details in data["projects"].items():
            project = {"name": name}
            project.update(details)
            projects.append(project)

        # Sort by last_activity, most recent first
        projects.sort(key=lambda x: x.get("last_activity", ""), reverse=True)
        return projects

    def update_activity(self, name: str):
        """
        Update last_activity timestamp for a project

        Args:
            name: Project name
        """
        data = self._read_projects()

        if name in data["projects"]:
            data["projects"][name]["last_activity"] = datetime.now().isoformat()
            self._write_projects(data)

    def add_conversation(self, project_name: str, conversation_name: str):
        """
        Link a conversation to a project

        Args:
            project_name: Project name
            conversation_name: Conversation context name
        """
        data = self._read_projects()

        if project_name in data["projects"]:
            if conversation_name not in data["projects"][project_name]["conversations"]:
                data["projects"][project_name]["conversations"].append(conversation_name)
                data["projects"][project_name]["last_activity"] = datetime.now().isoformat()
                self._write_projects(data)
