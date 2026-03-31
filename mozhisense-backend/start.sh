#!/bin/bash
set -e

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Starting MozhiSense API..."
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
