import math
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)


class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):
    """
    Write your own logic by modifying the body of the run() method.

    .. important::
        This class will be automatically instantiated by DSS, do not add a custom constructor on it.

    The superclass is setting those fields for you:
    self.config: the dict of the configuration of the object
    self.plugin_config: the dict of the plugin settings
    self.project: the current `DSSProject` to use in your check spec
    """

    def run(self):
        """
        Run the check

        :returns: the run result.
            Use `ProjectStandardsCheckRunResult.success(message)` or `ProjectStandardsCheckRunResult.failure(severity, message)` depending on the result.
            Use `ProjectStandardsCheckRunResult.not_applicable(message)` if the check is not applicable to the project.
            Use `ProjectStandardsCheckRunResult.error(message)` if you want to mark the check as an error. You can also raise an Exception.
        """

        required_article_names = self.config.get('required_article_names')  # use self.config to get your check config values
        
        project = self.project  # use self.project to access the current project
        wiki = project.get_wiki()
        article_names = [article.get_data().get_name() for article in wiki.list_articles()]
        
        missing_article_names = []
        for article_name in required_article_names:
            if article_name not in article_names:
                missing_article_names.append(article_name)
        
        if len(missing_article_names) == 0:
            return ProjectStandardsCheckRunResult.success('All required wiki articles found.')
        else:
            pct_missing = len(missing_article_names) / len(required_article_names)
            severity = math.ceil(pct_missing * 5)
            
            missing_list = ', '.join([f"'{n}'" for n in missing_article_names])
            return ProjectStandardsCheckRunResult.failure(severity, f"Missing wiki articles: {missing_list}")
