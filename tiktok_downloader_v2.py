#!/usr/bin/env python3
"""
Enhanced TikTok Downloader v2
Supports both video and photo slideshow downloads with robust error handling.
"""

import os
import sys
import json
import re
import time
import signal
import csv
import datetime
import requests
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Optional, Tuple
import yt_dlp
from bs4 import BeautifulSoup

# Global stop flag for graceful interruption
stop_requested = False

def signal_handler(signum, frame):
    global stop_requested
    stop_requested = True
    print("\n⚠️  Interrupt received. Finishing current download and saving progress...")

signal.signal(signal.SIGINT, signal_handler)

class TikTokDownloader:
    def __init__(self, output_folder: str):
        self.output_folder = output_folder
        self.session = requests.Session()
        self.setup_session()
        
        # Tracking
        self.downloaded_count = 0
        self.error_count = 0
        self.skipped_count = 0
        
        # Files for logging
        self.error_file = None
        self.progress_file = os.path.join(output_folder, "progress.txt")
        self.metadata_file = os.path.join(output_folder, "metadata.csv")
        self.skipped_file = os.path.join(output_folder, "skipped_links.txt")
        
    def setup_session(self):
        """Configure session with optimal headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',  # Exclude brotli to avoid decompression issues
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })

    def sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filenames"""
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
        return sanitized.strip().replace(" ", "_")[:200]  # Limit length

    def validate_tiktok_url(self, url: str) -> Tuple[bool, str]:
        """Validate and classify TikTok URLs"""
        url = url.strip()
        
        # Remove common prefixes
        if url.startswith('@'):
            url = url[1:]
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Check if it's a valid TikTok URL
        if 'tiktok.com' not in url.lower():
            return False, "Not a TikTok URL"
            
        # Classify URL type
        if '/video/' in url:
            return True, "video"
        elif '/photo/' in url:
            return True, "photo"
        elif any(tag in url for tag in ['/tag/', '/music/', '/effect/', '/challenge/']):
            return False, "Tag/music/effect page (not downloadable content)"
        elif '/@' in url and '/video/' not in url and '/photo/' not in url:
            return False, "User profile page (not specific content)"
        else:
            # Try to determine if it's a valid content URL
            return True, "unknown"

    def extract_slideshow_images(self, url: str) -> List[str]:
        """Extract image URLs from TikTok photo slideshow"""
        print(f"🖼️  Extracting slideshow images from: {url}")
        
        try:
            # Get the page content
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            html_content = response.text
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Try multiple methods to find JSON data
            json_data = None
            
            # Method 1: SIGI_STATE script tag
            sigi_script = soup.find('script', {'id': 'SIGI_STATE'})
            if sigi_script:
                try:
                    json_data = json.loads(sigi_script.string)
                    print("✓ Found data in SIGI_STATE")
                except json.JSONDecodeError:
                    pass
            
            # Method 2: __UNIVERSAL_DATA_FOR_REHYDRATION__ script tag
            if not json_data:
                universal_script = soup.find('script', {'id': '__UNIVERSAL_DATA_FOR_REHYDRATION__'})
                if universal_script:
                    try:
                        json_data = json.loads(universal_script.string)
                        print("✓ Found data in __UNIVERSAL_DATA_FOR_REHYDRATION__")
                    except json.JSONDecodeError:
                        pass
            
            # Method 3: Search for JSON in all script tags
            if not json_data:
                for script in soup.find_all('script'):
                    if script.string and len(script.string) > 1000:
                        text = script.string.strip()
                        if text.startswith('{') and 'imagePost' in text:
                            try:
                                json_data = json.loads(text)
                                print("✓ Found JSON data in script tag")
                                break
                            except json.JSONDecodeError:
                                continue
            
            if not json_data:
                raise ValueError("Could not find JSON data in page")
            
            # Search for images in the JSON structure
            image_urls = []
            
            def find_images_recursive(obj, path=""):
                if isinstance(obj, dict):
                    # Look for common image array keys
                    for key in ['images', 'imagePost', 'urlList', 'imageURL', 'imageUrls']:
                        if key in obj:
                            images = obj[key]
                            if isinstance(images, list):
                                for img in images:
                                    if isinstance(img, str) and img.startswith('http'):
                                        image_urls.append(img)
                                    elif isinstance(img, dict) and 'url' in img:
                                        image_urls.append(img['url'])
                                    elif isinstance(img, dict) and 'urlList' in img:
                                        if isinstance(img['urlList'], list):
                                            image_urls.extend([u for u in img['urlList'] if isinstance(u, str) and u.startswith('http')])
                    
                    # Recursively search nested objects
                    for key, value in obj.items():
                        find_images_recursive(value, f"{path}.{key}")
                        
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        find_images_recursive(item, f"{path}[{i}]")
            
            find_images_recursive(json_data)
            
            # Filter and deduplicate URLs
            valid_urls = []
            seen_urls = set()
            
            for url in image_urls:
                if url not in seen_urls and self.is_valid_image_url(url):
                    valid_urls.append(url)
                    seen_urls.add(url)
            
            print(f"✓ Found {len(valid_urls)} valid image URLs")
            return valid_urls
            
        except Exception as e:
            print(f"❌ Error extracting slideshow images: {e}")
            return []

    def is_valid_image_url(self, url: str) -> bool:
        """Check if URL points to a valid image"""
        if not url.startswith('http'):
            return False
        
        # Check for image extensions or TikTok CDN patterns
        if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif']):
            return True
        
        # TikTok CDN patterns
        if 'tiktokcdn.com' in url.lower() and any(pattern in url for pattern in ['obj/tos', 'img/tos']):
            return True
            
        return False

    def download_image(self, url: str, filename: str) -> bool:
        """Download a single image"""
        try:
            response = self.session.get(url, stream=True, timeout=15)
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            else:
                # Default or guess from URL
                parsed_url = urlparse(url)
                path_ext = os.path.splitext(parsed_url.path)[1]
                ext = path_ext if path_ext in ['.jpg', '.jpeg', '.png', '.webp', '.avif'] else '.jpg'
            
            file_path = os.path.join(self.output_folder, f"{filename}{ext}")
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"  ✓ Downloaded: {os.path.basename(file_path)}")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to download image: {e}")
            return False

    def download_slideshow(self, url: str, title: str = "") -> bool:
        """Download all images from a TikTok photo slideshow"""
        print(f"\n📸 Downloading slideshow: {title or 'Untitled'}")
        
        image_urls = self.extract_slideshow_images(url)
        
        if not image_urls:
            print("❌ No images found in slideshow")
            return False
        
        # Create subfolder for slideshow
        safe_title = self.sanitize_filename(title or f"slideshow_{int(time.time())}")
        slideshow_folder = os.path.join(self.output_folder, safe_title)
        os.makedirs(slideshow_folder, exist_ok=True)
        
        success_count = 0
        for i, img_url in enumerate(image_urls, 1):
            filename = f"{safe_title}_img_{i:02d}"
            if self.download_image(img_url, os.path.join(safe_title, f"img_{i:02d}")):
                success_count += 1
            
            if stop_requested:
                break
        
        print(f"✓ Downloaded {success_count}/{len(image_urls)} images from slideshow")
        return success_count > 0

    def download_video(self, url: str) -> Optional[Dict]:
        """Download video using yt-dlp"""
        print(f"\n🎥 Downloading video from: {url}")
        
        ydl_opts = {
            'outtmpl': os.path.join(self.output_folder, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                print(f"✓ Downloaded video: {info.get('title', 'Unknown')}")
                return info
        except Exception as e:
            print(f"❌ Failed to download video: {e}")
            return None

    def process_url(self, url: str, line_number: int) -> bool:
        """Process a single URL (video or slideshow)"""
        global stop_requested
        
        if stop_requested:
            return False
        
        # Validate URL
        is_valid, url_type = self.validate_tiktok_url(url)
        
        if not is_valid:
            print(f"⏭️  Skipping line {line_number}: {url_type}")
            with open(self.skipped_file, 'a', encoding='utf-8') as f:
                f.write(f"Line {line_number}: {url} - {url_type}\n")
            self.skipped_count += 1
            return True
        
        print(f"\n📋 Processing line {line_number}: {url}")
        
        try:
            if url_type == "photo":
                # Use slideshow downloader
                success = self.download_slideshow(url)
            else:
                # Try video download first
                info = self.download_video(url)
                if info:
                    success = True
                    # Save metadata
                    self.save_metadata(line_number, url, info)
                else:
                    # Fallback to slideshow if video fails
                    print("🔄 Video download failed, trying slideshow...")
                    success = self.download_slideshow(url)
            
            if success:
                self.downloaded_count += 1
                return True
            else:
                self.error_count += 1
                self.log_error(line_number, url, "Download failed")
                return False
                
        except Exception as e:
            print(f"❌ Error processing {url}: {e}")
            self.error_count += 1
            self.log_error(line_number, url, str(e))
            return False

    def save_metadata(self, line_number: int, url: str, info: Dict):
        """Save video metadata"""
        metadata = {
            'line': line_number,
            'url': url,
            'id': info.get('id', ''),
            'title': info.get('title', ''),
            'uploader': info.get('uploader', ''),
            'duration': info.get('duration', ''),
            'view_count': info.get('view_count', ''),
            'filename': f"{info.get('id', '')}.{info.get('ext', '')}"
        }
        
        # Write to CSV
        file_exists = os.path.exists(self.metadata_file)
        with open(self.metadata_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=metadata.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(metadata)

    def log_error(self, line_number: int, url: str, error: str):
        """Log download errors"""
        if not self.error_file:
            error_path = os.path.join(self.output_folder, "download_errors.csv")
            self.error_file = open(error_path, 'w', newline='', encoding='utf-8')
            error_writer = csv.writer(self.error_file)
            error_writer.writerow(['line', 'url', 'error', 'timestamp'])
        
        error_writer = csv.writer(self.error_file)
        error_writer.writerow([line_number, url, error, datetime.datetime.now().isoformat()])
        self.error_file.flush()

    def save_progress(self, line_number: int):
        """Save current progress"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            f.write(str(line_number))

    def load_progress(self) -> int:
        """Load saved progress"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return int(f.read().strip())
            except:
                return 0
        return 0

    def close(self):
        """Clean up resources"""
        if self.error_file:
            self.error_file.close()

    def rename_files_from_metadata(self):
        """Renames downloaded video files based on metadata.csv."""
        if not os.path.exists(self.metadata_file):
            print("\nℹ️  metadata.csv not found, skipping renaming.")
            return

        print("\nRenaming files...")
        renamed_count = 0
        rename_errors = 0
        
        try:
            with open(self.metadata_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                videos_to_rename = list(reader)
                
            for row in videos_to_rename:
                original_filename = row.get('filename')
                video_title = row.get('title')

                if not original_filename or not video_title:
                    continue

                if video_title.startswith('#'):
                    video_title = video_title[1:].lstrip()

                old_path = os.path.join(self.output_folder, original_filename)
                if os.path.exists(old_path) and os.path.isfile(old_path):
                    try:
                        file_ext = os.path.splitext(original_filename)[1]
                        sanitized_title = self.sanitize_filename(video_title)

                        if not sanitized_title:
                            print(f"  ⚠️  Skipping rename for '{original_filename}' due to empty title after sanitizing.")
                            continue

                        new_filename = f"{sanitized_title}{file_ext}"
                        new_path = os.path.join(self.output_folder, new_filename)
                        
                        if old_path == new_path:
                            continue

                        if os.path.exists(new_path):
                            print(f"  ⚠️  Skipping rename: '{new_filename}' already exists.")
                            continue
                            
                        os.rename(old_path, new_path)
                        print(f"  ✓ Renamed '{original_filename}' to '{new_filename}'")
                        renamed_count += 1
                    except Exception as e:
                        print(f"  ❌ Error renaming '{original_filename}': {e}")
                        rename_errors += 1
        except Exception as e:
            print(f"❌ Error reading metadata file for renaming: {e}")

        print(f"\n✅ Renaming complete. {renamed_count} files renamed, {rename_errors} errors.")

def load_urls_from_file(file_path: str) -> List[str]:
    """Load URLs from text file"""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    urls.append(line)
        return urls
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {e}")
        return []

def main():
    print("🚀 Enhanced TikTok Downloader v2")
    print("=" * 50)
    
    # Basic argument parsing
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    flags = [arg for arg in sys.argv[1:] if arg.startswith('--')]

    input_file = ""
    rename_files = '--no-rename' not in flags

    try:
        if args:
            input_file = args[0]
            print(f"📁 Using URLs file: {input_file}")
        else:
            input_file = input("📁 Enter path to URLs file (txt): ").strip()
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user. Exiting.")
        sys.exit(0)

    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        sys.exit(1)
    
    # Create output folder
    date_str = datetime.datetime.now().strftime("%d-%m-%Y")
    output_folder = f"downloads-{date_str}"
    os.makedirs(output_folder, exist_ok=True)
    print(f"📂 Output folder: {output_folder}")
    
    # Load URLs
    urls = load_urls_from_file(input_file)
    if not urls:
        print("❌ No valid URLs found in file")
        sys.exit(1)
    
    print(f"📋 Found {len(urls)} URLs to process")
    
    # Initialize downloader
    downloader = TikTokDownloader(output_folder)
    
    # Check for resume
    resume_line = downloader.load_progress()
    if resume_line > 0:
        response = input(f"🔄 Resume from line {resume_line + 1}? (y/n): ").strip().lower()
        if response != 'y':
            resume_line = 0
    
    try:
        start_time = time.time()
        
        for i, url in enumerate(urls, 1):
            if i <= resume_line:
                continue
                
            downloader.process_url(url, i)
            downloader.save_progress(i)
            
            if stop_requested:
                print("\n⚠️  Download interrupted by user")
                break
        
        # Summary
        elapsed = time.time() - start_time
        print(f"\n📊 Download Summary")
        print(f"Time elapsed: {elapsed:.1f} seconds")
        print(f"✅ Downloaded: {downloader.downloaded_count}")
        print(f"❌ Errors: {downloader.error_count}")
        print(f"⏭️  Skipped: {downloader.skipped_count}")
        
        if not stop_requested:
            # Clean up progress file on successful completion
            if os.path.exists(downloader.progress_file):
                os.remove(downloader.progress_file)
            print("✅ Download completed!")
            
            # Conditionally rename files
            if rename_files:
                downloader.rename_files_from_metadata()
            else:
                print("\n⏭️  Skipping file renaming as per --no-rename flag.")
        
    except KeyboardInterrupt:
        print("\n⚠️  Download interrupted")
    finally:
        downloader.close()

if __name__ == "__main__":
    main() 