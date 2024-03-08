FROM ubuntu:22.04
MAINTAINER Stefano Alberto Russo <stefano.russo@gmail.com>

# Set non-interactive
ENV DEBIAN_FRONTEND noninteractive

# Update
RUN apt-get update

# Install utilities
RUN apt-get install -y nano telnet wget supervisor net-tools iproute2 iputils-ping sudo curl 

# Create bash_profile for loading correct env (/env.sh created by entrypoint.sh)
RUN echo "source /env.sh" > /root/.bash_profile

# Download get-pip script
RUN curl -O https://bootstrap.pypa.io/pip/3.6/get-pip.py

# Install Python3 and Pip3 (python3-distutils required for pip3)
RUN apt-get install python3 python3-distutils -y 
RUN python3 get-pip.py 'pip==21.3.1'

# Python 3 dev (for pycrypto) and build-essential for uWSGI
RUN apt-get install -y python3-dev build-essential

# Add webapp group, with GID 65527 to try avoiding conflicts.
RUN groupadd -g 65527 webapp

# Add webapp user, with UID 65527 to try avoiding conflicts.
RUN useradd webapp -d /webapp -u 65527 -g 65527 -m -s /bin/bash

# Install Python requirements
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

# Prepare code dir, copy code & fix permissions
RUN mkdir /code
COPY code /code
RUN chown -R webapp:webapp /code

# Run script
COPY run.sh /
RUN chmod 755 /run.sh

# Entrypoint
COPY entrypoint.sh /
RUN chmod 755 /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]