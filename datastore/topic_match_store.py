import sqlite3


class TopicMatchStore:
    """A helper for persisting matching topic/url pairs to SqLite"""

    def __init__(self, sqlite_file):
        """
        Initializer.
        :param string sqlite_file: Path to the file to use as the sqlite store.
        """
        self._db = sqlite3.connect(sqlite_file)

    def add_or_update_match(self, topic, url, confidence):
        """
        Add a url for a page matching a particular topic, or update
        the confidence of an existing match.
        :param str topic: A string uniquely identifying a topic
        :param str url: The url of the matching page
        :param float confidence: A float between 0 and 1, indicating
        the confidence in the match, 1 being more confident.
        :return: None
        """
        pass

    def remove_match(self, topic, url):
        """
        Remove a match.
         :param str topic: A string uniquely identifying a topic
        :param str url: The url to remove
        :return:
        """
        pass

    def get_matches(self, topic, threshold=0):
        """
        Get the urls matching a topic.
        :param str topic: The topic to get matching urls for
        :param float threshold: The threshold confidence level for
        returned matches; no match with confidence under the specified
        amount will be returned.
        :return: A list of matching urls, sorted in decreasing order
        of match confidence.
        """
        pass

    def get_matches_with_confidence(self, topic, threshold=0):
        """
        Get the urls matching a topic.
        :param str topic: The topic to get matching urls for
        :param float threshold: The threshold confidence level for
        returned matches; no match with confidence under the specified
        amount will be returned.
        :return: A list (matching url, confidence) tuples, sorted in
        decreasing order of match confidence.
        """
        pass