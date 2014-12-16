#!usr/bin/python

from datastore.topic_match_store import TopicMatchStore

if __name__ == "__main__":
    store = TopicMatchStore(":memory:")
    store.add_or_update_match("algebra", "1", "http://www.wikipedia.com/algebra", 1.0)
    store.add_or_update_match("algebra", "2", "http://www.wikipedia.com/algebra2", 0.9)
    store.add_or_update_match("algebra", "3", "http://www.wikipedia.com/algebra3", 0.8)
    assert(0.8 == store.get_confidence("algebra", "3", "http://www.wikipedia.com/algebra3"))
    store.add_or_update_match("algebra", "3", "http://www.wikipedia.com/algebra3", 0.2)
    assert(0.2 == store.get_confidence("algebra", "3", "http://www.wikipedia.com/algebra3"))
    matches = list(store.get_matches_with_confidence("algebra", 0.5))
    assert(len(matches) == 2)
    assert(matches[0] == ("1", "http://www.wikipedia.com/algebra", 1.0))
    assert(matches[1] == ("2", "http://www.wikipedia.com/algebra2", 0.9))
    store.remove_match("algebra", "1", "http://www.wikipedia.com/algebra")
    try:
        store.get_confidence("algebra", "1", "http://www.wikipedia.com/algebra")
        assert(False)
    except ValueError:
        pass
    store.close()