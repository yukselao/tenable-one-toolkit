#!/usr/bin/env python3
"""
Tenable One Asset Analysis Tool

This script uses the Tenable One API to:
1. List successful scans
2. Export assets by tag
3. Analyze the most exposed assets (AES)

Usage:
    python main.py
"""

from dotenv import load_dotenv
from modules.helper import (
    get_client,
    list_successful_scans,
    export_assets_by_tag,
    get_top_exposed_assets
)

# Load environment variables from .env file
load_dotenv()


# ==========================================
# CONFIGURATION
# ==========================================

# Tag filtering settings - modify according to your Tenable One tags
TAG_CATEGORY = "Location"
TAG_VALUE = "London"

# Output file
OUTPUT_FILE = "assets.csv"


# ==========================================
# MAIN FLOW
# ==========================================

if __name__ == "__main__":
    # 1. Initialize Tenable API connection
    tio = get_client()

    # 2. List completed scans
    list_successful_scans(tio)

    # 3. Export assets by specified tag
    df_assets = export_assets_by_tag(tio, TAG_CATEGORY, TAG_VALUE, OUTPUT_FILE)

    # 4. Display assets with highest AES scores
    get_top_exposed_assets(df_assets)
