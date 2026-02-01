"""
Tenable One API Helper Functions

This module contains helper functions for interacting with
the Tenable One/IO API:
- Client connection initialization
- Scan listing
- Asset export operations
- AES analysis
"""

import os
import sys
import pandas as pd
from tenable.io import TenableIO
from tenable.errors import TioExportsError


# ==========================================
# CLIENT CONNECTION
# ==========================================

def get_client():
    """
    Creates a TenableIO client using API keys from environment variables.

    Required environment variables:
        - TENABLE_ACCESS_KEY
        - TENABLE_SECRET_KEY

    Returns:
        TenableIO: Connected client instance
    """
    access_key = os.getenv('TENABLE_ACCESS_KEY')
    secret_key = os.getenv('TENABLE_SECRET_KEY')

    if not access_key or not secret_key:
        print("Error: TENABLE_ACCESS_KEY and TENABLE_SECRET_KEY must be set as environment variables.")
        sys.exit(1)

    return TenableIO(
        access_key=access_key,
        secret_key=secret_key,
        vendor='Custom Script',
        product='TenableOne_Asset_Tool'
    )


# ==========================================
# SCAN LISTING
# ==========================================

def list_successful_scans(tio):
    """
    Lists all completed scans.

    Args:
        tio: TenableIO client instance
    """
    print("\n--- Successful VM Scans ---")

    try:
        scans = tio.scans.list()

        count = 0
        print(f"{'Scan ID':<10} | {'Status':<15} | {'Scan Name'}")
        print("-" * 60)

        for scan in scans:
            if scan.get('status') == 'completed':
                print(f"{scan.get('id'):<10} | {scan.get('status'):<15} | {scan.get('name')}")
                count += 1

        print(f"\nTotal Successful Scans: {count}")

    except Exception as e:
        print(f"Error listing scans: {e}")


# ==========================================
# ASSET EXPORT
# ==========================================

def export_assets_by_tag(tio, tag_category, tag_value, output_file='assets.csv'):
    """
    Filters assets by the specified tag category and value,
    then exports them to a CSV file.

    Args:
        tio: TenableIO client instance
        tag_category: Tag category to filter (e.g., "Location")
        tag_value: Tag value to filter (e.g., "London")
        output_file: Output CSV filename

    Returns:
        DataFrame: Exported asset data or None
    """
    print(f"\n--- Asset Export (Tag: {tag_category}:{tag_value}) ---")

    asset_data = []

    try:
        # Tag filter format: [(Category, Value)]
        export_filters = [(tag_category, tag_value)]

        # Initiates async export job and automatically downloads chunks
        assets_iterator = tio.exports.assets(tags=export_filters)

        print("Export job started, downloading data...")

        for asset in assets_iterator:
            # Flatten relevant fields for CSV output
            flat_asset = {
                'id': asset.get('id'),
                'ipv4': asset.get('ipv4s', [''])[0],
                'hostname': asset.get('hostnames', [''])[0],
                'os': asset.get('operating_system', ['Unknown'])[0],
                'exposure_score': asset.get('exposure_score', 0),  # AES score
                'acr_score': asset.get('acr_score', 0),            # ACR score
                'tags': str(asset.get('tags', []))
            }
            asset_data.append(flat_asset)

        if not asset_data:
            print(f"No assets found with tag {tag_category}:{tag_value}")
            return None

        df = pd.DataFrame(asset_data)
        df.to_csv(output_file, index=False)

        print(f"{len(df)} assets exported to '{output_file}'")
        return df

    except TioExportsError as e:
        print(f"Export job error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return None


# ==========================================
# AES ANALYSIS
# ==========================================

def get_top_exposed_assets(df, top_n=5):
    """
    Lists assets with the highest AES (Asset Exposure Score)
    from the exported data.

    Args:
        df: DataFrame containing asset data
        top_n: Number of assets to list (default: 5)
    """
    print(f"\n--- Top {top_n} Most Exposed Assets (AES) ---")

    if df is None or df.empty:
        print("No data available for analysis.")
        return

    if 'exposure_score' not in df.columns:
        print("Warning: 'exposure_score' (AES) field not found. Check license/permissions.")
        return

    # Convert AES column to numeric format
    df['exposure_score'] = pd.to_numeric(df['exposure_score'], errors='coerce').fillna(0)

    # Sort by AES in descending order
    top_assets = df.sort_values(by='exposure_score', ascending=False).head(top_n)

    print(f"{'AES':<10} | {'IP Address':<15} | {'Hostname'}")
    print("-" * 50)

    for _, row in top_assets.iterrows():
        print(f"{int(row['exposure_score']):<10} | {row['ipv4']:<15} | {row['hostname']}")
