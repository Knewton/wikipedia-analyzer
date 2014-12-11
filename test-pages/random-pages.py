#!/usr/bin/env python
"""
This program selects 175 random pages
"""
import wikipedia

def main():
    for i in range(1, 225):
        print wikipedia.random(1).encode('ascii', 'xmlcharrefreplace')

if __name__ == '__main__':
    main()
