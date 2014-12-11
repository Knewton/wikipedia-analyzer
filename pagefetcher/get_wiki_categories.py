import click
import re
import wikipedia


FIRST_PASS_RESULT_COUNT = 5
INTERNAL_KEYWORDS = ['Articles', 'articles', '-language sources', 'mdy date',
                     'move-protected', 'semi-protected', 'Wikidata', 'Wikipedia']

@click.command()
@click.option('--concept_path', prompt='Pipe-separated concept path',
              help='Knewton ontology concept path.')
def get_categories(concept_path):
    keywords = concept_path.split('|')
    matches = wikipedia.search(keywords[-1], results=FIRST_PASS_RESULT_COUNT,
                               suggestion=False)

    categories = {}
    category_relevance_score = {}

    for match in matches:
        page = wikipedia.page(match)
        categories[page.title] = [category for category in page.categories
            if not _has_substring_from_list(category, INTERNAL_KEYWORDS)]
        category_relevance_score[page.title] = _get_category_relevance_score(
            categories[page.title], concept_path)

    relevant_category_keys = sorted(categories, key=category_relevance_score.get,
                                    reverse=True)

    categories_found = False
    if len(relevant_category_keys):
        category_path = categories[relevant_category_keys[0]]
        if len(category_path):
            categories_found = True
            click.echo('%s: %s' % (relevant_category_keys[0], '|'.join(category_path)))

    if not categories_found:
        click.echo('No matching category found')


def _has_substring_from_list(word, wordlist):
    for w in wordlist:
        if w in word:
            return True
    return False


def _get_category_relevance_score(category_path, query):
    wiki_words = set()
    for item in category_path:
        wiki_words.update(re.split(re.compile('\ '), item))
    query_words = set(re.split(re.compile('\||\ '), query))
    return len(wiki_words.intersection(query_words))


if __name__ == '__main__':
    get_categories()
