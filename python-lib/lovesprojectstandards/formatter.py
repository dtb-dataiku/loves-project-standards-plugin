"""
formatter.py —> Generate markdown for extracted metadata.
"""

import re

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any


def _convert_ms_to_timestamp(ms: int) -> datetime:
    """Convert milliseconds to a timestamp."""
    return datetime.fromtimestamp(ms / 1000, tz=ZoneInfo('America/New_York'))

def _clean_text(text: str) -> str:
    """Replaces pipes to prevent breaking markdown tables."""

    if not text:
        return ''

    cleaned_text = re.sub(r'\s+', ' ', text.replace('|', ' - ').strip()) # Remove pipes
    cleaned_text = re.sub(r'#+\s+', '', cleaned_text) # Remove headers

    return cleaned_text.strip()

def _generate_table_rows(columns: list[dict]) -> str:
    """Iterates through columns to build table rows."""

    rows = []
    if not columns:
        return "| *No columns found* | - | - |"

    for c, column in enumerate(columns):
        col_name = column.get('name', f'Column_{c}')
        col_type = column.get('type', 'string')
        col_desc = _clean_text(column.get('description', ''))

        row = f"| **{col_name}** | `{col_type}` | {col_desc} |"
        rows.append(row)

    return '\n'.join(rows)

def dataset_to_markdown(dataset_metadata: dict[str, Any], dataset_sources: list[tuple[str, str]]=None) -> str:
    """Turns dictionary of dataset metadata into markdown string."""

    ds_name = dataset_metadata.get('name', 'unnamed dataset')
    ds_type = dataset_metadata.get('type', 'unknown type')
    ds_conn = dataset_metadata.get('connection', 'unknown connection')
    ds_proj = dataset_metadata.get('project_name', 'unknown project name')
    ds_pkey = dataset_metadata.get('project_key', 'unknown project key')
    ds_summary = _clean_text(dataset_metadata.get('short_description', 'No summary available.').replace('#', ''))
    ds_description = _clean_text(dataset_metadata.get('long_description', 'No detailed description provided.').replace('#', ''))

    if not ds_summary:
        ds_summary = 'No summary available.'

    if not ds_description:
        ds_description = 'No detailed description provided.'
        
    if (not dataset_sources) or (not isinstance(dataset_sources, list)):
        ds_sources = 'Not calculated.'
    else:
        ds_sources = ', '.join([f'{d[1]} [{d[0]}]' for d in dataset_sources])

    columns = dataset_metadata.get('columns', [])
    table_rows = _generate_table_rows(columns)

    timestamp = datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M:%S %Z')

    markdown_output = \
f"""
# [{ds_name}](dataset:{ds_pkey}.{ds_name})
**{ds_summary}**
> Connection: **{ds_conn} ({ds_type})**
> Project: **{ds_proj} ({ds_pkey})**
> Sources: **{ds_sources}**

## Description
{ds_description}

## Schema
| Column Name | Type | Description |
| :--- | :---: | :--- |
{table_rows}

---
*Auto-generated on {timestamp}*
"""

    return markdown_output

def folder_to_markdown(folder_metadata: dict[str, Any]) -> str:
    """Turns dictionary of folder metadata into markdown string."""

    mf_id = folder_metadata.get('id', 'xxxxxxxx')
    mf_name = folder_metadata.get('name', 'unnamed folder')
    mf_type = folder_metadata.get('type', 'unknown type')
    mf_conn = folder_metadata.get('connection', 'unknown connection')
    mf_summary = _clean_text(folder_metadata.get('short_description', 'No summary available.').replace('#', ''))
    mf_description = _clean_text(folder_metadata.get('description', 'No detailed description provided.').replace('#', ''))

    if not mf_summary:
        mf_summary = 'No summary available.'

    if not mf_description:
        mf_description = 'No detailed description provided.'

    timestamp = datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M:%S %Z')

    markdown_output = \
f"""
# [{mf_name}](managed_folder:{mf_id})
**{mf_summary}**
> ID: **{mf_id}**
> Connection: **{mf_conn} ({mf_type})**

## Description
{mf_description}

---
*Auto-generated on {timestamp}*
"""

    return markdown_output

def project_description_to_markdown(project_metadata: dict[str, Any]) -> str:
    """Turns dictionary of dataset metadata into markdown string."""

    project_key = project_metadata['project_key']
    name = project_metadata['name']
    short_description = project_metadata['short_description']
    description = project_metadata['description']
    owner = project_metadata['owner']
    created_by = project_metadata['created_by']
    created_on = project_metadata['created_on']
    
    created_on_ts = _convert_ms_to_timestamp(created_on)
    created_on_str = created_on_ts.strftime('%Y-%m-%d %H:%M:%S %Z')
    timestamp = datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M:%S %Z')

    markdown_output = \
f"""
# {name}
**{short_description}**
> Owner: **{owner}**
> Project key: **{project_key}**
> Created by: **{created_by}**
> Created on: **{created_on_str}**

## Description
{description}

---
*Auto-generated on {timestamp}*
"""
    
    return markdown_output

def placeholder_to_markdown(label: str='SECTION TITLE') -> str:
    """Create placeholder markdown string."""

    markdown_output = \
f"""
# PLACEHOLDER ARTICLE
{label}
"""
    
    return markdown_output
