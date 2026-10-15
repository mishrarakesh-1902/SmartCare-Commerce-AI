#!/usr/bin/env bash
# Build script for Vercel Serverless Deployment
set -e

echo "==> Preparing build directories..."
mkdir -p staticfiles_build/static

echo "==> Installing Python dependencies..."
if command -v uv &> /dev/null; then
    echo "Detected uv, installing dependencies..."
    uv pip install --system -r requirements.txt
elif python3 -m pip install -r requirements.txt --break-system-packages; then
    echo "Installed dependencies with pip (--break-system-packages)..."
else
    echo "Creating virtual environment fallback..."
    python3 -m venv .build_venv
    source .build_venv/bin/activate
    pip install -r requirements.txt
fi

echo "==> Collecting static assets..."
if [ -d ".build_venv" ]; then
    python manage.py collectstatic --noinput --clear
else
    python3 manage.py collectstatic --noinput --clear
fi

echo "==> Ensuring static output directory exists..."
mkdir -p staticfiles_build/static

echo "==> Build completed successfully!"
