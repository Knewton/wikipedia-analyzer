#!/usr/bin/env python
"""
This program reads in a page and splits it into tuples - a paragraph at a time
"""
import sys

def main():
    minsize = int(sys.argv[1])
    maxsize = int(sys.argv[2])
    filename = sys.argv[3]
    f = open(filename, 'r')
    while True:
        line = f.readline()
        if not line: break  # EOF
        line = line.strip()
        words = line.split(' ')
        # tvdbg print words
        # tvdbg print len(words)
        for i in range(minsize, maxsize + 1):
            for j in range(0, len(words) - i + 1):
                ntup = ""
                for k in range(0, i):
                    ntup = ntup + words[j + k] + " "
                print ntup
    f.close

if __name__ == '__main__':
    main()
