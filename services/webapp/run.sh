#!/bin/bash

DATE=$(date)

echo ""
echo "==================================================="
echo "  Starting Web App @ $DATE"
echo "==================================================="
echo ""

echo "Loading/sourcing env and settings..."
echo ""

# Load env
source /env.sh

# Stay quiet on Python warnings
export PYTHONWARNINGS=ignore

# To Python3 (unbuffered). P.s. "python -u" does not work..
export PYTHONUNBUFFERED=on

# Move to the code dir
cd /code

# Apply migrations if any
python3 manage.py migrate --noinput

if [[ "x$DJANGO_DEV_SERVER" == "xtrue" ]] ; then

    # Run the (development) server
    echo "Now starting the development server."
    exec python3 manage.py runserver 0.0.0.0:8080

else

    # Collect static
    echo "Collecting static files..."
    python3 manage.py collectstatic

    # Run uWSGI
    echo "Now starting the uWSGI server."

    uwsgi --chdir=/code \
          --module=webapp.wsgi \
          --env DJANGO_SETTINGS_MODULE=webapp.settings \
          --master --pidfile=/tmp/webapp-master.pid \
          --workers 8 \
          --threads 1 \
          --socket=127.0.0.1:49152 \
          --static-map /static=/webapp/static \
          --static-map /media=/data/media \
          --http :8080 \
          --harakiri 180 \
          --http-timeout 180 \
          --http-timeout 180 \
          --disable-logging
fi