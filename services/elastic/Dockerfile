FROM docker.elastic.co/elasticsearch/elasticsearch:7.17.21

# Copy the startup script into the container
COPY check_and_create_index.sh /usr/local/bin/check_and_create_index.sh

# Make the script executable
RUN chmod +x /usr/local/bin/check_and_create_index.sh

# Run the script on container startup
CMD ["/bin/bash", "-c", "/usr/local/bin/check_and_create_index.sh & /usr/local/bin/docker-entrypoint.sh eswrapper"]
