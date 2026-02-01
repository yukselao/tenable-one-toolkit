# Tenable One Asset Analysis Tool

A CLI tool for interacting with the Tenable One API to list scans, export assets, and analyze asset exposure scores (AES).

## Features

- List all successful (completed) VM scans
- Export assets to Parquet format (or CSV) - filtered by tag or all assets
- Get detailed asset info by hostname (human-friendly JSON)
- Get plugin details and affected assets by plugin ID
- Search assets by IP address or hostname
- Identify top exposed assets based on AES (Asset Exposure Score)
- Fully parameterized CLI interface

## Prerequisites

- Python 3.8+
- Tenable One / Tenable.io account with API access
- API Access Key and Secret Key

## Installation

### 1. Clone the repository

```bash
git clone git@github.com:yukselao/tenable-one-toolkit.git
cd tenable-one-toolkit
```

### 2. Create virtual environment

```bash
python3 -m venv venv
```

### 3. Activate virtual environment

**macOS / Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your Tenable API credentials:
```
TENABLE_ACCESS_KEY=your_actual_access_key
TENABLE_SECRET_KEY=your_actual_secret_key
```

## How It Works

A typical workflow to explore your Tenable One environment:

```bash
# 1. Overview - Check scan status
python main.py --list-scans

# 2. Discovery - Export full asset inventory
python main.py --export-all -o all_assets.parquet

# 3. Top 10 riskiest assets - Where to focus?
python main.py --top-assets -i all_assets.parquet --top 10

# 4. Deep dive into a specific asset - details + top 5 vulnerabilities
python main.py --asset-info se-dc1 -i all_assets.parquet --limit 5

# 5. Get ALL vulnerabilities for an asset (no limit)
python main.py --asset-info se-dc1 -i all_assets.parquet --limit 0

# 6. Search assets - By IP (show first 10 matches)
python main.py --search-assets 192.168.15 -i all_assets.parquet --limit 10

# 7. Search assets - By hostname (show all matches)
python main.py --search-assets dc -i all_assets.parquet --limit 0

# 8. Investigate a critical vulnerability (top 5 affected assets)
python main.py --plugin-info 10114 --limit 5

# 9. Tag-based filtering - Specific group
python main.py --export-assets --tag-category tom --tag-value 'linux servers' -o linux.parquet

# 10. Top risks in that group
python main.py --top-assets -i linux.parquet --top 5

# 11. Export for sharing - Convert to CSV or JSON
python main.py --to-csv -i all_assets.parquet
python main.py --to-json -i all_assets.parquet
```

**Note:** Use `--limit N` to control output size. `--limit 0` or `--limit -1` shows all items.

**Demo story:** Scan status → Inventory → Risk prioritization → Investigation → Vulnerability analysis → Segment-based review → Export for sharing

## Usage

### Show help

```bash
python main.py --help
```

### List completed scans

```bash
python main.py --list-scans
```

### Export assets by tag

```bash
# Default output (assets.parquet)
python main.py --export-assets --tag-category Location --tag-value London

# Custom output file
python main.py --export-assets --tag-category tom --tag-value 'linux servers' -o linux.parquet

# Export as CSV if needed
python main.py --export-assets --tag-category tom --tag-value 'linux servers' -o linux.csv
```

### Export all assets

```bash
# Export all assets (default: assets.parquet)
python main.py --export-all

# Custom output file
python main.py --export-all -o all_assets.parquet
```

### Get asset info by hostname (with vulnerabilities)

```bash
# First export assets, then search in the exported file
python main.py --export-all -o all_assets.parquet

# Get detailed asset information including vulnerabilities (default: top 30)
python main.py --asset-info se-dc1 -i all_assets.parquet

# Limit vulnerabilities to top 10
python main.py --asset-info se-dc1 -i all_assets.parquet --limit 10

# Show all vulnerabilities (no limit)
python main.py --asset-info se-dc1 -i all_assets.parquet --limit 0
```

Output includes: asset details, tags, exposure scores, and vulnerabilities sorted by severity (Critical → High → Medium → Low → Info) with a summary count.

