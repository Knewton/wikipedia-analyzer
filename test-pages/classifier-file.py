#!/usr/bin/env python
"""
This program reads in a list of tuples with counts and a text string for a wikipedia name
It looks up the page and scores it, based on the list of tuples
"""
import sys
import wikipedia

def get_tuples(filename):
    # read the tuple file
    # store pairs of tuple = count
    t = open(filename, 'r')
    tupledict = {}
    tupletotal = 0.0
    while True:
        line = t.readline()
        if not line: break  # EOF
        pair = line.split('=')
        count = float(pair[0].rstrip())
        tupledict[pair[1].rstrip()] = count
        tupletotal = tupletotal + count
    t.close
    return (tupledict, tupletotal)

def main():
    tupledict, tupletotal = get_tuples(sys.argv[1])
    filename = sys.argv[2]
    f = open(filename, 'r')
    filename = sys.argv[3]
    o = open(filename, 'w')
    while True:
        page = f.readline()
        if not page: break  # EOF
        page = page.rstrip()
        try:
            text = wikipedia.WikipediaPage(page).content.encode('ascii', 'xmlcharrefreplace')
        except wikipedia.exceptions.DisambiguationError as e:
            print e.options
            continue
        score = 0.0
        for tupletext in tupledict:
            if tupletext in text:
                score = score + tupledict[tupletext]
        score = (score / tupletotal)
        result =  "%f %s" % (score, page)
        o.write(result + "\n")
        print result
    f.close
    o.close

if __name__ == '__main__':
    main()
