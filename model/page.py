from part import Part

class Page(Part):
    """Represents a wikipedia page."""

    def __init__(self, id, header, url):
        super(id, header)
        self.content = None
        self.summary = None
        self.links = []
        self.references = []
        self.url = url
        self.parts = []

