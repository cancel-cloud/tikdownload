#!/usr/bin/env python3
"""
CSV to TXT Converter
Converts existing TikTok CSV files to the new TXT format for the enhanced downloader.
"""

import csv
import sys
import os
from urllib.parse import urlparse

def extract_urls_from_csv(csv_file_path: str, output_file_path: str):
    """Extract URLs from CSV and save to TXT file"""
    urls = []
    skipped_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            # Try tab-delimited first (like your existing files)
            sample = csvfile.read(1024)
            csvfile.seek(0)
            
            delimiter = '\t' if '\t' in sample else ','
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            print(f"📊 CSV columns found: {reader.fieldnames}")
            
            for row_num, row in enumerate(reader, 1):
                for column, value in row.items():
                    if value and isinstance(value, str):
                        # Split by semicolon and extract URLs
                        parts = value.split(';')
                        for part in parts:
                            part = part.strip()
                            if part.startswith('http') and 'tiktok.com' in part:
                                # Extract just the TikTok URL (before any query parameters that might be malformed)
                                url = part.split('?')[0] if '?' in part else part
                                
                                # Basic URL validation
                                try:
                                    parsed = urlparse(url)
                                    if parsed.scheme and parsed.netloc:
                                        if 'tiktok.com' in url.lower():
                                            # Only add video or photo URLs
                                            if '/video/' in url or '/photo/' in url:
                                                urls.append(url)
                                            else:
                                                print(f"⚠️  Skipping non-content URL (row {row_num}): {url[:60]}...")
                                                skipped_count += 1
                                        else:
                                            print(f"⚠️  Skipping non-TikTok URL (row {row_num}): {url[:60]}...")
                                            skipped_count += 1
                                    else:
                                        print(f"⚠️  Invalid URL format (row {row_num}): {url[:60]}...")
                                        skipped_count += 1
                                except Exception:
                                    print(f"⚠️  Malformed URL (row {row_num}): {url[:60]}...")
                                    skipped_count += 1
        
        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in urls:
            if url not in seen:
                unique_urls.append(url)
                seen.add(url)
        
        # Save to TXT file
        with open(output_file_path, 'w', encoding='utf-8') as txtfile:
            txtfile.write("# TikTok URLs extracted from CSV\n")
            txtfile.write(f"# Source: {csv_file_path}\n")
            txtfile.write(f"# Total URLs: {len(unique_urls)}\n\n")
            
            for url in unique_urls:
                txtfile.write(url + '\n')
        
        print(f"✅ Conversion complete!")
        print(f"📊 Stats:")
        print(f"   Total URLs found: {len(urls)}")
        print(f"   Unique URLs: {len(unique_urls)}")
        print(f"   Skipped invalid/non-TikTok: {skipped_count}")
        print(f"📁 Output saved to: {output_file_path}")
        
    except Exception as e:
        print(f"❌ Error processing CSV file: {e}")
        return False
    
    return True

def main():
    print("🔄 CSV to TXT Converter for TikTok Downloader")
    print("=" * 50)
    
    csv_file = ""
    try:
        if len(sys.argv) > 1:
            csv_file = sys.argv[1]
            print(f"📁 Using CSV file: {csv_file}")
        else:
            csv_file = input("📁 Enter path to CSV file: ").strip()
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user. Exiting.")
        sys.exit(0)
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        sys.exit(1)
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(csv_file))[0]
    output_file = f"{base_name}_urls.txt"
    
    # Ask for custom output path if desired
    custom_output = input(f"💾 Output file [default: {output_file}]: ").strip()
    if custom_output:
        output_file = custom_output
    
    success = extract_urls_from_csv(csv_file, output_file)
    
    if success:
        print(f"\n🚀 Ready to use with: python tiktok_downloader_v2.py")
        print(f"   Input file: {output_file}")

if __name__ == "__main__":
    main() 