### Get plugin info and affected assets

```bash
# Get plugin details (CVE, CVSS, solution) and list of affected assets
python main.py --plugin-info 10114

# Limit affected assets to 50
python main.py --plugin-info 10114 --limit 50

# Show all affected assets
python main.py --plugin-info 10114 --limit 0
```

### Search assets

```bash
# First export assets, then search in the exported file
python main.py --export-all -o all_assets.parquet

# Search by IP address (partial match)
python main.py --search-assets 192.168.15 -i all_assets.parquet

# Search with custom limit
python main.py --search-assets dc -i all_assets.parquet --limit 10

# Search with no limit (show all matches)
python main.py --search-assets 192.168 -i all_assets.parquet --limit 0

# Search by hostname (partial match)
python main.py --search-assets win-server -i all_assets.parquet
python main.py --search-assets dc -i all_assets.parquet
```

### Display top exposed assets

```bash
# From default file (assets.parquet)
python main.py --top-assets

# From specific file with custom count
python main.py --top-assets -i all_assets.parquet --top 10
```

### Run all operations

```bash
python main.py --all --tag-category Location --tag-value London
```

### Convert Parquet to CSV or JSON

```bash
# Convert to CSV (same filename with .csv extension)
python main.py --to-csv -i all_assets.parquet

# Convert to JSON (same filename with .json extension)
python main.py --to-json -i all_assets.parquet

# Convert with custom output filename
python main.py --to-csv -i all_assets.parquet -o exported_assets.csv
python main.py --to-json -i all_assets.parquet -o exported_assets.json
```

## CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--list-scans` | | List all completed scans | |
| `--export-assets` | | Export assets filtered by tag | |
| `--export-all` | | Export all assets without filtering | |
| `--asset-info` | | Get asset details + vulnerabilities (JSON) | |
| `--plugin-info` | | Get plugin details and affected assets | |
| `--search-assets` | | Search assets by IP or hostname | |
| `--top-assets` | | Display top exposed assets | |
| `--to-csv` | | Convert input file to CSV format | |
| `--to-json` | | Convert input file to JSON format | |
| `--all` | | Run all operations | |
| `--tag-category` | | Tag category for filtering | `Location` |
| `--tag-value` | | Tag value for filtering | `London` |
| `--output` | `-o` | Output file path (.parquet, .csv, .json) | `assets.parquet` |
| `--input` | `-i` | Input file for analysis | `assets.parquet` |
| `--top` | | Number of top assets | `5` |
| `--limit` | | Limit output items (0 or -1 = unlimited) | `30` |

## Project Structure

```
tenable-one-toolkit/
├── .env                # API credentials (git-ignored)
├── .env.example        # Example environment file
├── main.py             # CLI entry point
├── modules/
│   ├── __init__.py
│   └── helper.py       # Helper functions
├── requirements.txt    # Python dependencies
└── README.md
```

## Why Parquet?

We use Parquet format by default instead of CSV because:
- **Data integrity**: Complex nested data (like tags) is preserved without escaping issues
- **Performance**: Faster read/write operations, especially for large datasets
- **Compression**: Smaller file sizes
- **Type safety**: Column types are preserved

You can still use CSV by specifying `.csv` extension in the `-o` and `-i` parameters.

## Script Explanations

### 1. Authentication (`get_client`)

We use `TenableIO`. Even though the product is Tenable One, the underlying API endpoints for Vulnerability Management are hosted on the `cloud.tenable.com` infrastructure used by Tenable VM. The pyTenable library handles the `X-ApiKeys` header generation automatically.

### 2. Listing Scans (`list_successful_scans`)

We use `tio.scans.list()`. This endpoint retrieves scan definitions. We loop through them and check if `scan.get('status') == 'completed'` to ensure we only report successful runs, filtering out `aborted`, `running`, or `pending` scans.

### 3. Asset Export (`export_assets_by_tag`)

This is the most critical part. Instead of listing assets page-by-page (which is slow and rate-limited), we use the Export API:

