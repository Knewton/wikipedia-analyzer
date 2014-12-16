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
3. We collect the links from pages determined to be most relevance by their
wiki-category classification. We look at the number of occurences of each link
among the analyzed search query result, and output the ones with the highest
score as the most relevant for the given Knewton query.
"""

import click
import os
import re
import wikipedia

from collections import defaultdict
from wikipedia.exceptions import DisambiguationError
from wikipedia.exceptions import PageError

from datastore.topic_match_store import TopicMatchStore

SQLITE_FILE = "data/topic_match_store.db"
# The number of pages downloaded for the purpose of category analysis
FIRST_PASS_RESULT_COUNT = 20
# The number of pages considered for the best category result output
BEST_MATCH_COUNT = 5
# Keywords commonly occurring only in Wikipedia internal and meta categories,
# i.e. "Articles with dead links", "Topic on ..."
INTERNAL_CATEGORY_KEYWORDS = set(['articles', 'category template', 'chapter', 'commons', 'cs1', 'CS1', 'dmy', 'error',
                                  '-language sources', 'mdy', 'move-protected', 'outlines', 'pages', 'semi-protected',
                                  'stubs', 'topics', 'wikidata', 'wikipedia'])
# References and such
META_LINK_KEYWORDS = ['Digital object identifier', 'International Standard Book Number', 'JSTOR', 'Springer', 'ArXiv']
# Word matches exclude words of length shorter than this (common words like
# 'of', 'the' etc.
MATCHWORD_LENGTH_THRESHOLD = 4
# In some cases, the most specific taxon (deepest in the hierarchy) has a fairly general name (e.g. Series).
# If the title of the topic deepest in the tree is short, it's more likely to be not very specific. We then
# try to find the relevant topics based on taxons on the higher taxonomy levels but calculate but consider
# their relevances with lower weights
MATCH_SET_WEIGHTS = [1, 0.5]
# When evaluating a linked page relevance across a set of pages, the score the page is assigned is based on
# the number of occurrences (as a link), and the referencing page relevance.
CONFIDENCE_THRESHOLD = 0.7


# Cache wiki page when retrieving it. It's a slow call.
page_cache = {}
topic_match_store = TopicMatchStore(SQLITE_FILE)


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
    """
    For a given Knewton taxonomy path/concept description, analyze wiki pages that are among
    the most relevant search results, get a couple of those, refine the analysis by analyzing
    their assigned categories, and referenced links, then return what seem to be relevant matching
    wiki categories, and relevant webpage urls.
    :param knewton_path: Knewton taxonomy path/concept description/a file for a batch of those
    :param analyzed_query_count: Analyze this many best-match search results for the Knewton query.
    :param best_match_query_count: Order the returned queries by their assigned categories (in this
    script, this is based on matching-word count). Claim those to be the best-fit categories. Further
    analyze links referenced from these pages.
    :param output_file: If specified, the reports are written into text-files with this prefix.
    :return:
    """
    # Check if knewton_path defines the file, if so, parse the file, if not, consider it a single
    # query case.
    if os.path.exists(knewton_path):
        knewton_paths = [line.strip() for line in open(knewton_path, 'r').readlines()]
    else:
        knewton_paths = [knewton_path]

    # Dictionary to store matching categories
    matching_category_output = {}
    # Dictionary to store relevant links
    relevant_links_output = {}

    for path in knewton_paths:
        keywords = path.split('|')
        # If knewton_path defines a taxon, the last element on the patch (the most specific taxon)
        # is supposedly most accurate to use for the search, while being not overly restrictive
        # (which the whole path with its encoding could be)
        match_sets = [wikipedia.search(keywords[-1], results=analyzed_query_count,
                                       suggestion=False)]
        # If the deepest taxons is too short (e.g. "series"), it may be too ambiguous, and to get
        # accurate results, we may need to refine the context. Try to search by the last-but-one
        # element on the path, which is less-specific category and thus considered with lower weight
        if len(keywords) > 1 and len(keywords[-1].split()) == 1:
            match_sets.append(wikipedia.search(keywords[-2], results=analyzed_query_count, suggestion=False))

        categories = {}
        category_relevance_score = defaultdict(int)
        link_map = {}

        match_index = 0

        # For each search query, we get a set of best-match results. For each of these sets, let analyze
        # the pages further.
        for matches in match_sets:
            # Returned search results are presumably returned sorted by relevance (however, we're not
            # sure of the context). Give this order some weight by using the result_score (decreasing from
            # len(matches) -> 1) as a multiplicative factor when calculating the category relevance score.
            result_score = len(matches)
            for match in matches:
                try:
                    page = wikipedia.page(match)
                    page_cache[page.title] = page
                except DisambiguationError:
                    continue
                except PageError:
                    continue
                # Tokenize the page title
                page_title_words = [word.lower() for word in page.title.split()]
                # Get cateogories for each page but skip the internal/meta wiki categories
                categories[page.title] = [category for category in page.categories
                    if not _has_substring_from_set(category, INTERNAL_CATEGORY_KEYWORDS)]
                # Save page links
                link_map[page.title] = page.links
                # Assign relevance score to the categories assigned to this page, based on word-match
                # between the words occurring in the page title + wiki category path vs Knewton path
                # If the page was obtained as a search result for a higher-level category, consider
                # it with a lower weight
                category_relevance_score[page.title] += result_score * _get_category_relevance_score(
                    categories[page.title], page_title_words, path, MATCH_SET_WEIGHTS[match_index])

                result_score -= 1
            match_index += 1

        # Sort page-titles (keys of "categories" map) by their assigned score
        relevant_category_keys = sorted(categories, key=category_relevance_score.get,
                                        reverse=True)

        categories_found = False
        best_match_count_current = 0

        matching_category_output[path] = []
        click.echo('Categories found for query: %s' % path)

        links = set()
        linkset_list = []
        weight_list = []

        for page_title in relevant_category_keys:
            # Analyze best_match_count page_titles to gather relevant links.
            # Gather links from the page, and add the page itself, build a set of these tokens
            # for each page analyzed.
            category_path = categories[page_title]
            links.update(link_map[page_title])
            links.add(page_title)
            linkset_list.append(link_map[page_title] + [page_title])
            weight_list.append(category_relevance_score[page_title])

            # Output formatting
            if len(category_path):
                categories_found = True
                message = '\t%s, %.2f: %s' % (page_title, category_relevance_score[page_title], '|'.join(category_path))
                matching_category_output[path].append(message)
                click.echo(message)
                best_match_count_current += 1
                if best_match_count_current >= best_match_query_count:
                    break

        if not categories_found:
            message = '\tNo matching category found for query \"%s\".' % path
            matching_category_output[path].append(message)
            click.echo(message)

        # Get links from the analyzed pages, evaluated as relevant.
        relevant_links = _get_relevant_links(links, linkset_list, weight_list)
        relevant_link_data = _map_titles_to_urls_ids(relevant_links)

        message = path + ':\n'
        for link in relevant_link_data:
            data = relevant_link_data[link]
            for taxon in keywords:
                topic_match_store.add_or_update_match(taxon, str(data.pageid), data.url, 0)
            try:
                message += '\t%s: %s\n' % (data.url, data.pageid)
            except UnicodeDecodeError:
                continue

        relevant_links_output[path] = message
        click.echo(message)

    if len(output_file):
        with open(output_file + '_categories.txt', 'w') as output:
            for key in matching_category_output:
                try:
                    output.write('Categories found for query: %s\n' % key.encode('utf8'))
                    for item in matching_category_output[key]:
                        output.write(item.encode('utf8') + '\n')
                except UnicodeDecodeError:
                    pass
        with open(output_file + '_relevant_links.txt', 'w') as output:
            for key in relevant_links_output:
                try:
                    output.write(relevant_links_output[key].encode('utf8') + '\n')
                except UnicodeDecodeError:
                    pass


def _has_substring_from_set(word, wordset):
    """
    Checks if a given string contains a substring from a given set.
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


