#!/bin/bash
# This script was made to get free dynos on Heroku.
celery -A core worker -l info &
sleep 10
echo "Starting Celery beat"
celery -A core beat -l info