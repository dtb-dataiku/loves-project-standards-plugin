"""
extractor.py —> Dataiku project- and dataset-level metadata.
"""

import dataiku
import networkx as nx

from typing import Any


def get_project_metadata() -> dict[str, Any]:
    """
    Return metadata for a single project.

    Returns
    -------
    dict with keys:
        project_key, name, short_description, description, owner,
        tags, status, folder, created_by, created_on, last_modified_on
    """
    
    client = dataiku.api_client()
    project = client.get_default_project()
    
    summary = project.get_summary()
    settings = project.get_settings().get_raw()
    timeline = project.get_timeline()
        

    # Creation_tag is the git-style first-commit metadata DSS stores
    creation_tag = summary.get("creationTag", {})

    # Get project folder from project location
    project_location = summary.get('projectLocation', [])
    project_folders = [p['name'] for p in reversed(project_location) if p['id'] != 'ROOT']
    project_folder = ' > '.join(project_folders)
    
    # Get project timeline
    last_modified_dt = timeline.get('lastModifiedOn', 0)

    return {
        "project_key": project.project_key,
        "name": summary.get("name", project.project_key),
        "short_description": summary.get("shortDesc", ""),
        "description": summary.get("description", ""),
        "owner": summary.get("ownerLogin", ""),
        "tags": sorted(summary.get("tags", []),),
        "status": settings.get("projectStatus", ""),
        "folder": project_folder,
        "created_by": creation_tag.get("lastModifiedBy", {}).get("login", ""),
        "created_on": creation_tag.get("lastModifiedOn", 0),
        "last_modified_on": last_modified_dt
    }

def list_project_datasets(tag_filter: list[str]=None, include_shared: bool=True) -> list[tuple[str, str]]:
    """
    List dataset names in a Dataiku project.
    
    Parameters
    ----------
    tag_filter : list[str]
        List of tags for filtering.
    include_shared : bool
        Include datasets shared to project.
    
    Returns
    -------
    list of tuples:
        Project key, Dataset name
    """

    try:
        client = dataiku.api_client()
        project = client.get_default_project()
        project_key = project.project_key
        
        dataset_items = project.list_datasets(as_type='listitems', include_shared=include_shared)

        datasets = [(d['projectKey'], d['name']) for d in dataset_items]

        if not tag_filter:
            return sorted(datasets)

        if isinstance(tag_filter, str):
            target_tags = {tag_filter}
        
        if isinstance(tag_filter, list):
            target_tags = set(tag_filter)

        filtered_datasets = []
        for d in dataset_items:
            dataset_tags = set(d.get('tags', []))

            # Check intersection: do they share any tags?
            has_overlap = not target_tags.isdisjoint(dataset_tags)
            if has_overlap:
                filtered_datasets.append((d.get('projectKey'), d.get('name')))

        return sorted(filtered_datasets)
    except Exception as e:
        print(f'Error getting datasets in {project_key}: {e}')
        return None

def list_project_managed_folders(tag_filter: list[str]=None) -> list[tuple[str, str]]:
    """
    List managed folder IDs in a Dataiku project.
    
    Parameters
    ----------
    tag_filter : list[str]
        List of tags for filtering.
    
    Returns
    -------
    list of tuples:
        Project key, Folder ID
    """

    try:
        client = dataiku.api_client()
        project = client.get_default_project()
        project_key = project.project_key
        
        folders = project.list_managed_folders()
        
        if not tag_filter:
            return sorted([(project_key, f['id']) for f in folders])

        if isinstance(tag_filter, str):
            target_tags = {tag_filter}
        
        if isinstance(tag_filter, list):
            target_tags = set(tag_filter)

        filtered_folders = []
        for f in folders:
            folder_tags = set(f.get('tags', []))

            # Check intersection: do they share any tags?
            has_overlap = not target_tags.isdisjoint(folder_tags)
            if has_overlap:
                filtered_folders.append((project_key, f['id']))

        return sorted(filtered_folders)
    except Exception as e:
        print(f'Error getting managed folders in {project_key}: {e}')
        return None
    
