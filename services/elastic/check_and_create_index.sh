#!/bin/bash

# Wait for Elasticsearch to start
until curl -s http://elasticsearch:9200 >/dev/null; do
    echo "Waiting for Elasticsearch to start..."
    sleep 2
done

# Define the index name
INDEX_NAME="food_index"

# Check if the index exists
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:9200/$INDEX_NAME | grep -q "200"; then
    echo "Index $INDEX_NAME does not exist. Creating..."

    # Create the index
    curl -X PUT http://localhost:9200/$INDEX_NAME -H 'Content-Type: application/json' -d '{
          "mappings": {
            "properties": {
              "uuid": { "type": "keyword" },
              "description": { "type": "text" },
              "ingredients": { "type": "keyword" }
            }
          }
        }
        '
else
    echo "Index $INDEX_NAME already exists."
fi

# Start Elasticsearch
exec /usr/local/bin/docker-entrypoint.sh eswrapper
