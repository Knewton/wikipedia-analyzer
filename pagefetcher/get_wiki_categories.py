"""
Goal: For a given knewton taxonomy path/concept, or a file for a batch of those,
output the set of wikipedia categories that are most likely to contain useful
pages from the given ontology path.

Outline of the algorithm:
1. For a given taxonomy path/concept, e.g. taxonomy
"Algebra & Algebra 2|Matrix Algebra|Properties of Matrices",
we execute a search query/queries to wikipedia.
2. We collect the categories the most relevant returned results
belong to, and then compute the matching-word count with the submitted
knewton taxonomy path. Based on this count, we assign the relevance score
to the returned results (pages), and output the best matches'
assigned categories as the most promising categories to search for.
"""

import click
import os
import re
import wikipedia

from wikipedia.exceptions import DisambiguationError
from wikipedia.exceptions import PageError


# The number of pages downloaded for the purpose of category analysis
FIRST_PASS_RESULT_COUNT = 20
# The number of pages considered for the best category result output
BEST_MATCH_COUNT = 5
# Keywords commonly occurring only in Wikipedia internal and meta categories,
# i.e. "Articles with dead links", "Topic on ..."
INTERNAL_KEYWORDS = set(['articles', 'category template', 'chapter', 'commons', 'cs1', 'CS1', 'dmy', 'error',
                         '-language sources', 'mdy', 'move-protected', 'outlines', 'pages', 'semi-protected',
                         'stubs', 'topics', 'wikidata', 'wikipedia'])
# Word matches exclude words of length shorter than this (common words like
# 'of', 'the' etc.
MATCHWORD_LENGTH_THRESHOLD = 4
# In some cases, the most specific taxon (deepest in the hierarchy) has a fairly general name (e.g. Series).
# If the title of the topic deepest in the tree is short, it's more likely to be not very specific. We then
# try to find the relevant topics based on taxons on the higher taxonomy levels but calculate but consider
# their relevances with lower weights
MATCH_SET_WEIGHTS = [1, 0.2]

@click.command()
@click.option('--knewton_path', prompt='Pipe-separated taxonomy path/concept or the file name for batch load',
              help='Knewton taxonomy path, concept description, or the file with one of those in each line for batch load.')
@click.option('--analyzed_query_count', default=FIRST_PASS_RESULT_COUNT,
              prompt='Search query count to analyze',
              help='This many search results will be analyzed.')
@click.option('--best_match_query_count', default=BEST_MATCH_COUNT,
              prompt='Best-match page count to consider in the input',
              help='This many best-match pages will be considered for the output')
@click.option('--output_file', default="",
              prompt='Output filename', help='Output filename.')
def get_categories(knewton_path, analyzed_query_count, best_match_query_count, output_file):
    if os.path.exists(knewton_path):
        knewton_paths = [line.strip() for line in open(knewton_path, 'r').readlines()]
    else:
        knewton_paths = [knewton_path]

    matching_category_output = {}

    for path in knewton_paths:
        keywords = path.split('|')
        match_sets = [wikipedia.search(keywords[-1], results=analyzed_query_count,
                                       suggestion=False)]
        if len(keywords) > 1 and len(keywords[-2].split()) > len(keywords[-1].split()):
            match_sets.append(wikipedia.search(keywords[-2], results=analyzed_query_count, suggestion=False))

        categories = {}
        category_relevance_score = {}

        match_index = 0
        for matches in match_sets:
            for match in matches:
                try:
                    page = wikipedia.page(match)
                except DisambiguationError:
                    continue
                except PageError:
                    continue
                categories[page.title] = [category for category in page.categories
                    if not _has_substring_from_set(category, INTERNAL_KEYWORDS)]
                category_relevance_score[page.title] = _get_category_relevance_score(
                    categories[page.title], path, MATCH_SET_WEIGHTS[match_index])
            match_index += 1

        relevant_category_keys = sorted(categories, key=category_relevance_score.get,
                                        reverse=True)

        categories_found = False
        best_match_count_current = 0

        matching_category_output[path] = []
        click.echo('Categories found for query: %s' % path)
        for page_title in relevant_category_keys:
            category_path = categories[page_title]
            if len(category_path):
                categories_found = True
                message = '\t%s: %s' % (page_title, '|'.join(category_path))
                matching_category_output[path].append(message)
                click.echo(message)
                best_match_count_current += 1
                if best_match_count_current >= best_match_query_count:
                    break

        if not categories_found:
            message = '\tNo matching category found for query \"%s\".' % path
            matching_category_output[path].append(message)
            click.echo(message)

    if len(output_file):
        with open(output_file, 'w') as output:
            for key in matching_category_output:
                output.write('Categories found for query: %s\n' % key)
                for item in matching_category_output[key]:
                    output.write(item.encode('utf8') + '\n')


def _has_substring_from_set(word, wordset):
    """
    :param word: Word to examine
    :param wordset: Set of words we are interested if they
    occur in the given word
    :return: True if the input word contains some of the words
    from the wordset
    """
    for w in wordset:
        if w in word:
            return True
    return False


def _get_category_relevance_score(category_path, query, weight):
    """
    :param category_path: Wikipedia category path
    :param query: Submitted query (taxonomy path or concept description)
    :param weight: If relevance score is computed for a higher-level
    category, it's less important (weight is the multiplication factor to
    achieve that
    :return: The number of words matching between the Wikipedia category
    path and the submitted query
    """
    wiki_words = set()
    for item in category_path:
        wiki_words.update(re.split(re.compile('\ '), item))
    query_words = set(re.split(re.compile('\||\ '), query))
    return weight * len([word for word in wiki_words.intersection(query_words)
        if len(word) >= MATCHWORD_LENGTH_THRESHOLD])


def _capitalize_internal_keywords(wordset):
    capitalized = [word.title() for word in wordset]
    wordset.update(capitalized)

if __name__ == '__main__':
    _capitalize_internal_keywords(INTERNAL_KEYWORDS)
    get_categories()