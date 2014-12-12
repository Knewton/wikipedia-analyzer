import sqlite3
import uuid

class TopicMatchStore:
    """A helper for persisting matching topic/url pairs to SqLite"""
    _TABLE_NAME = "TopicMatches"
    _TOPIC_COL = "topic"
    _URL_COL = "url"
    _CONFIDENCE_COL = "confidence"

    def __init__(self, sqlite_file):
        """
        Initializer.
        :param string sqlite_file: Path to the file to use as the sqlite store.
        ':memory:' may be passed if an in-memory store is desired.
        """
        self._db = sqlite3.connect(sqlite_file)
        cursor = self._db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS {}
            (
                id TEXT PRIMARY KEY,
                {} TEXT,
                {} TEXT,
                {} REAL
            )
            '''.format(TopicMatchStore._TABLE_NAME,
                       TopicMatchStore._TOPIC_COL,
                       TopicMatchStore._URL_COL,
                       TopicMatchStore._CONFIDENCE_COL))
        self._db.commit()

    def _does_match_exist(self, topic, url):
        """
        :param str topic: A string uniquely identifying a topic
        :param str url: The potentially matching url
        :return bool: True if a the given topic has the given url as a match in the db.
        """
        cursor = self._db.cursor()
        cursor.execute("SELECT * FROM {} WHERE topic=? AND url=?"
                       .format(TopicMatchStore._TABLE_NAME), (topic, url))
        return cursor.fetchone() is not None

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
        cursor = self._db.cursor()
        if self._does_match_exist(topic, url):
            cursor.execute("UPDATE {} SET confidence=? WHERE topic=? AND url=?"
                           .format(TopicMatchStore._TABLE_NAME), (confidence, topic, url))
        else:
            id = str(uuid.uuid4())
            cursor.execute("INSERT INTO {} VALUES (?, ?, ?, ?)"
                           .format(TopicMatchStore._TABLE_NAME), (id, topic, url, confidence))
        self._db.commit()

    def remove_match(self, topic, url):
        """
        Remove a match.
         :param str topic: A string uniquely identifying a topic
        :param str url: The url to remove
        :return:
        """
        cursor = self._db.cursor()
        cursor.execute("DELETE FROM {} WHERE topic=? AND url=?"
                       .format(TopicMatchStore._TABLE_NAME), (topic, url))
        self._db.commit()

    def get_confidence(self, topic, url):
        """
        Get the confidence of a match.
        :param topic: The topic of the match
        :param url: The matching url
        :return float: The confidence of the match
        """
        cursor = self._db.cursor()
        cursor.execute("SELECT {} FROM {} WHERE topic=? AND url=?"
                       .format(TopicMatchStore._CONFIDENCE_COL, TopicMatchStore._TABLE_NAME),
                       (topic, url))
        confidence = cursor.fetchone()
        if confidence is None:
            raise ValueError("No match found for topic {} url {}".format(topic, url))
        return float(confidence[0])


    def get_matches(self, topic, threshold=0):
        """
        Get the urls matching a topic.
        :param str topic: The topic to get matching urls for
        :param float threshold: The threshold confidence level for
        returned matches; no match with confidence under the specified
        amount will be returned.
        :return: An iterable of matching urls, sorted in decreasing order
        of match confidence.
        """
        matches = self.get_matches_with_confidence(topic, threshold)
        return (match[0] for match in matches)

    def get_matches_with_confidence(self, topic, threshold=0):
        """
        Get the urls matching a topic.
        :param str topic: The topic to get matching urls for
        :param float threshold: The threshold confidence level for
        returned matches; no match with confidence under the specified
        amount will be returned.
        :return: An iterable over (matching url, confidence) tuples, sorted in
        decreasing order of match confidence.
        """
        cursor = self._db.cursor()
        return cursor.execute("SELECT {0},{1} FROM {2} WHERE {3}=? AND {1}>=? ORDER BY {1} DESC"
                       .format(TopicMatchStore._URL_COL,
                               TopicMatchStore._CONFIDENCE_COL,
                               TopicMatchStore._TABLE_NAME,
                               TopicMatchStore._TOPIC_COL),
                       (topic, threshold))

    def close(self):
        """Close connection to the db"""
        self._db.close()