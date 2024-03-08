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

# Supervisord global conf
COPY supervisord.conf /etc/supervisor/

# Install pache & certbot
RUN apt-get install -y apache2 apache2-utils certbot python3-certbot-apache

# Supervisord scripts
COPY supervisord_apache.conf /etc/supervisor/conf.d/
COPY run_apache.sh /etc/supervisor/conf.d/
RUN chmod 755 /etc/supervisor/conf.d/run_apache.sh
COPY supervisord_certbot.conf /etc/supervisor/conf.d/
COPY run_certbot.sh /etc/supervisor/conf.d/
RUN chmod 755 /etc/supervisor/conf.d/run_certbot.sh

# Enable mod_proxy and SSL
RUN a2enmod proxy
RUN a2enmod proxy_http
RUN a2enmod ssl
RUN a2enmod rewrite
RUN a2enmod headers
RUN a2enmod proxy_wstunnel

# Clean up default stuff
RUN rm /etc/apache2/sites-available/000-default.conf
RUN rm /etc/apache2/sites-enabled/000-default.conf
RUN rm /etc/apache2/sites-available/default-ssl.conf
#RUN rm /etc/apache2/sites-enabled/default-ssl.conf

# Apache conf
COPY apache2.conf /etc/apache2/apache2.conf
COPY ssl.conf /etc/apache2/mods-enabled/ssl.conf

# Copy self-signed (snakeoil) certificates
RUN mkdir /root/certificates
COPY certificates/selfsigned.crt /root/certificates/selfsigned.crt
COPY certificates/selfsigned.key /root/certificates/selfsigned.key
COPY certificates/selfsigned.ca-bundle /root/certificates/selfsigned.ca-bundle

# Copy index and norobots.txt
COPY index.html /var/www/html/
COPY norobots.txt /var/www/html/

# Copy and enable conf for proxy and ssl. Warning: there are issues with precedences if splitting
# the conf over multiple files (including task proxy files), as the first conf found in files which
# are read in alphabetical order wins. You can cheeck ordering with "apachectl -t -D DUMP_VHOSTS".
COPY proxy-global.conf /etc/apache2/sites-available/
RUN ln -s /etc/apache2/sites-available/proxy-global.conf /etc/apache2/sites-enabled/proxy-global.conf

# Create default log dir
RUN mkdir -p /var/log/proxy

# Entrypoint
COPY entrypoint.sh /
RUN chmod 755 /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
