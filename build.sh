#!/usr/bin/env bash
# Render build script — runs once during every deployment

set -e  # Exit immediately on any error

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🗄️  Running database migrations..."
alembic upgrade head

echo "✅ Build complete!"
