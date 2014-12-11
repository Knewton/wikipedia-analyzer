
class Part:
    """Represents a piece of content."""

    def __init__(self, id, header):
        """Part initializer. Other attributes may be set after construction.
        :param str id:
        :param str header:
        """
        self.id = id
        self.parentId = None
        self.header = header
        self.categories = []