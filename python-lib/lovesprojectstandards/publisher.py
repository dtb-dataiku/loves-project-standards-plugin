def _get_or_create_parent_article(wiki, article_name='Project Documentation', content=None):
    '''Get or create a parent article in a wiki.'''

    articles = wiki.list_articles()

    # Search for existing parent article
    for article in articles:
        name = article.get_data().article_data['article']['name']
        if name == article_name:
            return article.article_id

    # Create parent article if missing
    article = wiki.create_article(article_name, content=content)

    return article.article_id

def _find_article_id_by_name(wiki, article_name):
    '''Find article ID by article name.'''
    
    for article in wiki.list_articles():
        name = article.get_data().article_data['article']['name']
        if name == article_name:
            return article.article_id
    return None

def publish_to_dataiku_wiki(wiki, article_name, article_content, parent_name=None, parent_content=None):
    '''Publish article to a Dataiku project wiki.'''

    try:
        parent_id = _get_or_create_parent_article(wiki, article_name=parent_name, content=parent_content)
        article_id = _find_article_id_by_name(wiki, article_name)

        if article_id:
            print(f'Delete existing article: {article_name}')
            article = wiki.get_article(article_id)
            article.delete()

        print(f'Create new article: {article_name}')
        article = wiki.create_article(
            article_name,
            parent_id=parent_id,
            content=article_content
        )
    except Exception as e:
        print(f'Error publishing {article_name} in wiki: {e}')
