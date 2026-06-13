#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
set -a
source "$SCRIPT_DIR/credentials.env"
set +a
cd "$SCRIPT_DIR"
python3 scraper.py
