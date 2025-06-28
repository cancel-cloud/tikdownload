# TikTok Downloader Suite

A comprehensive Python toolkit for downloading TikTok videos and photo slideshows with robust error handling and resume capabilities.

## ✨ Features

- **Video Downloads**: Full support for TikTok video content
- **Photo Slideshow Support**: Limited support for photo slideshows (TikTok has changed their architecture)
- **Smart URL Detection**: Automatically detects content type and chooses appropriate downloader
- **Resume Downloads**: Pause and resume large batch downloads
- **Error Logging**: Comprehensive error tracking and reporting
- **Progress Tracking**: Real-time download statistics
- **URL Validation**: Filters out invalid or non-downloadable links
- **Metadata Extraction**: Saves video titles, uploader info, and more
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Conda Support**: Full support for conda environments

## 🚀 Quick Start

### 1. Install Dependencies

#### Option A: Using Conda (Recommended)
```bash
# Create conda environment (if not already created)
conda create -n tiktokdownloader python=3.9

# Activate environment
conda activate tiktokdownloader

# Install dependencies
pip install -r requirements.txt

# Or run automatic setup
python setup.py
```

#### Option B: Using pip (System Python)
```bash
pip install -r requirements.txt

# Or run automatic setup
python setup.py
```

### 2. Quick Setup (Cross-Platform)
```bash
# Run the setup script for automatic installation
python setup.py
```

**Note for conda users:** Always activate your environment before running the downloader:
```bash
conda activate tiktokdownloader
```

### 2. Prepare Your URLs

Create a text file with one TikTok URL per line:

```
https://www.tiktok.com/@username/video/1234567890
https://www.tiktok.com/@username/photo/9876543210
# Comments start with #
https://www.tiktok.com/@another/video/5555555555
```

### 3. Run the Downloader

```bash
# Download and automatically rename files (default)
python tiktok_downloader_v2.py sample_urls.txt

# Download without renaming
python tiktok_downloader_v2.py sample_urls.txt --no-rename

# Run interactively
python tiktok_downloader_v2.py
```

## 📁 Scripts Overview

### `tiktok_downloader_v2.py` (Recommended)
The enhanced downloader with modern TikTok support:
- **Input**: Text file with URLs (one per line)
- **Features**: Video + slideshow support, robust error handling
- **Output**: `downloads-DD-MM-YYYY/` folder with organized content
- **Usage**: `python tiktok_downloader_v2.py [path_to_urls.txt] [--no-rename]`

### `convert_csv_to_txt.py`
Utility to convert existing CSV files to the new TXT format:
- **Usage**: `python convert_csv_to_txt.py [path_to_file.csv]`
```bash
# By providing the file as an argument
python convert_csv_to_txt.py your_file.csv

# Or run it and enter the path when prompted
python convert_csv_to_txt.py
```

### Legacy Scripts
- `tiktokdownloader.py`: Original CSV-based downloader (German interface)
- `bulk_tiktok_downloader.py`: Previous enhanced version
- `imagetesting/imagedownloader.py`: Specialized image downloader

## 🏗️ Architecture

### TikTokDownloader Class
Core functionality with methods for:
- `validate_tiktok_url()`: Smart URL validation and classification
- `extract_slideshow_images()`: Multi-method JSON parsing for slideshows
- `download_video()`: yt-dlp integration for videos
- `download_slideshow()`: Custom slideshow handling
- `process_url()`: Main processing logic with fallbacks

### Session Management
- Optimized headers to avoid compression issues
- Excludes brotli encoding to prevent decompression errors
- Multiple user agent rotation for blocked requests

### Error Handling
- Graceful degradation (video → slideshow fallback)
- Comprehensive error logging with timestamps
- Progress saving for large batches

## 📊 Output Structure

```
downloads-DD-MM-YYYY/
├── videoID.mp4              # Downloaded videos
├── slideshow_title/         # Slideshow folders
│   ├── img_01.jpg
│   ├── img_02.jpg
│   └── ...
├── metadata.csv             # Video metadata
├── download_errors.csv      # Error log
├── skipped_links.txt        # Skipped URLs with reasons
└── progress.txt            # Resume point (auto-deleted on completion)
```

## 🛠️ Advanced Usage

### Command-line Options for `tiktok_downloader_v2.py`
- `[input_file]`: (Optional) Path to your URLs file. If omitted, you will be prompted to enter it.
- `--no-rename`: (Optional) Prevents the script from automatically renaming downloaded videos based on their titles. By default, files are renamed.

### Resume Interrupted Downloads
The downloader automatically detects incomplete downloads:
```