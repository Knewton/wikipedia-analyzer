#!/usr/bin/env python
"""
This program reads in a list of tuples with counts and a text string for a wikipedia name
It looks up the page and scores it, based on the list of tuples
"""
import sys
import wikipedia

def main():
    filename = sys.argv[1]
    f = open(filename, 'r')
    while True:
        page = f.readline()
        if not page: break  # EOF
        page = page.rstrip()
        try:
            links = wikipedia.WikipediaPage(page).links
        except wikipedia.exceptions.DisambiguationError as e:
            print e.options
            continue
        print links
    f.close

if __name__ == '__main__':
    main()
