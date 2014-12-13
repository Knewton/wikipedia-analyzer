import os

import boto.dynamodb2
from boto.dynamodb2.table import Table


class ContentStore:
    """
    DynamoDb proxy for wikidata store, which contains page ids, titles, and contents.

    This class is designed to be used in a "with" block, as in
    with ContentStore() as store:
        ... statements using store ...

    You must have a configuration file in your home directory containing the AWS access key id
    and secret key for the IAM identity that has access to the database. This file must be named
    ".boto", and must contain a section of the form:

    [Credentials]
    aws_access_key_id = <access key id>
    aws_secret_access_key = <secret key id>
    """

    def add_page(self, pageId, pageTitle, pageText):
        """
        Adds a new page to the data store.

        New pages are batched and sent to DynamoDB 25 at a time. Clients may call flush() to
        cause all pending pages to be uploaded immediately.
        :param str pageId: The unique identifier of the page
        :param str pageTitle: The title of the page
        :param str pageText: The text contents of the page, in wiki markup format
        """
        self._batch_write.put_item(data={
            'pageId': pageId,
            'pageTitle': pageTitle,
            'pageText': pageText})

    def flush(self):
        """
        Ensure that all added pages are persisted to DynamoDB.
        """
        self._batch_write.flush()

    def get_content(self, pageId):
        """
        Retrieve the content of a page
        :param str pageId: The unique page identifier
        :return: The text content of a page in wiki markup format
        """
        item = self._table.get_item(pageId=pageId)
        return item['pageText']

    def get_title(self, pageId):
        """
        Get the title of a page
        :param str pageId: The unique page identifier
        :return: The title content of a page
        """
        item = self._table.get_item(pageId=pageId)
        return item['pageTitle']

    def __enter__(self):
        self._previous_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
        self._previous_secret_key = os.environ["AWS_SECRET_ACCESS_KEY"]
        del os.environ["AWS_ACCESS_KEY_ID"]
        del os.environ["AWS_SECRET_ACCESS_KEY"]
        connection = boto.dynamodb2.connect_to_region('us-east-1')
        self._table = Table('wikidata', connection=connection)
        self._batch_write = self._table.batch_write()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.environ["AWS_ACCESS_KEY_ID"] = self._previous_access_key_id
        os.environ["AWS_SECRET_ACCESS_KEY"] = self._previous_secret_key
        if self._batch_write.should_flush():
            self._batch_write.flush()

        # Cause the exception to be re-raised if one has occurred
        return exc_value is None


if __name__ == "__main__":

    with ContentStore() as store:
        store.add_page("testPageId1", "Test Title", "There once was a man from dakota, who tried to used dynamo db but failed." )
        store.flush()
        content = store.get_content("testPageId1")
        print content
