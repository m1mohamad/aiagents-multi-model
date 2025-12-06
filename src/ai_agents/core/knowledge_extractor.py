#!/usr/bin/env python3
"""
Knowledge Extractor for Phase 4.5
Extracts decisions, facts, and patterns from conversations
"""

import re
from typing import Dict, List
from datetime import datetime


class KnowledgeExtractor:
    """Extracts structured knowledge from conversation history"""

    def __init__(self):
        """Initialize knowledge extractor"""
        pass

    def extract_decisions(self, conversation: List[Dict]) -> List[Dict]:
        """
        Extract decision points from conversation

        Looks for patterns like:
        - "we decided to..."
        - "we're using..."
        - "we chose..."
        - "the approach is..."

        Args:
            conversation: List of message dicts with 'role' and 'content'

        Returns:
            List of decision dicts with timestamp, text, context
        """
        decisions = []

        decision_patterns = [
            r"(?:we|I)\s+decided\s+to\s+(.+?)[\.\n]",
            r"(?:we|I)'re\s+using\s+(.+?)[\.\n]",
            r"(?:we|I)\s+chose\s+(.+?)[\.\n]",
            r"the\s+approach\s+is\s+(.+?)[\.\n]",
            r"(?:we|I)'ll\s+use\s+(.+?)[\.\n]",
        ]

        for msg in conversation:
            if msg['role'] == 'assistant':
                content = msg['content']

                for pattern in decision_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        decision_text = match.group(1).strip()

                        # Get context (previous sentence)
                        context = self._get_context(content, match.start())

                        decisions.append({
                            'timestamp': msg.get('timestamp', datetime.now().isoformat()),
                            'decision': decision_text,
                            'context': context
                        })

        # Deduplicate similar decisions
        return self._deduplicate(decisions, key='decision')

    def extract_facts(self, conversation: List[Dict]) -> List[Dict]:
        """
        Extract factual statements from conversation

        Looks for patterns like:
        - "X is Y"
        - "X uses Y"
        - "X supports Y"

        Args:
            conversation: List of message dicts

        Returns:
            List of fact dicts
        """
        facts = []

        fact_patterns = [
            r"(\w+(?:\s+\w+){0,3})\s+is\s+(.+?)[\.\n]",
            r"(\w+(?:\s+\w+){0,3})\s+uses\s+(.+?)[\.\n]",
            r"(\w+(?:\s+\w+){0,3})\s+supports\s+(.+?)[\.\n]",
        ]

        for msg in conversation:
            if msg['role'] == 'assistant':
                content = msg['content']

                for pattern in fact_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        subject = match.group(1).strip()
                        predicate = match.group(2).strip()

                        facts.append({
                            'timestamp': msg.get('timestamp', datetime.now().isoformat()),
                            'subject': subject,
                            'predicate': predicate,
                            'fact': f"{subject} {predicate}"
                        })

        return self._deduplicate(facts, key='fact')

    def extract_patterns(self, conversation: List[Dict]) -> List[Dict]:
        """
        Extract code patterns and technical approaches

        Looks for:
        - File paths mentioned
        - Technologies mentioned
        - Commands mentioned

        Args:
            conversation: List of message dicts

        Returns:
            List of pattern dicts
        """
        patterns = []

        # Extract file paths
        file_pattern = r'`([/\w\-_.]+(?:\.\w+)?)`'

        # Extract technology names (common patterns)
        tech_pattern = r'\b(Python|JavaScript|Docker|Podman|PostgreSQL|Redis|FastAPI|Flask|Django|React|Vue)\b'

        for msg in conversation:
            if msg['role'] == 'assistant':
                content = msg['content']

                # Find file paths
                file_matches = re.finditer(file_pattern, content)
                for match in file_matches:
                    patterns.append({
                        'timestamp': msg.get('timestamp', datetime.now().isoformat()),
                        'type': 'file',
                        'value': match.group(1)
                    })

                # Find technologies
                tech_matches = re.finditer(tech_pattern, content)
                for match in tech_matches:
                    patterns.append({
                        'timestamp': msg.get('timestamp', datetime.now().isoformat()),
                        'type': 'technology',
                        'value': match.group(1)
                    })

        return self._deduplicate(patterns, key='value')

    def _get_context(self, text: str, position: int, window: int = 100) -> str:
        """
        Get surrounding context for a match

        Args:
            text: Full text
            position: Position of match
            window: Characters to include before match

        Returns:
            Context string
        """
        start = max(0, position - window)
        end = min(len(text), position + window)
        context = text[start:end].strip()

        # Truncate to sentence boundaries
        sentences = context.split('.')
        if len(sentences) > 1:
            return sentences[-2].strip() if len(sentences) > 2 else sentences[0].strip()
        return context[:100]

    def _deduplicate(self, items: List[Dict], key: str) -> List[Dict]:
        """
        Remove duplicate items based on key

        Args:
            items: List of dicts
            key: Key to check for duplicates

        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []

        for item in items:
            value = item.get(key, '')
            normalized = value.lower().strip()

            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(item)

        return unique

    def extract_all(self, conversation: List[Dict]) -> Dict:
        """
        Extract all knowledge types from conversation

        Args:
            conversation: List of message dicts

        Returns:
            Dict with decisions, facts, patterns
        """
        return {
            'decisions': self.extract_decisions(conversation),
            'facts': self.extract_facts(conversation),
            'patterns': self.extract_patterns(conversation),
            'extracted_at': datetime.now().isoformat()
        }
