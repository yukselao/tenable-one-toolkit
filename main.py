#!/usr/bin/env python3
"""
Tenable One Asset Analysis Tool

A CLI tool for interacting with Tenable One API to list scans,
export assets, and analyze exposure scores.

Usage:
    python main.py --list-scans
    python main.py --export-assets --tag-category Location --tag-value London
    python main.py --export-all -o all_assets.parquet
    python main.py --asset-info win-2019 -i all_assets.parquet
    python main.py --plugin-info 10114
    python main.py --search-assets 192.168.1 -i all_assets.parquet
    python main.py --top-assets -i all_assets.parquet
"""

import argparse
from dotenv import load_dotenv
from modules.helper import (
    get_client,
    list_successful_scans,
    export_assets_by_tag,
    export_all_assets,
    get_asset_info,
    get_plugin_info,
    search_assets,
    get_top_exposed_assets,
    load_dataframe,
    convert_to_csv,
    convert_to_json
)

# Load environment variables from .env file
load_dotenv()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Tenable One Asset Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python main.py --list-scans
  python main.py --export-all -o all_assets.parquet
  python main.py --export-assets --tag-category OS --tag-value Linux -o linux.parquet
  python main.py --asset-info se-dc1 -i all_assets.parquet
  python main.py --search-assets 192.168.15 -i all_assets.parquet
  python main.py --plugin-info 10114
  python main.py --top-assets -i all_assets.parquet --top 10
  python main.py --to-csv -i all_assets.parquet
  python main.py --to-json -i all_assets.parquet -o assets.json
        '''
    )

    # Command options
    parser.add_argument(
        '--list-scans',
        action='store_true',
        help='List all completed scans'
    )

    parser.add_argument(
        '--export-assets',
        action='store_true',
        help='Export assets filtered by tag'
    )

    parser.add_argument(
        '--export-all',
        action='store_true',
        help='Export all assets without tag filtering'
    )

    parser.add_argument(
        '--asset-info',
        type=str,
        metavar='HOSTNAME',
        help='Get detailed asset info by hostname (JSON output)'
    )

    parser.add_argument(
        '--plugin-info',
        type=int,
        metavar='PLUGIN_ID',
        help='Get plugin details and affected assets (JSON output)'
    )

    parser.add_argument(
        '--search-assets',
        type=str,
        metavar='QUERY',
        help='Search assets by IP address or hostname'
    )

    parser.add_argument(
        '--top-assets',
        action='store_true',
        help='Display top exposed assets by AES score'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all operations (list-scans, export-assets, top-assets)'
    )

    parser.add_argument(
        '--to-csv',
        action='store_true',
        help='Convert input file to CSV format'
    )

    parser.add_argument(
        '--to-json',
        action='store_true',
        help='Convert input file to JSON format'
    )

    # Export parameters
    parser.add_argument(
        '--tag-category',
        type=str,
        default='Location',
        help='Tag category for filtering assets (default: Location)'
    )

    parser.add_argument(
        '--tag-value',
        type=str,
        default='London',
        help='Tag value for filtering assets (default: London)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='assets.parquet',
        help='Output file path (default: assets.parquet)'
    )

    # Input file parameter
    parser.add_argument(
        '-i', '--input',
        type=str,
        default='assets.parquet',
        help='Input file for analysis (default: assets.parquet)'
    )

    parser.add_argument(
        '--top',
        type=int,
        default=5,
        help='Number of top assets to display (default: 5)'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Show help if no command specified
    has_command = any([
        args.list_scans,
        args.export_assets,
        args.export_all,
        args.asset_info,
        args.plugin_info,
        args.search_assets,
        args.top_assets,
        args.all,
        args.to_csv,
        args.to_json
    ])

    if not has_command:
        print("No command specified. Use --help for usage information.")
        return

    # Initialize client only when needed
    tio = None
    needs_client = any([
        args.list_scans,
        args.export_assets,
        args.export_all,
        args.asset_info,
        args.plugin_info,
        args.search_assets,
        args.all
    ])

    if needs_client:
        tio = get_client()

    # Execute commands
    df_assets = None

    if args.list_scans or args.all:
        list_successful_scans(tio)

    if args.export_all:
        df_assets = export_all_assets(tio, args.output)

    elif args.export_assets or args.all:
        df_assets = export_assets_by_tag(
            tio,
            args.tag_category,
            args.tag_value,
            args.output
        )

    if args.asset_info:
        get_asset_info(tio, args.asset_info, args.input)

    if args.plugin_info:
        get_plugin_info(tio, args.plugin_info)

    if args.search_assets:
        search_assets(tio, args.search_assets, args.input)

    if args.top_assets or args.all:
        if df_assets is None:
            # Load from file if not already in memory
            try:
                df_assets = load_dataframe(args.input)
                print(f"\nLoaded {len(df_assets)} assets from '{args.input}'")
            except FileNotFoundError:
                print(f"Error: File '{args.input}' not found. Run --export-all first.")
                return

        get_top_exposed_assets(df_assets, args.top)

    # File conversion commands (no API needed)
    if args.to_csv:
        convert_to_csv(args.input, args.output if args.output != 'assets.parquet' else None)

    if args.to_json:
        convert_to_json(args.input, args.output if args.output != 'assets.parquet' else None)


if __name__ == "__main__":
    main()
