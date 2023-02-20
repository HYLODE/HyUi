#!/bin/bash

# Curl a URL with the X-Varnish-Nuke:1 header to refresh
# the cache for that endpoint, formatted as below
curl -H 'X-Varnish-Nuke:1' -f http://cache:8000/docs

# refresh cache for /electives between 6:00 and 6:30
currenttime=$(date +%H:%M)
if [[ "$currenttime" > "06:00" ]] && [[ "$currenttime" < "06:30" ]]; then
  curl -H 'X-Varnish-Nuke:1' -f http://cache:8000/electives/
fi