def get_dataset_sources(dataset_name: str, project_key: str) -> list[tuple[str, str]]:
    """
    Get source dataset(s) for a dataset.
    Sources mean first input datasets in project to specified dataset.
    
    Parameters
    ----------
    dataset_name : str
        Dataset name.
    project_key : str
        Project key.
    
    Returns
    -------
    list of tuples:
        Project key, Dataset name
    
    """
    
    def _build_graph_from_lineage(lineage):
        # Create an empty graph
        graph = nx.DiGraph()
        
        # Add edges
        for entry in lineage:
            graph.add_edge(entry['inputDataset'], entry['outputDataset'])
            
        return graph
    
    def _find_column_sources(graph, dataset_name):
        # Find all nodes (datasets) that have a path to the target node (dataset)
        ancestors = nx.ancestors(graph, dataset_name)
        
        # Find sources
        # NOTE: A source is an ancestor with no incoming edges (in_degree == 0)
        # NOTE: A source should also be connected to another node (out_degree > 0)
        sources = [
            node for node in ancestors
            if (graph.in_degree(node) == 0) and (graph.out_degree(node) > 0)
        ]
        
        return sources
    
    sources = []
    
    try:
        client = dataiku.api_client()
        project = client.get_project(project_key)
        dataset = project.get_dataset(dataset_name)
        
        dataset_info = dataset.get_info().info['dataset']
        column_names = [c['name'] for c in dataset_info['schema']['columns']]

        for c in column_names:
            lineage = dataset.get_column_lineage(c)
            
            if lineage:
                graph = _build_graph_from_lineage(lineage)
                sources.extend(_find_column_sources(graph, f'{project_key}.{dataset_name}'))

        return sorted(list(set([tuple(s.split('.')) for s in sources])))
    except Exception as e:
        print(f'Error getting source dataset(s) for {dataset_name}: {e}')
        return None
    
def get_dataset_metadata(dataset_name: str, project_key: str) -> dict[str, Any]:
    """
    Return dataset metadata.
    
    Parameters
    ----------
    dataset_name : str
        Dataset name.
    project_key : str
        Project key.
    
    Returns
    -------
    dict with keys:
        name, project_key, project_name,
        type, connection,
        short_description, description, columns
    """

    metadata = {
        'name': dataset_name,
        'project_key': project_key,
        'project_name': None,
        'type': None,
        'connection': None,
        'short_description': None,
        'description': None,
        'columns': []
    }

    try:
        client = dataiku.api_client()
        project = client.get_project(project_key)
        dataset = project.get_dataset(dataset_name)
        
        dataset_info = dataset.get_info().info['dataset']

        metadata['name'] = dataset_info['name']
        metadata['project_key'] = dataset_info['projectKey']
        metadata['project_name'] = project.get_metadata()['label']
        metadata['type'] = dataset_info['type']
        metadata['connection'] = dataset_info['params']['connection']
        metadata['short_description'] = dataset_info.get('shortDesc', 'No description provided.').strip()
        metadata['description'] = dataset_info.get('description', 'No description provided.').strip()
        metadata['columns'] = [{'name': c['name'], 'type': c['type'],  'description': c.get('comment', '')} for c in dataset_info['schema']['columns']]

        return metadata
    except Exception as e:
        print(f'Error getting metadata for {dataset_name}: {e}')
        return None
        
def get_managed_folder_metadata(folder_id: str, project_key: str) -> dict[str, Any]:
    """
    Return managed folder metadata.
    
    Parameters
    ----------
    folder_name : str
        Dataset name.
    project_key : str
        Project key.
    
    Returns
    -------
    dict with keys:
        name, type, connection,
        short_description, description
    """

    metadata = {
        'id': folder_id,
        'name': None,
        'type': None,
        'connection': None,
        'short_description': None,
        'description': None
    }

    try:
        client = dataiku.api_client()
        project = client.get_project(project_key)
        folder = project.get_managed_folder(folder_id)
        folder_settings = folder.get_settings().settings

        metadata['name'] = folder_settings['name']
        metadata['type'] = folder_settings['type']
        metadata['connection'] = folder_settings['params']['connection']
        metadata['short_description'] = folder_settings.get('shortDesc', 'No description provided.').strip()
        metadata['description'] = folder_settings.get('description', 'No description provided.').strip()

        return metadata
    except Exception as e:
        print(f'Error getting metadata for {folder_id}: {e}')
        return None
