#!/usr/bin/env bash
# Build script for Vercel Serverless Deployment
set -e

echo "==> Preparing build directories..."
mkdir -p staticfiles_build/static

echo "==> Setting up Python 3.11 environment..."
if command -v uv &> /dev/null; then
    echo "Using uv to provision Python 3.11 virtual environment..."
    uv venv --python 3.11 .build_venv
    source .build_venv/bin/activate
    echo "Installing requirements into Python 3.11 environment..."
    uv pip install -r requirements.txt
elif command -v python3.11 &> /dev/null; then
    echo "Using python3.11 venv..."
    python3.11 -m venv .build_venv
    source .build_venv/bin/activate
    pip install -r requirements.txt
else
    echo "Using system python venv fallback..."
    python3 -m venv .build_venv
    source .build_venv/bin/activate
    pip install -r requirements.txt
fi

echo "==> Collecting static assets with Django..."
python manage.py collectstatic --noinput --clear

echo "==> Ensuring static output directory exists..."
mkdir -p staticfiles_build/static

echo "==> Build completed successfully!"
