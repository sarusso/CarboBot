from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

import logging
logger = logging.getLogger('uvicorn') # TODO: meh...

class ElasticFood(Elasticsearch):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_index_name = "food_index"

    def init_index(self, index_name=None):
        self.create_index(self.default_index_name if not index_name else index_name)

    def reset_index(self, index_name=None):
        if self.indices.exists(index=self.default_index_name if not index_name else index_name):
            self.indices.delete(index=self.default_index_name if not index_name else index_name)
        self.create_index(self.default_index_name if not index_name else index_name)

    def delete_index(self, index_name=None):
        self.indices.delete(index=self.default_index_name if not index_name else index_name)

    def create_index(self, index_name=None):
        index_name = self.default_index_name if not index_name else index_name
        try:
            if not self.indices.exists(index=self.default_index_name if not index_name else index_name):
                # Define the index mapping
                mapping = {
                    "settings": {"number_of_shards": 1, "number_of_replicas": 1},
                    "mappings": {
                        "properties": {
                            "uuid": {"type": "keyword"},
                            "description": {"type": "text"},
                            "ingredients": {"type": "keyword"},
                        }
                    },
                }
                # Create the index with the mapping
                self.indices.create(index=index_name, body=mapping)
                print(f"Index '{index_name}' created.")
            else:
                print(f"Index '{index_name}' already exists.")
        except NotFoundError as e:
            print(f"Error checking/creating index: {e}")

    def add_item(self, item, index_name=None):
        return self.index(index=self.default_index_name if not index_name else index_name, id=str(item["uuid"]), body=item)

    def delete_item(self, uuid, index_name=None):
        return self.delete(index=self.default_index_name if not index_name else index_name, id=uuid)

    def query(self, q, index_name=None):
        #search_query = {"query": {"fuzzy": {"description": q}}}
        search_query = {
                          "query": {
                            "multi_match": {
                              "query": q,
                              "fields": ["description"],
                              "fuzziness": "AUTO",
                              "operator": "and"
                            }
                          }
                        }
        index_name = self.default_index_name if not index_name else index_name
        logger.debug('Searching elastic for "%s" on "%s"', q, index_name )
        results = self.search(index=index_name, body=search_query)
        logger.debug('Got elastic results: "%s"', results)
        return results


es = ElasticFood("http://elastic:9200")
