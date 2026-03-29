#!/usr/bin/env bash
set -e
pip install -r requirements.txt
python decision_app/manage.py collectstatic --no-input
python decision_app/manage.py migrate
