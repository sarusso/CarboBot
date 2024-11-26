from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError


class ElasticFood(Elasticsearch):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index_name = "food_index"

    def init(self):
        self.create_index()

    def reset(self):
        self.indices.delete(self.index_name)
        self.create_index()

    def delete(self):
        self.indices.delete(self.index_name)

    def create_index(self):
        try:
            if not self.indices.exists(index=self.index_name):
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
                self.indices.create(index=self.index_name, body=mapping)
                print(f"Index '{self.index_name}' created.")
            else:
                print(f"Index '{self.index_name}' already exists.")
        except NotFoundError as e:
            print(f"Error checking/creating index: {e}")

    def add(self, item):
        return self.index(index=self.index_name, id=str(item["uuid"]), body=item)

    def search_q(self, q):
        search_query = {"query": {"fuzzy": {"description": q}}}

        return self.search(index=self.index_name, body=search_query)


es = ElasticFood("http://elastic:9200")
