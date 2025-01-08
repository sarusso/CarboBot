FROM docker.elastic.co/elasticsearch/elasticsearch:7.17.21

# Copy the initialization script into the container
COPY initialize.sh /usr/local/bin/initialize.sh

# Make the script executable
RUN chmod +x /usr/local/bin/initialize.sh

# Run the script on container startup
CMD ["/bin/bash", "-c", "/usr/local/bin/initialize.sh & /usr/local/bin/docker-entrypoint.sh eswrapper"]
