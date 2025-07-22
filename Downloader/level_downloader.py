#!/usr/bin/env python3
"""
Gravity Defied Levels Downloader
Downloads all available MRG level files from gdtr.net
"""

import requests
import json
import time
import os
from pathlib import Path
from typing import List, Dict, Any
import argparse


class GDLevelsDownloader:
    """Downloads Gravity Defied levels from gdtr.net"""

    def __init__(self, output_dir: str = "levels"):
        self.api_url = "http://gdtr.net/api.php"
        self.mrg_url_template = "http://gdtr.net/mrg/{}.mrg"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Request headers to look like the mobile app
        self.headers = {
            'User-Agent': 'GravityDefied/1.1.1 (Android)',
            'Accept': 'application/json'
        }

    def get_levels_list(self, offset: int = 0, limit: int = 100, sort: str = "popular") -> Dict[str, Any]:
        """Get list of levels from the API"""
        # Try different API formats
        api_formats = [
            # Format 1: Based on Android app code
            {
                'action': 'getLevels',
                'offset': offset,
                'limit': limit,
                'sort': sort
            },
            # Format 2: Try without method parameter
            {
                'offset': offset,
                'limit': limit,
                'sort': sort
            },
            # Format 3: Try POST request
            None  # Will trigger POST request
        ]

        for i, params in enumerate(api_formats):
            try:
                if params is None:
                    # Try POST request
                    data = {
                        'action': 'getLevels',
                        'offset': offset,
                        'limit': limit,
                        'sort': sort
                    }
                    response = requests.post(self.api_url, data=data, headers=self.headers, timeout=30)
                else:
                    response = requests.get(self.api_url, params=params, headers=self.headers, timeout=30)

                print(f"  Trying API format {i + 1}: {response.status_code}")
                print(f"  URL: {response.url}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"  Success! Got JSON response")
                        return result
                    except json.JSONDecodeError:
                        print(f"  Got response but not JSON: {response.text[:200]}")
                        continue
                else:
                    print(f"  HTTP {response.status_code}: {response.text[:200]}")

            except requests.exceptions.RequestException as e:
                print(f"  Request error: {e}")
                continue

    def scrape_levels_from_website(self) -> List[Dict[str, Any]]:
        """Fallback: scrape level IDs from the website"""
        print("Trying to scrape levels from website...")

        levels = []
        base_url = "https://gdtr.net/levels/"

        try:
            # Try to get the levels page
            response = requests.get(base_url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # Look for level URLs in the HTML
            import re
            level_pattern = r'/level/(\d+)/'
            matches = re.findall(level_pattern, response.text)

            # Remove duplicates and convert to int
            level_ids = list(set(int(match) for match in matches))
            level_ids.sort(reverse=True)  # Newest first

            print(f"Found {len(level_ids)} level IDs from website scraping")

            # Create basic level info
            for level_id in level_ids:
                levels.append({
                    'id': level_id,
                    'name': f'Level_{level_id}',
                    'author': 'Unknown'
                })

            return levels

        except Exception as e:
            print(f"Website scraping failed: {e}")
            return []

    def download_mrg_file(self, level_id: int, filename: str = None) -> bool:
        """Download a single MRG file"""
        if filename is None:
            filename = f"{level_id}.mrg"

        file_path = self.output_dir / filename

        # Skip if already exists
        if file_path.exists():
            print(f"  Already exists: {filename}")
            return True

        url = self.mrg_url_template.format(level_id)

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # Save the file
            with open(file_path, 'wb') as f:
                f.write(response.content)

            print(f"  Downloaded: {filename} ({len(response.content)} bytes)")
            return True

        except requests.exceptions.RequestException as e:
            print(f"  Failed to download {filename}: {e}")
            return False

    def download_all_levels(self, max_levels: int = None, sort: str = "popular", delay: float = 0.5):
        """Download all available levels"""
        print(f"Starting download to: {self.output_dir.absolute()}")
        print(f"Sort order: {sort}")

        offset = 0
        limit = 100
        total_downloaded = 0
        total_failed = 0

        # Create metadata file to track downloads
        metadata_file = self.output_dir / "levels_metadata.json"
        all_metadata = []

        while True:
            print(f"\nFetching levels batch (offset={offset}, limit={limit})...")

            # Get levels list from API
            api_response = self.get_levels_list(offset, limit, sort)

            if not api_response or 'data' not in api_response:
                print("API failed, trying website scraping...")

                # Fallback to website scraping
                if offset == 0:  # Only try scraping once
                    scraped_levels = self.scrape_levels_from_website()
                    if scraped_levels:
                        levels_data = scraped_levels
                        print(f"Using scraped data: {len(levels_data)} levels")
                    else:
                        print("No more levels found or API error.")
                        break
                else:
                    print("No more levels found or API error.")
                    break
            else:
                levels_data = api_response['data']

            if not levels_data:
                print("No levels in this batch.")
                break

            print(f"Found {len(levels_data)} levels in this batch")

            # Download each level
            for level_info in levels_data:
                if max_levels and total_downloaded >= max_levels:
                    print(f"\nReached maximum limit of {max_levels} levels.")
                    break

                level_id = level_info.get('id') or level_info.get('api_id')
                name = level_info.get('name', f'Unknown_{level_id}')
                author = level_info.get('author', 'Unknown')

                if not level_id:
                    print(f"  Skipping level with no ID: {level_info}")
                    continue

                print(f"Downloading: {name} by {author} (ID: {level_id})")

                # Try different filename formats
                filename = f"{level_id}.mrg"
                success = self.download_mrg_file(level_id, filename)

                if success:
                    total_downloaded += 1
                    # Store metadata
                    metadata = {
                        'id': level_id,
                        'name': name,
                        'author': author,
                        'filename': filename,
                        **level_info  # Include all original data
                    }
                    all_metadata.append(metadata)
                else:
                    total_failed += 1

                # Rate limiting
                if delay > 0:
                    time.sleep(delay)

            # Check if we should continue (only for API mode, not scraping)
            if max_levels and total_downloaded >= max_levels:
                break

            # If we used scraping, we got all levels at once
            if 'scraped_levels' in locals():
                break

            if len(levels_data) < limit:
                print("Reached end of available levels.")
                break

            offset += limit

        # Save metadata
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(all_metadata, f, indent=2, ensure_ascii=False)

        print(f"\n" + "=" * 50)
        print(f"Download complete!")
        print(f"Total downloaded: {total_downloaded}")
        print(f"Total failed: {total_failed}")
        print(f"Files saved to: {self.output_dir.absolute()}")
        print(f"Metadata saved to: {metadata_file}")

        return total_downloaded, total_failed


def main():
    parser = argparse.ArgumentParser(description='Download Gravity Defied levels')
    parser.add_argument('--output', '-o', default='levels',
                        help='Output directory for MRG files (default: levels)')
    parser.add_argument('--max', '-m', type=int,
                        help='Maximum number of levels to download')
    parser.add_argument('--sort', '-s', default='popular',
                        choices=['popular', 'recent', 'oldest', 'tracks'],
                        help='Sort order (default: popular)')
    parser.add_argument('--delay', '-d', type=float, default=0.5,
                        help='Delay between downloads in seconds (default: 0.5)')

    args = parser.parse_args()

    downloader = GDLevelsDownloader(args.output)

    try:
        downloader.download_all_levels(
            max_levels=args.max,
            sort=args.sort,
            delay=args.delay
        )
    except KeyboardInterrupt:
        print("\nDownload interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")


if __name__ == "__main__":
    main()