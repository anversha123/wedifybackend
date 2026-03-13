#!/usr/bin/env bash
# exit on error
set -o errexit

# Change directory to backend if it exists (for root-level execution)
if [ -d "backend" ]; then
    cd backend
fi

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
