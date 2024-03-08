#!/bin/bash

# Exit on any "error". More sophisticated approaches could be implemented in future.
# See also: https://stackoverflow.com/questions/4381618/exit-a-script-on-error
set -e

echo ""
echo "[INFO] Executing entrypoint..."


#------------------------------
#   Set up SSL certificates
#------------------------------
echo "[INFO] Setting up SSL..."

# Always create dir if not existent
mkdir -p /etc/letsencrypt/live/$PUBLIC_HOST/

# If there are no certificates, use snakeoils
if [ ! -f "/etc/letsencrypt/live/$PUBLIC_HOST/cert.pem" ]; then
    echo "Using default self-signed certificate cer file for $PUBLIC_HOST as not existent..."
    cp -a /root/certificates/selfsigned.crt /etc/letsencrypt/live/$PUBLIC_HOST/cert.pem
else
    echo "Not using default self-signed certificate cer file for $PUBLIC_HOST as already existent."
fi

if [ ! -f "/etc/letsencrypt/live/$PUBLIC_HOST/privkey.pem" ]; then
    echo "Using default self-signed certificate privkey file for $PUBLIC_HOST as not existent..."
    cp -a /root/certificates/selfsigned.key /etc/letsencrypt/live/$PUBLIC_HOST/privkey.pem
else
    echo "Not using default self-signed certificate privkey file for $PUBLIC_HOST as already existent."
fi

if [ ! -f "/etc/letsencrypt/live/$PUBLIC_HOST/fullchain.pem" ]; then
    echo "Using default self-signed certificate fullchain file for $PUBLIC_HOST as not existent..."
    cp -a /root/certificates/selfsigned.ca-bundle /etc/letsencrypt/live/$PUBLIC_HOST/fullchain.pem
else
    echo "Not using default self-signed certificate fullchain file for $PUBLIC_HOST as already existent."
fi

# Replace the PUBLIC_HOST in the Apache proxy conf. Directly using an env var doen not wotk
# with the letsencryot client, which has a bug: https://github.com/certbot/certbot/issues/8243
sudo sed -i "s/__PUBLIC_HOST__/$PUBLIC_HOST/g" /etc/apache2/sites-available/proxy-global.conf


#------------------------------
#   Save environment to file
#------------------------------
echo "[INFO] Dumping env..."

env | \
while read env_var; do
  if [[ $env_var == HOME\=* ]]; then
      : # Skip HOME var
  elif [[ $env_var == PWD\=* ]]; then
      : # Skip PWD var
  else
      echo "export $env_var" >> /env.sh
  fi
done


#------------------------------
#  Execute entrypoint command
#------------------------------
if [[ "x$@" == "x" ]] ; then
    ENTRYPOINT_COMMAND="supervisord"
else
    ENTRYPOINT_COMMAND=$@
fi

echo -n "[INFO] Executing entrypoint command: "
echo $ENTRYPOINT_COMMAND
exec "$ENTRYPOINT_COMMAND"
