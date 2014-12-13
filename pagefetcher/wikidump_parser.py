from xml.etree import ElementTree

def parse(dumpfile):
    """
    Parse the xml in the specified dump file.

    This file is expected to conform to a particular
    schema, summarized below. Such files can be obtained from
    http://en.m.wikipedia.org/w/index.php?title=Special:Export&action=submit
    To simplify parsing, you must manually remove the namespaces attribute of the mediawiki
    element before using this function.

    <mediawiki>
      <siteinfo>
        ...
      </siteinfo>
      <page>
        <title>Page Title</title>
        <id>#########</id>
        ...
        <revision>
          ...
          <format>text/x-wiki</format>
          <text>
            Bla Bla Bla this is wiki markup text
          </text>
          ...
      <page>
      <page>
        ...
      </page>
      ...
    </mediawiki>

    :param path: Full path to the xml file
    :return: An iterable of 3-tuples in the format (str:pageId, str:pageTitle, str:pageText)
    """

    with open(dumpfile) as f:
        tree = ElementTree.parse(f)

    for page in tree.iterfind('page'):
        title = page.find('title')
        page_id = page.find('id')
        rev = page.find('revision')
        text = rev.find('text')
        tup = (page_id.text, title.text, text.text)
        yield tup

if __name__ == "__main__":
    pages = parse("/Users/alex.heitzmann/Downloads/Wikipedia-20141212192912.xml")
    print pages.next()





