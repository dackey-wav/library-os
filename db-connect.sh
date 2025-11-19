#!/bin/bash

# default
Role="${1: -owner}"

shift
Args=("$@")

# load .env
if [[ -f ".env" ]]; then
    export $(grep -v '^#' .env | xargs)
else
    echo ".env not found. Copy .env.example first."
    exit 1
fi

if  [[ $Role == "user" ]]; then
    url="$APP_DATABASE_URL_PSQL"
else
    url="$DATABASE_URL_PSQL"
fi

if [[ -z "$url" ]]; then
    echo "URL not found for role: $Role"
    echo "Check .env and ensure urls are set"
    exit 1
fi

exec psql "$url" "${Args[@]}"
