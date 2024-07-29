#!/bin/bash

# Exit on any "error". More sophisticated approaches could be implemented in future.
# See also: https://stackoverflow.com/questions/4381618/exit-a-script-on-error
set -e

echo ""
echo "[INFO] Executing entrypoint..."


#------------------------------
#   Data & media dirs
#------------------------------
echo "[INFO] Setting up media and database dirs..."

mkdir -p /data/media 
chown webapp:webapp /data/media

mkdir -p /data/db 
chown webapp:webapp /data/db

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
    ENTRYPOINT_COMMAND="sudo -i -u webapp /run.sh"
else
    ENTRYPOINT_COMMAND=$@
fi

echo -n "[INFO] Executing entrypoint command: "
echo $ENTRYPOINT_COMMAND
exec $ENTRYPOINT_COMMAND
