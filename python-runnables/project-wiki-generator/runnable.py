# This file is the actual code for the Python runnable project-wiki-generator
import dataiku
from dataiku.runnables import Runnable
from lovesprojectstandards import extractor, formatter, publisher


class MyRunnable(Runnable):
    """The base interface for a Python runnable"""

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        
    def get_progress_target(self):
        """
        If the runnable will return some progress info, have this function return a tuple of 
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return None

    def run(self, progress_callback):
        """
        Do stuff here. Can return a string or raise an exception.
        The progress_callback is a function expecting 1 value: current progress
        """
        
        # Get macro parameters
        use_status = self.config.get('use_status', False)
        status = self.config.get('status', '')
#         use_metadata = self.config.get('use_metadata', True)
#         use_default_tags = self.config.get('use_default_tags', True)
#         selected_tags = self.config.get('selected_tags', [])
#         overwrite = self.config.get('overwrite', True)
        
        # Get client, project, and wiki
        client = dataiku.api_client()
        project = client.get_default_project()
        project_key = project.project_key
        wiki = project.get_wiki()
        
        # Get wiki URL
        host_url = client.get_general_settings().get_raw()['studioExternalUrl']
        wiki_url = f"{host_url}/projects/{project_key}/wiki"

        # Set status
        if use_status and status:
            project_settings = project.get_settings()
            project_settings.settings['projectStatus'] = status
            project_settings.save()
        
        # Generate starter content for wiki
        source_datasets = extractor.list_project_datasets(tag_filter=['Tracking:Source'])
        source_folders = extractor.list_project_managed_folders(tag_filter=['Tracking:Source'])
        
        output_datasets = extractor.list_project_datasets(tag_filter=['Tracking:Deliverable'])
        output_folders = extractor.list_project_managed_folders(tag_filter=['Tracking:Deliverable'])
        
        required_articles = ['Description', 'Business Value', 'Stakeholders', 'Deliverables', 'Data Sources', 'Data Outputs']
        for article_name in required_articles:
            if article_name == 'Description':
                project_metadata = extractor.get_project_metadata()
                project_content = formatter.project_description_to_markdown(project_metadata)
                publisher.publish_to_dataiku_wiki(
                    wiki,
                    article_name,
                    project_content,
                    parent_name='Project Documentation',
                    parent_content='**Standard Project Documentation**'
                )
            elif article_name == 'Data Sources':
                publisher.publish_to_dataiku_wiki(
                    wiki,
                    article_name,
                    '**Listing of Data Source(s)**',
                    parent_name='Project Documentation',
                    parent_content='**Standard Project Documentation**'
                )
                
                for ds_pkey, ds_name in source_datasets:
                    ds_metadata = extractor.get_dataset_metadata(ds_name, ds_pkey)
                    ds_sources = extractor.get_dataset_sources(ds_name, ds_pkey)
                    ds_content = formatter.dataset_to_markdown(ds_metadata, dataset_sources=ds_sources)
                    publisher.publish_to_dataiku_wiki(
                        wiki,
                        ds_name,
                        ds_content,
                        parent_name=article_name
                    )
                    
                for mf_pkey, mf_id in source_folders:
                    mf_metadata = extractor.get_managed_folder_metadata(mf_id, mf_pkey)
                    mf_content = formatter.folder_to_markdown(mf_metadata)
                    publisher.publish_to_dataiku_wiki(
                        wiki,
                        mf_metadata['name'],
                        mf_content,
                        parent_name=article_name
                    )
            elif article_name == 'Data Outputs':
                publisher.publish_to_dataiku_wiki(
                    wiki,
                    article_name,
                    '**Listing of Data Output(s)**',
                    parent_name='Project Documentation',
                    parent_content='**Standard Project Documentation**'
                )
                
                for ds_pkey, ds_name in output_datasets:
                    ds_metadata = extractor.get_dataset_metadata(ds_name, ds_pkey)
                    ds_sources = extractor.get_dataset_sources(ds_name, ds_pkey)
                    ds_content = formatter.dataset_to_markdown(ds_metadata, dataset_sources=ds_sources)
                    publisher.publish_to_dataiku_wiki(
                        wiki,
                        ds_name,
                        ds_content,
                        parent_name=article_name
                    )
                    
                for mf_pkey, mf_id in output_folders:
                    mf_metadata = extractor.get_managed_folder_metadata(mf_id, mf_pkey)
                    mf_content = formatter.folder_to_markdown(mf_metadata)
                    publisher.publish_to_dataiku_wiki(
                        wiki,
                        mf_metadata['name'],
                        mf_content,
                        parent_name=article_name
                    )
            else:
                article_content = formatter.placeholder_to_markdown(article_name)
                publisher.publish_to_dataiku_wiki(
                    wiki,
                    article_name,
                    article_content,
                    parent_name='Project Documentation',
                    parent_content='**Standard Project Documentation**'
                )
                
        return wiki_url
