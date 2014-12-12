#!/usr/bin/env python
"""
This program counts tuples in a page of text
NOTE: the input page of tuples is in the form of a count already:
### = text
"""
import sys

def get_tuples(filename):
    # read the tuple file
    # initialize pairs of tuple = 0
    t = open(filename, 'r')
    tupledict = {}
    while True:
        line = t.readline()
        if not line: break  # EOF
        pair = line.split('=')
        tupledict[pair[1].rstrip()] = 0
    t.close
    return (tupledict)

def main():
    tupledict = get_tuples(sys.argv[1])
    filename = sys.argv[2]
    f = open(filename, 'r')
    filename = sys.argv[3]
    o = open(filename, 'w')
    while True:
        line = f.readline()
        if not line: break  # EOF
        line = line.strip()
        # words = line.split(' ')
        for tupletext in tupledict:
            if tupletext in line:
                tupledict[tupletext] = tupledict[tupletext] + 1
    for tupletext in tupledict:
        result =  "%d = %s" % (tupledict[tupletext], tupletext)
        o.write(result + "\n")
        print result
    f.close
    o.close

if __name__ == '__main__':
    main()
