from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

import logging
logger = logging.getLogger('uvicorn') # TODO: meh...

class ElasticFood(Elasticsearch):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init_index(self, index_name):
        self.create_index(index_name)

    def reset_index(self, index_name):
        if self.indices.exists(index=index_name):
            self.indices.delete(index=index_name)
        self.create_index(index_name)

    def delete_index(self, index_name):
        self.indices.delete(index=self.default_index_name if not index_name else index_name)

    def create_index(self, index_name):
        try:
            if not self.indices.exists(index=index_name):
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

    def add_item(self, item, index_name):
        logger.debug('ElasticFood: adding "{}" on index "{}"'.format(str(item["uuid"]), index_name))
        return self.index(index=index_name, id=str(item["uuid"]), body=item)

    def delete_item(self, uuid, index_name):
        logger.debug('ElasticFood: deleting "{}" on index "{}"'.format(uuid, index_name))
        return self.delete(index=index_name, id=uuid)

    def query(self, q, index_name):
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
        logger.debug('ElasticFood: searching for "{}" on index "{}"'.format(q, index_name))
        try:
            results = self.search(index=index_name, body=search_query)
        except NotFoundError:
            return None
        logger.debug('ElasticFood: got results: "%s"', results)
        return results


es = ElasticFood("http://elastic:9200")