- **`tio.exports.assets()`**: This initiates an asynchronous job on the Tenable cloud.
- **Filtering**: We pass `tags=[(Category, Value)]` to the export function. Tenable filters the data server-side before sending it to us.
- **Pandas**: We load the results into a Pandas DataFrame and save to Parquet (or CSV based on file extension).

### 4. Export All Assets (`export_all_assets`)

Calls `tio.exports.assets()` without any filters to export the entire asset inventory. Useful for full inventory reports or when you need all assets regardless of tags.

### 5. Asset Info Lookup (`get_asset_info`)

- First searches in the exported data file (specified by `-i` parameter) for more complete data
- Falls back to API if file not found
- Once asset UUID is found, retrieves full details via `tio.assets.details(uuid)`
- Outputs human-friendly JSON with key fields: IP addresses, OS, AES/ACR scores, first/last seen dates, tags, etc.

### 6. Top Assets by AES (`get_top_exposed_assets`)

- **AES (Asset Exposure Score)**: In the API JSON response, this field is usually mapped to `exposure_score` (ranges from 0-1000).
- We cast this column to numeric (handling any potential nulls) and use `df.sort_values(ascending=False)` to put the riskiest assets at the top.

### 7. Plugin Info (`get_plugin_info`)

- Uses `tio.plugins.plugin_details(plugin_id)` to get plugin metadata (CVE, CVSS, synopsis, solution)
- Uses `tio.workbenches.vuln_assets()` to find all assets affected by this plugin
- Outputs human-friendly JSON with plugin details and up to 20 affected assets

### 8. Asset Search (`search_assets`)

- First searches in the exported data file (specified by `-i` parameter) for more complete data
- Falls back to API if file not found
- Performs partial, case-insensitive matching across hostname, IPv4, and ID fields
- Returns up to 50 matching assets with key details

## Output Example

### List Scans

```
$ python main.py --list-scans

--- Successful VM Scans ---
Scan ID    | Status          | Scan Name
------------------------------------------------------------
4027       | completed       | Tire 1 Vuln Scan

Total Successful Scans: 1
```

### Export Assets

```
$ python main.py --export-all -o all_assets.parquet

--- Asset Export (All Assets) ---
Export job started, downloading data...
13489 assets exported to 'all_assets.parquet'
```

### Top Exposed Assets

```
$ python main.py --top-assets -i all_assets.parquet --top 10

Loaded 13489 assets from 'all_assets.parquet'

--- Top 10 Most Exposed Assets (AES) ---
AES        | IP Address      | Hostname
--------------------------------------------------
948        | 192.168.15.102  | se-dc2
948        | 192.168.15.101  | se-dc1
947        | 192.168.42.100  | dc1
945        | 192.168.15.168  | se-ad-dc
942        | 192.168.48.56   | target2
```

### Asset Info (with Vulnerabilities)

```
$ python main.py --asset-info se-dc1 -i all_assets.parquet

--- Asset Info: se-dc1 ---
{
  "Asset ID": "fcc29644-748e-4143-83d6-f75055b575d0",
  "Name": "se-dc1",
  "Hostname": "se-dc1",
  "FQDN": "se-dc1.demo.io",
  "IPv4 Addresses": ["192.168.15.101"],
  "Operating System": "Microsoft Windows Server 2019 Standard Build 17763",
  "Exposure Score (AES)": 948,
  "ACR Score": 9,
  "Tags": [
    "Software:Mcafee Agent Missing",
    "OS:Windows Server",
    "OS:Windows"
  ],
  "Vulnerability Count": 310,
  "Vulnerability Summary": {
    "Critical": 49,
    "High": 63,
    "Medium": 21,
    "Low": 3,
    "Info": 174
  },
  "Vulnerabilities": [
    {
      "plugin_id": 182865,
      "plugin_name": "KB5031361: Windows Server 2019 Security Update (October 2023)",
      "severity": "Critical",
      "vpr_score": 8.4,
      "cvss_base_score": 10.0,
      "exploit_available": false
    },
    ...
  ],
  "Vulnerabilities Note": "Showing top 30 of 310 vulnerabilities (sorted by severity)"
}
```

## License

MIT
