#!/bin/bash
set -e  # Exit on error

python -m venv --copies /opt/venv
source /opt/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt