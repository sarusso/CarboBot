# Carbo Bot

Bot for obtaining food carbohydrates info (and more).

## Quickstart

Requirements:
    
    Bash, Git and Docker.

Build

    $ carbobot/build

Run

	$ carbobot/run

List running services

    # carbobot/ps

Clean

	# carbobot/clean


## Configuration

### Webapp

These are the webapp service configuration parameters and their defaults in Django:

      - DJANGO_DEV_SERVER=true
      - DJANGO_DEBUG=true
      - DJANGO_LOG_LEVEL=ERROR
      - WEBAPP_LOG_LEVEL=DEBUG
      - DJANGO_SECRET_KEY=""

### Proxy

These is the proxy service configuration parameter and its default:

      - PUBLIC_HOST=localhost

Certificates can be automatically handled with Letsencrypt. By default, a snakeoil certificate is used. To set up Letsencrypt, you need to run the following commands inside the proxy service (once in its lifetime).

    $ carbobot/shell proxy

First of all remove the default snakeoil certificates:

	$ sudo rm -rf /etc/letsencrypt/live/YOUR_PUBLIC_HOST
Then:

    $ nano /etc/apache2/sites-available/proxy-global.conf
    
...and change the certificates for the domain that you want to enable with Letsencrypt to use the snakeoils located in `/root/certificates/` as per the first lines of the `proxy-global.conf` file (otherwise next command will fail).

Now restart apache to pick up the new snakeoils:

	$  sudo apache2ctl -k graceful

Lastly, tell certbot to generate and validate certificates for the domain:

    $ sudo certbot certonly --apache --register-unsafely-without-email --agree-tos -d YOUR_PUBLIC_HOST
    
This will initialize the certificates in /etc/letsencypt, which are stored on the host in `./data/proxy/letsencrypt`

Finally, re-run the proxy service to drop the temporary changes and pick up the new, real certificates:

    $ carbobot/rerun proxy


## Development

### Live code changes

Django development server is running on port 8080 of the "webapp" service.

To enable live code changes, add or comment out the following in docker-compose.yaml under the "volumes" section of the "webapp" service:

    - ./services/webapp/code:/code
    
This will mount the code from services/webapp/code as a volume inside the webapp container itself allowing to make immediately effective codebase edits.

Note that when you edit the Django ORM model, you need to make migrations and apply them to migrate the database:

    $ carbobot/makemigrations
    $ carbobot/migrate


### Testing

Run the tests (Django unit tests):
    
    $ carbobot/test


### Logs


Check out logs for Docker containers:


    $ webapp/logs web

    $ webapp/logs proxy


Check out logs for supervisord tasks in the proxy service:

    $ carbobot/logs proxy apache
    
    $ carbobot/logs proxy certbot

    
## Known issues

### Building errors

It is common for the build process to fail with a "404 not found" error on an apt-get instructions, as apt repositories often change their IP addresses. In such case, try:

    $ CACHE=false carbobot/build

## License

This work is licensed under the Apache License 2.0.


