#!/bin/bash

# Curl a URL with the X-Varnish-Nuke:1 header to refresh
# the cache for that endpoint, formatted as below
curl -H 'X-Varnish-Nuke:1' -f http://cache:8000/docs