def _get_category_relevance_score(category_path, page_title_words, query, weight):
    """
    Try to score category relevance according to the number of words above certain
    length it shares with Knewton taxonomy path/concept description.
    :param category_path: Wikipedia category path
    :param page_title_words: Words in the title of the page tagged by these categories
    :param query: Submitted query (taxonomy path or concept description)
    :param weight: If relevance score is computed for a higher-level
    category, it's less important (weight is the multiplication factor to
    achieve that
    :return: The number of words matching between the Wikipedia category
    path and the submitted query
    """
    wiki_words = set(page_title_words)
    for item in category_path:
        wiki_words.update([word.lower() for word in re.split(re.compile('\ '), item)])
    query_words = set([word.lower() for word in re.split(re.compile('\||\ '), query)])
    return weight * len([word for word in wiki_words.intersection(query_words)
        if len(word) >= MATCHWORD_LENGTH_THRESHOLD])


def _capitalize_internal_keywords(wordset):
    capitalized = [word.title() for word in wordset]
    wordset.update(capitalized)


def _get_relevant_links(all_links, link_sets, weights):
    """
    Get links that are significant for a set of link-sets gathered
    from several wiki pages.
    :param all_links: set of links to filter
    :param link_sets: links clustered in sets common to a single article
    :param weights: weights assigned to these sets of links, based on
    category relevance
    :return: links that get at least half of the maximum score, where the
    max score is the sum of max(1, set_weight), computed over all set_weights
    """
    relevant = []
    max_score = 0

    # Compute a score for each link referenced from some of the analyzed
    # pages + the analyze page titles themselves. This is done as follows:
    # For each reachable page (within one-hop from the starting set), start with 0.
    # If a page has relevance_score r >= 1 based on category word_match, add r to the
    # scores of all links, and the page itself. If it has score <1 (in the current model,
    # ==0), add 1 to each link/the page itsef - This is because even though there's no
    # word match between the categories assigned and Knewton query, the page was returned
    # as a search result for some reason.
    # Obviously, the maximum score is achieved for a page referenced from or identical to
    # each from the analyzed pages.
    # Consider a link relevant if it has at least 1/2 of the maximum score.
    for weight in weights:
        max_score += max(1, weight)

    for link in all_links:
        index = 0
        score = 0
        for link_set in link_sets:
            if link in link_set:
                score += max(weights[index], 1)
            index += 1
        if score > max_score * CONFIDENCE_THRESHOLD and not _has_substring_from_set(link, META_LINK_KEYWORDS):
            relevant.append(link)

    relevant.sort(reverse=True)
    return relevant


def _map_titles_to_urls_ids(titles):
    """
    Convert a set of wiki page titles into the corresponding (url, id) pairs.
    """
    link_data = {}
    for title in titles:
        if title in page_cache:
            page = page_cache[title]
        else:
            try:
                page = wikipedia.page(title)
                page_cache[title] = page
            except DisambiguationError:
                continue
            except PageError:
                continue
        link_data[title] = LinkData(page.url, page.pageid)
    return link_data


class LinkData:
    def __init__(self, url, pageid):
        self.url = url
        self.pageid = pageid


if __name__ == '__main__':
    _capitalize_internal_keywords(INTERNAL_CATEGORY_KEYWORDS)
    get_categories()
