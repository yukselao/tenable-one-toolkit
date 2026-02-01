# Tenable One Asset Analysis Tool

A CLI tool for interacting with the Tenable One API to list scans, export assets by tags, and analyze asset exposure scores (AES).

## Features

- List all successful (completed) VM scans
- Export assets filtered by tag category and value to CSV
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

### 4. Top Assets by AES (`get_top_exposed_assets`)

- **AES (Asset Exposure Score)**: In the API JSON response, this field is usually mapped to `exposure_score` (ranges from 0-1000).
- We cast this column to numeric (handling any potential nulls) and use `df.sort_values(ascending=False)` to put the riskiest assets at the top.

## Output Example

```
$ python main.py --all --tag-category Location --tag-value London

--- Successful VM Scans ---
Scan ID    | Status          | Scan Name
------------------------------------------------------------
12345      | completed       | Weekly Network Scan
12346      | completed       | Monthly Full Scan

Total Successful Scans: 2

--- Asset Export (Tag: Location:London) ---
Export job started, downloading data...
150 assets exported to 'assets.csv'

--- Top 5 Most Exposed Assets (AES) ---
AES        | IP Address      | Hostname
--------------------------------------------------
850        | 192.168.1.10    | server-prod-01
720        | 192.168.1.15    | db-primary
680        | 192.168.1.20    | web-frontend
550        | 192.168.1.25    | api-gateway
490        | 192.168.1.30    | cache-server
```

## License

MIT
