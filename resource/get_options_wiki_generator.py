import dataiku


def do(payload, config, plugin_config, inputs):
    """Populate choices in the initial macro interface"""
    
    client = dataiku.api_client()
    
    parameter_name = payload.get('parameterName')
    
    # Set options for project status
    if parameter_name == 'status':
        general_settings = client.get_general_settings()
        
        statuses = [s['name'] for s in general_settings.settings['projectStatusList']]
        choices = [{'value': s, 'label': s} for s in statuses]
        
        return {'choices': choices}
    
    # Set options for selected tags
    elif parameter_name == 'selected_tags':
        project = client.get_default_project()
        datasets = project.list_datasets(as_type='objects', include_shared=True)
        
        available_tags = []
        for dataset in datasets:
            available_tags.extend(dataset.get_metadata().get('tags', []))
            
        available_tags = sorted(list(filter(lambda t: t, set(available_tags))))
        
        choices = [{'value': t, 'label': t} for t in available_tags]
        
        return {'choices': choices}
