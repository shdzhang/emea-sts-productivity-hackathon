#!/usr/bin/env python3
"""
Service Alignment Assessment Module

This module provides functions to assess meeting activities against
specific STS service goals and deliverables.
"""

import re
from typing import Dict, List, Any


def parse_service_definition(markdown_content: str) -> Dict[str, Any]:
    """Parse service definition from markdown README file."""

    service_def = {
        'name': '',
        'overview': '',
        'key_activities': [],
        'deliverables': [],
        'success_metrics': [],
        'prerequisites': [],
        'target_audience': [],
        'duration': '',
        'service_type': ''
    }

    lines = markdown_content.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()

        # Parse section headers
        if line.startswith('# '):
            service_def['name'] = line[2:].strip()
        elif line.startswith('## Overview'):
            current_section = 'overview'
        elif line.startswith('## Key Activities'):
            current_section = 'key_activities'
        elif line.startswith('## Deliverables'):
            current_section = 'deliverables'
        elif line.startswith('## Success Metrics'):
            current_section = 'success_metrics'
        elif line.startswith('## Prerequisites'):
            current_section = 'prerequisites'
        elif line.startswith('## Target Audience'):
            current_section = 'target_audience'
        elif line.startswith('## Duration'):
            current_section = 'duration'
        elif line.startswith('## '):
            current_section = None

        # Parse content based on current section
        elif current_section and line:
            if line.startswith('- '):
                item = line[2:].strip()
                if current_section in ['key_activities', 'deliverables', 'success_metrics',
                                       'prerequisites', 'target_audience']:
                    service_def[current_section].append(item)
            elif current_section == 'overview' and not service_def['overview']:
                service_def['overview'] = line
            elif current_section == 'duration':
                service_def['duration'] = line

    # Determine service type from name
    if 'ML' in service_def['name'] or 'AI' in service_def['name'] or 'GenAI' in service_def['name']:
        service_def['service_type'] = 'ML & GenAI'
    elif 'Data Engineering' in service_def['name'] or 'Pipeline' in service_def['name']:
        service_def['service_type'] = 'Data Engineering'
    elif 'Platform' in service_def['name'] or 'Workspace' in service_def['name']:
        service_def['service_type'] = 'Platform'
    elif 'Warehouse' in service_def['name'] or 'SQL' in service_def['name']:
        service_def['service_type'] = 'Data Warehousing'
    else:
        service_def['service_type'] = 'General'

    return service_def


def extract_keywords(text: str) -> List[str]:
    """Extract important keywords from text for matching."""

    # Keywords to look for
    important_keywords = [
        'setup', 'configuration', 'implementation', 'deployment', 'training',
        'documentation', 'security', 'network', 'identity', 'access', 'control',
        'model', 'pipeline', 'data', 'etl', 'streaming', 'batch', 'real-time',
        'unity catalog', 'databricks', 'workspace', 'cluster', 'warehouse',
        'ml', 'ai', 'genai', 'rag', 'vector', 'embedding', 'fine-tuning',
        'monitoring', 'optimization', 'performance', 'cost', 'governance'
    ]

    text_lower = text.lower()
    found_keywords = []

    for keyword in important_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)

    return found_keywords


def activity_was_discussed(key_activity: str, meeting_activities: List[Dict]) -> bool:
    """Check if a key activity was discussed in the meeting."""

    activity_keywords = extract_keywords(key_activity)

    for meeting_activity in meeting_activities:
        meeting_keywords = meeting_activity.get('keywords', [])

        # Check for keyword overlap
        common_keywords = set(activity_keywords) & set(meeting_keywords)
        if len(common_keywords) >= 1:  # At least one keyword match
            return True

        # Direct text match (case-insensitive)
        if any(word in meeting_activity.get('content', '').lower()
               for word in key_activity.lower().split()[:3]):  # Check first 3 words
            return True

    return False


def find_evidence(key_activity: str, meeting_data: Dict) -> str:
    """Find evidence in meeting data that relates to the key activity."""

    evidence_pieces = []
    activity_lower = key_activity.lower()

    # Search in key decisions
    for decision in meeting_data.get('key_decisions', []):
        if any(word in decision.lower() for word in activity_lower.split()[:3]):
            evidence_pieces.append(f"Decision: {decision}")

    # Search in action items
    for action in meeting_data.get('action_items', []):
        task = action.get('task', '')
        if any(word in task.lower() for word in activity_lower.split()[:3]):
            evidence_pieces.append(f"Action: {task}")

    # Return first evidence found
    return evidence_pieces[0] if evidence_pieces else ""


def check_deliverable_progress(deliverable: str, meeting_data: Dict) -> Dict[str, str]:
    """Check the progress status of a deliverable based on meeting data."""

    progress = {
        'status': 'not_started',
        'evidence': ''
    }

    deliverable_lower = deliverable.lower()

    # Keywords indicating progress
    in_progress_keywords = ['working on', 'in progress', 'started', 'beginning', 'implementing']
    completed_keywords = ['completed', 'done', 'finished', 'deployed', 'delivered', 'operational']

    all_text = ' '.join([
        ' '.join(meeting_data.get('key_decisions', [])),
        ' '.join([a.get('task', '') for a in meeting_data.get('action_items', [])]),
        ' '.join(meeting_data.get('next_steps', []))
    ]).lower()

    # Check for completed status
    for keyword in completed_keywords:
        if keyword in all_text and any(word in all_text for word in deliverable_lower.split()[:3]):
            progress['status'] = 'completed'
            progress['evidence'] = f"Mentioned as {keyword}"
            return progress

    # Check for in-progress status
    for keyword in in_progress_keywords:
        if keyword in all_text and any(word in all_text for word in deliverable_lower.split()[:3]):
            progress['status'] = 'in_progress'
            progress['evidence'] = f"Currently {keyword}"
            return progress

    # Check if it's mentioned at all (implies some progress)
    if any(word in all_text for word in deliverable_lower.split()[:3]):
        progress['status'] = 'in_progress'
        progress['evidence'] = "Discussed in meeting"

    return progress


def get_default_service_definition() -> Dict[str, Any]:
    """Return a default service definition if specific one can't be loaded."""

    return {
        'name': 'General Technical Support',
        'overview': 'Technical support and guidance for Databricks platform',
        'key_activities': [
            'Requirements gathering',
            'Technical consultation',
            'Best practices guidance',
            'Problem resolution',
            'Knowledge transfer'
        ],
        'deliverables': [
            'Solution design',
            'Implementation guidance',
            'Documentation',
            'Training materials',
            'Support handover'
        ],
        'success_metrics': [
            'Customer requirements addressed',
            'Technical issues resolved',
            'Knowledge successfully transferred',
            'Customer satisfaction achieved'
        ],
        'service_type': 'General'
    }