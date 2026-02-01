# Tenable One Asset Analysis Tool

A CLI tool for interacting with the Tenable One API to list scans, export assets by tags, and analyze asset exposure scores (AES).

## Features

- List all successful (completed) VM scans
- Export assets filtered by tag category and value to CSV
- Export all assets without filtering
- Get detailed asset info by hostname (human-friendly JSON)
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
# Basic usage
python main.py --export-assets --tag-category Location --tag-value London

# Custom output file
python main.py --export-assets --tag-category Environment --tag-value Production -o prod_assets.csv
```

### Export all assets

```bash
# Export all assets without tag filtering
python main.py --export-all

# With custom output file
python main.py --export-all -o all_assets.csv
```

### Get asset info by hostname

```bash
# Get detailed asset information in JSON format
python main.py --asset-info win-2019
python main.py --asset-info websvr.labnet.local
```

### Display top exposed assets

```bash
# From default file (assets.csv)
python main.py --top-assets

# From specific file with custom count
python main.py --top-assets --input prod_assets.csv --top 10
```

### Run all operations

```bash
python main.py --all --tag-category Location --tag-value London
```

## CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--list-scans` | | List all completed scans | |
| `--export-assets` | | Export assets filtered by tag | |
| `--export-all` | | Export all assets without filtering | |
| `--asset-info` | | Get asset details by hostname (JSON) | |
| `--top-assets` | | Display top exposed assets | |
| `--all` | | Run all operations | |
| `--tag-category` | | Tag category for filtering | `Location` |
| `--tag-value` | | Tag value for filtering | `London` |
| `--output` | `-o` | Output CSV file path | `assets.csv` |
| `--input` | `-i` | Input CSV for analysis | `assets.csv` |
| `--top` | | Number of top assets | `5` |

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

## Script Explanations

### 1. Authentication (`get_client`)

We use `TenableIO`. Even though the product is Tenable One, the underlying API endpoints for Vulnerability Management are hosted on the `cloud.tenable.com` infrastructure used by Tenable VM. The pyTenable library handles the `X-ApiKeys` header generation automatically.

### 2. Listing Scans (`list_successful_scans`)

We use `tio.scans.list()`. This endpoint retrieves scan definitions. We loop through them and check if `scan.get('status') == 'completed'` to ensure we only report successful runs, filtering out `aborted`, `running`, or `pending` scans.

### 3. Asset Export (`export_assets_by_tag`)

This is the most critical part. Instead of listing assets page-by-page (which is slow and rate-limited), we use the Export API:

- **`tio.exports.assets()`**: This initiates an asynchronous job on the Tenable cloud.
- **Filtering**: We pass `tags=[(Category, Value)]` to the export function. Tenable filters the data server-side before sending it to us.
- **Pandas**: We load the results into a Pandas DataFrame. This makes saving to CSV (`df.to_csv`) and sorting data significantly easier than writing raw file handlers.

### 4. Export All Assets (`export_all_assets`)

Calls `tio.exports.assets()` without any filters to export the entire asset inventory. Useful for full inventory reports or when you need all assets regardless of tags.

### 5. Asset Info Lookup (`get_asset_info`)

- Uses `tio.assets.list()` to search for an asset by hostname (case-insensitive match)
- Once found, retrieves full details via `tio.assets.details(uuid)`
- Outputs human-friendly JSON with key fields: IP addresses, OS, AES/ACR scores, first/last seen dates, tags, etc.

### 6. Top Assets by AES (`get_top_exposed_assets`)

- **AES (Asset Exposure Score)**: In the API JSON response, this field is usually mapped to `exposure_score` (ranges from 0-1000).
- We cast this column to numeric (handling any potential nulls) and use `df.sort_values(ascending=False)` to put the riskiest assets at the top.

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
$ python main.py --export-assets --tag-category tom --tag-value 'linux servers'

--- Asset Export (Tag: tom:linux servers) ---
Export job started, downloading data...
113 assets exported to 'assets.csv'
```

**CSV Output Structure:**

```
$ head -3 assets.csv

id,ipv4,hostname,os,exposure_score,acr_score,tags
0521d598-94bf-407b-9c21-af96a4732277,192.168.1.41,websvr.labnet.local,Unknown,620.0,5.0,"[{'key': 'tom', 'value': 'linux servers', ...}]"
091f3255-d7a1-4b5b-8a00-6ee6a03e3f63,192.168.1.70,win-2019,Unknown,773.0,6.0,"[{'key': 'tom', 'value': 'linux servers', ...}]"
```

| Column | Description |
|--------|-------------|
| `id` | Tenable asset UUID |
| `ipv4` | Primary IPv4 address |
| `hostname` | Asset hostname |
| `os` | Operating system |
| `exposure_score` | AES score (0-1000) |
| `acr_score` | Asset Criticality Rating |
| `tags` | Associated Tenable tags |

### Asset Info

```
$ python main.py --asset-info win-2019

--- Asset Info: win-2019 ---
{
  "Asset ID": "091f3255-d7a1-4b5b-8a00-6ee6a03e3f63",
  "Hostname": "win-2019",
  "FQDN": "win-2019.labnet.local",
  "IPv4 Addresses": ["192.168.1.70"],
  "IPv6 Addresses": [],
  "MAC Addresses": ["00:50:56:92:6f:96"],
  "Operating System": "Windows Server 2019",
  "System Type": ["eng. station"],
  "Network": "Default",
  "Exposure Score (AES)": 773,
  "ACR Score": 6,
  "First Seen": "2025-05-07T01:04:00.000Z",
  "Last Seen": "2026-02-01T08:50:00.000Z",
  "Last Authenticated Scan": "2026-01-15T10:30:00.000Z",
  "Last Licensed Scan": "2026-02-01T08:50:00.000Z",
  "Has Agent": false,
  "Agent Name": [],
  "Sources": ["NESSUS_SCAN"],
  "Tags": [
    "OS:Windows Server",
    "Software:Mcafee Agent Missing",
    "OS:Windows"
  ]
}
```

### Top Exposed Assets

```
$ python main.py --top-assets --top 10

Loaded 113 assets from 'assets.csv'

--- Top 10 Most Exposed Assets (AES) ---
AES        | IP Address      | Hostname
--------------------------------------------------
836        | 192.168.1.28    | win-vuln-email
835        | 192.168.1.14    | win-exchange
773        | 192.168.1.26    | prod-bigfix
773        | 192.168.1.70    | win-2019
773        | 192.168.1.43    | vistax64
773        | 192.168.1.55    | winxpro
773        | 192.168.1.64    | win-sql2012
772        | 192.168.1.82    | winxp-nonhacked
771        | 192.168.1.56    | win2k
755        | 192.168.1.110   | svr-sharepoint
```

## License

MIT
