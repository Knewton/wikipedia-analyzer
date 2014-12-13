from xml.etree import ElementTree

def xml_convert(path):
    with open(path , 'rt') as  f:
        tree = ElementTree.parse(f)
    #root = tree.getroot()
    Dlist = []
    for page in tree.findall('page'):
        title = page.find('title')
        id = page.find('id')
        rev = page.find('revision')
        text =  rev.find('text')
        tup = (id.text , title.text , text.text)
        Dlist.append(tup)
    return Dlist







