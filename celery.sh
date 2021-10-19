#!/bin/bash
# This script was made to get free dynos on Heroku.
celery -A core worker -l info &
sleep 10
celery -A core beat -l info &