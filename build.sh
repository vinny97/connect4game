#!/usr/bin/env bash

# Install system dependencies for lxml
apt-get update && apt-get install -y libxml2-dev libxslt-dev
pip install -r requirements.txt
