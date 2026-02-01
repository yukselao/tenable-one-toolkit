"""
Tenable One API Helper Functions

This module contains helper functions for interacting with
the Tenable One/IO API:
- Client connection initialization
- Scan listing
- Asset export operations
- Asset info lookup
- AES analysis
"""

import os
import sys
import json
import pandas as pd
from tenable.io import TenableIO
from tenable.errors import TioExportsError


# ==========================================
# FILE I/O HELPERS
# ==========================================

def save_dataframe(df, file_path):
    """
    Save DataFrame to file. Format is determined by file extension.
    Supports: .parquet (default), .csv

    Args:
        df: pandas DataFrame
        file_path: Output file path
    """
    if file_path.endswith('.csv'):
        df.to_csv(file_path, index=False)
    else:
        # Default to parquet for better data integrity
        df.to_parquet(file_path, index=False)


def load_dataframe(file_path):
    """
    Load DataFrame from file. Format is determined by file extension.
    Supports: .parquet (default), .csv

    Args:
        file_path: Input file path

    Returns:
        pandas DataFrame
    """
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    else:
        return pd.read_parquet(file_path)


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

def export_assets_by_tag(tio, tag_category, tag_value, output_file='assets.parquet'):
    """
    Filters assets by the specified tag category and value,
    then exports them to a file (parquet or csv based on extension).

    Args:
        tio: TenableIO client instance
        tag_category: Tag category to filter (e.g., "Location")
        tag_value: Tag value to filter (e.g., "London")
        output_file: Output filename (.parquet or .csv)

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
            # Flatten relevant fields
            # Handle empty lists safely
            ipv4s = asset.get('ipv4s') or []
            hostnames = asset.get('hostnames') or []
            os_list = asset.get('operating_system') or []

            flat_asset = {
                'id': asset.get('id'),
                'ipv4': ipv4s[0] if ipv4s else '',
                'hostname': hostnames[0] if hostnames else '',
                'os': os_list[0] if os_list else 'Unknown',
                'exposure_score': asset.get('exposure_score', 0),  # AES score
                'acr_score': asset.get('acr_score', 0),            # ACR score
                'tags': asset.get('tags', [])  # Keep as list for parquet
            }
            asset_data.append(flat_asset)

        if not asset_data:
            print(f"No assets found with tag {tag_category}:{tag_value}")
            return None

        df = pd.DataFrame(asset_data)
        save_dataframe(df, output_file)

        print(f"{len(df)} assets exported to '{output_file}'")
        return df

    except TioExportsError as e:
        print(f"Export job error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return None


# ==========================================
# EXPORT ALL ASSETS
# ==========================================

def export_all_assets(tio, output_file='assets.parquet'):
    """
    Exports all assets without any tag filtering.

    Args:
        tio: TenableIO client instance
        output_file: Output filename (.parquet or .csv)

    Returns:
        DataFrame: Exported asset data or None
    """
    print("\n--- Asset Export (All Assets) ---")

    asset_data = []

    try:
        # Export all assets without filters
        assets_iterator = tio.exports.assets()

        print("Export job started, downloading data...")

        for asset in assets_iterator:
            # Flatten relevant fields
            ipv4s = asset.get('ipv4s') or []
            hostnames = asset.get('hostnames') or []
            os_list = asset.get('operating_system') or []

            flat_asset = {
                'id': asset.get('id'),
                'ipv4': ipv4s[0] if ipv4s else '',
                'hostname': hostnames[0] if hostnames else '',
                'os': os_list[0] if os_list else 'Unknown',
                'exposure_score': asset.get('exposure_score', 0),
                'acr_score': asset.get('acr_score', 0),
                'tags': asset.get('tags', [])  # Keep as list for parquet
            }
            asset_data.append(flat_asset)

        if not asset_data:
            print("No assets found.")
            return None

        df = pd.DataFrame(asset_data)
        save_dataframe(df, output_file)

        print(f"{len(df)} assets exported to '{output_file}'")
        return df

    except TioExportsError as e:
        print(f"Export job error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return None


# ==========================================
# ASSET INFO LOOKUP
# ==========================================

def get_asset_info(tio, hostname, data_file='assets.parquet'):
    """
    Retrieves detailed asset information by hostname.
    First searches in data file, then tries API for full details.

    Args:
        tio: TenableIO client instance
        hostname: Asset hostname to search for
        data_file: Path to exported assets file (.parquet or .csv)

    Returns:
        dict: Asset details or None
    """
    print(f"\n--- Asset Info: {hostname} ---")

    try:
        asset_uuid = None
        file_data = None

        # First try to find in data file (more complete dataset)
        try:
            df = load_dataframe(data_file)
            hostname_lower = hostname.lower()

            for _, row in df.iterrows():
                row_hostname = str(row.get('hostname', '')).lower()
                row_ipv4 = str(row.get('ipv4', '')).lower()

                if hostname_lower == row_hostname or hostname_lower == row_ipv4:
                    asset_uuid = row.get('id')
                    file_data = row
                    break

        except FileNotFoundError:
            print(f"Note: Data file '{data_file}' not found, searching via API only...")

        # If not found in CSV, try API
        if not asset_uuid:
            for asset in tio.assets.list():
                asset_hostnames = asset.get('hostname') or []
                asset_fqdns = asset.get('fqdn') or []
                asset_netbios = asset.get('netbios_name') or []
                asset_ipv4s = asset.get('ipv4') or []

                all_names = asset_hostnames + asset_fqdns + asset_netbios + asset_ipv4s

                if any(h.lower() == hostname.lower() for h in all_names):
                    asset_uuid = asset.get('id')
                    break

        if not asset_uuid:
            print(f"Asset with hostname '{hostname}' not found.")
            return None

        # Try to get detailed info via API
        try:
            details = tio.assets.details(asset_uuid)

            hostname_list = details.get('hostname') or []
            fqdn_list = details.get('fqdn') or []
            os_list = details.get('operating_system') or []
            system_type_list = details.get('system_type') or []

            friendly_output = {
                'Asset ID': details.get('id'),
                'Name': details.get('name', 'N/A'),
                'Hostname': hostname_list[0] if hostname_list else 'N/A',
                'FQDN': fqdn_list[0] if fqdn_list else 'N/A',
                'IPv4 Addresses': details.get('ipv4') or [],
                'IPv6 Addresses': details.get('ipv6') or [],
                'MAC Addresses': details.get('mac_address') or [],
                'Operating System': os_list[0] if os_list else 'Unknown',
                'System Type': system_type_list,
                'Network': 'Default',
                'Exposure Score (AES)': details.get('exposure_score') or details.get('aes_score_v3') or 'N/A',
                'ACR Score': details.get('acr_score') or details.get('acr_score_v3') or 'N/A',
                'First Seen': details.get('first_seen', 'N/A'),
                'Last Seen': details.get('last_seen', 'N/A'),
                'Last Authenticated Scan': details.get('last_authenticated_scan_date') or 'N/A',
                'Last Licensed Scan': details.get('last_licensed_scan_date') or 'N/A',
                'Has Agent': details.get('has_agent', False),
                'Agent Name': details.get('agent_name') or [],
                'Sources': [s.get('name') for s in (details.get('sources') or [])],
                'Tags': [
                    f"{t.get('tag_key')}:{t.get('tag_value')}"
                    for t in (details.get('tags') or [])
                ]
            }

            print(json.dumps(friendly_output, indent=2, default=str))
            return details

        except Exception:
            # If API details fail, use file data
            if file_data is not None:
                friendly_output = {
                    'Asset ID': file_data.get('id', 'N/A'),
                    'Hostname': file_data.get('hostname', 'N/A'),
                    'IPv4': file_data.get('ipv4', 'N/A'),
                    'Operating System': file_data.get('os', 'Unknown'),
                    'Exposure Score (AES)': file_data.get('exposure_score', 'N/A'),
                    'ACR Score': file_data.get('acr_score', 'N/A'),
                    'Tags': file_data.get('tags', 'N/A'),
                    'Note': 'Limited data from file (API details unavailable)'
                }
                print(json.dumps(friendly_output, indent=2, default=str))
                return friendly_output

            raise

    except Exception as e:
        print(f"Error retrieving asset info: {e}")
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


# ==========================================
# PLUGIN INFO & AFFECTED ASSETS
# ==========================================

def get_plugin_info(tio, plugin_id):
    """
    Retrieves plugin details and lists affected assets.

    Args:
        tio: TenableIO client instance
        plugin_id: Plugin ID to look up (e.g., 10114)

    Returns:
        dict: Plugin details and affected assets
    """
    print(f"\n--- Plugin Info: {plugin_id} ---")

    try:
        # Get plugin details
        plugin = tio.plugins.plugin_details(plugin_id)

        # Convert attributes list to dictionary for easier access
        # API returns: [{'attribute_name': 'key', 'attribute_value': 'value'}, ...]
        attributes_list = plugin.get('attributes', [])
        attributes = {}
        for attr in attributes_list:
            key = attr.get('attribute_name')
            value = attr.get('attribute_value')
            # Handle multiple values for same key (like cve)
            if key in attributes:
                if isinstance(attributes[key], list):
                    attributes[key].append(value)
                else:
                    attributes[key] = [attributes[key], value]
            else:
                attributes[key] = value

        # Get affected assets using workbenches API
        affected_assets = []
        try:
            for asset in tio.workbenches.vuln_assets(('plugin.id', 'eq', str(plugin_id))):
                asset_info = {
                    'id': asset.get('id'),
                    'hostname': (asset.get('hostname') or ['N/A'])[0] if isinstance(asset.get('hostname'), list) else asset.get('hostname', 'N/A'),
                    'ipv4': (asset.get('ipv4') or ['N/A'])[0] if isinstance(asset.get('ipv4'), list) else asset.get('ipv4', 'N/A'),
                    'fqdn': (asset.get('fqdn') or ['N/A'])[0] if isinstance(asset.get('fqdn'), list) else asset.get('fqdn', 'N/A'),
                    'operating_system': (asset.get('operating_system') or ['Unknown'])[0] if isinstance(asset.get('operating_system'), list) else asset.get('operating_system', 'Unknown'),
                    'last_seen': asset.get('last_seen', 'N/A')
                }
                affected_assets.append(asset_info)
        except Exception as e:
            print(f"Warning: Could not retrieve affected assets: {e}")

        # Get description and truncate if too long
        description = attributes.get('description', 'N/A')
        if isinstance(description, str) and len(description) > 500:
            description = description[:500] + '...'

        # Build human-friendly output
        friendly_output = {
            'Plugin ID': plugin.get('id'),
            'Name': plugin.get('name'),
            'Family': plugin.get('family_name'),
            'Severity': attributes.get('risk_factor', 'N/A'),
            'CVSS Base Score': attributes.get('cvss_base_score', 'N/A'),
            'CVSS3 Base Score': attributes.get('cvss3_base_score', 'N/A'),
            'CVSS Vector': attributes.get('cvss_vector', 'N/A'),
            'Synopsis': attributes.get('synopsis', 'N/A'),
            'Description': description,
            'Solution': attributes.get('solution', 'N/A'),
            'CVE': attributes.get('cve') if isinstance(attributes.get('cve'), list) else [attributes.get('cve')] if attributes.get('cve') else [],
            'CWE': attributes.get('cwe', 'N/A'),
            'See Also': attributes.get('see_also', 'N/A'),
            'Plugin Publication Date': attributes.get('plugin_publication_date', 'N/A'),
            'Plugin Modification Date': attributes.get('plugin_modification_date', 'N/A'),
            'Affected Assets Count': len(affected_assets),
            'Affected Assets': affected_assets[:20]  # Limit to first 20
        }

        if len(affected_assets) > 20:
            friendly_output['Note'] = f'Showing first 20 of {len(affected_assets)} affected assets'

        print(json.dumps(friendly_output, indent=2, default=str))
        return friendly_output

    except Exception as e:
        print(f"Error retrieving plugin info: {e}")
        return None


# ==========================================
# ASSET SEARCH
# ==========================================

def search_assets(tio, query, data_file='assets.parquet'):
    """
    Search assets by IP address or hostname from exported data file.
    Falls back to API if file not found.

    Args:
        tio: TenableIO client instance
        query: Search query (IP address or hostname)
        data_file: Path to exported assets file (.parquet or .csv)

    Returns:
        list: Matching assets
    """
    print(f"\n--- Asset Search: {query} ---")

    try:
        matches = []
        query_lower = query.lower()

        # Try to load from data file first (more complete data)
        try:
            df = load_dataframe(data_file)
            print(f"Searching in '{data_file}'...")

            for _, row in df.iterrows():
                # Search in hostname, ipv4, and id columns
                searchable = f"{row.get('hostname', '')} {row.get('ipv4', '')} {row.get('id', '')}".lower()

                if query_lower in searchable:
                    match_info = {
                        'id': row.get('id', 'N/A'),
                        'hostname': row.get('hostname', 'N/A'),
                        'ipv4': row.get('ipv4', 'N/A'),
                        'os': row.get('os', 'Unknown'),
                        'exposure_score': row.get('exposure_score', 'N/A'),
                        'acr_score': row.get('acr_score', 'N/A')
                    }
                    matches.append(match_info)

        except FileNotFoundError:
            print(f"Data file '{data_file}' not found. Searching via API...")
            # Fall back to API
            for asset in tio.assets.list():
                hostnames = asset.get('hostname') or []
                fqdns = asset.get('fqdn') or []
                netbios = asset.get('netbios_name') or []
                ipv4s = asset.get('ipv4') or []
                ipv6s = asset.get('ipv6') or []

                all_fields = hostnames + fqdns + netbios + ipv4s + ipv6s

                if any(query_lower in str(field).lower() for field in all_fields):
                    match_info = {
                        'id': asset.get('id'),
                        'hostname': hostnames[0] if hostnames else 'N/A',
                        'ipv4': ipv4s[0] if ipv4s else 'N/A',
                        'os': (asset.get('operating_system') or ['Unknown'])[0] if isinstance(asset.get('operating_system'), list) else 'Unknown',
                        'exposure_score': asset.get('exposure_score', 'N/A'),
                        'acr_score': asset.get('acr_score', 'N/A')
                    }
                    matches.append(match_info)

        if not matches:
            print(f"No assets found matching '{query}'")
            return []

        # Format output
        output = {
            'Query': query,
            'Total Matches': len(matches),
            'Assets': matches[:50]
        }

        if len(matches) > 50:
            output['Note'] = f'Showing first 50 of {len(matches)} matches'

        print(json.dumps(output, indent=2, default=str))
        return matches

    except Exception as e:
        print(f"Error searching assets: {e}")
        return []
