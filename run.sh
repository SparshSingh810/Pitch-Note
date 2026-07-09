#!/usr/bin/env bash
# Convenience script: set up venv, install deps, seed data, run the app.
set -e
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -q -r requirements.txt
if [ ! -f data/pitchnote.db ]; then
  python data/generate_sample_data.py
fi
python app.py
