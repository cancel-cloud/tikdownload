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
python tiktok_downloader_v2.py
```

Enter the path to your URLs file when prompted.

## 📁 Scripts Overview

### `tiktok_downloader_v2.py` (Recommended)
The enhanced downloader with modern TikTok support:
- **Input**: Text file with URLs (one per line)
- **Features**: Video + slideshow support, robust error handling
- **Output**: `downloads-DD-MM-YYYY/` folder with organized content

### `convert_csv_to_txt.py`
Utility to convert existing CSV files to the new TXT format:
```bash
python convert_csv_to_txt.py your_file.csv
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

### Resume Interrupted Downloads
The downloader automatically detects incomplete downloads:
```
🔄 Resume from line 47? (y/n): y
```

### Custom Output Locations
Modify the `output_folder` variable in the script:
```python
output_folder = f"my_downloads-{date_str}"
```

### Batch Processing
Process multiple URL files:
```bash
for file in *.txt; do
    echo "Processing $file..."
    python tiktok_downloader_v2.py < <(echo "$file")
done
```

## 🔧 Troubleshooting

### Common Issues

**⚠️ TikTok Photo Slideshows Not Working**
- **Issue**: TikTok changed their architecture - photo content loads dynamically
- **Status**: `/photo/` URLs have limited support
- **Workaround**: Focus on video URLs which work reliably
- **Alternative**: Use TikTok's native save feature or browser screenshots

**Environment Issues**
- **Conda users**: Always activate environment first: `conda activate tiktokdownloader`
- **Python not found**: Use `python` instead of `python3` in conda environments
- **Path issues**: Run scripts from the project directory

**"Could not find JSON data in page"**
- TikTok may have changed their page structure
- Try waiting a few minutes and retry
- Check if the URL is accessible in your browser

**"Brotli decompression failed"**
- Fixed in v2 by excluding brotli encoding
- If you see this error, update to the latest version

**"Video download failed, trying slideshow..."**
- Normal behavior - the script automatically tries alternative methods
- Some URLs may be geo-restricted or require login

**Rate Limiting**
- Add delays between downloads if you get blocked:
```python
time.sleep(2)  # Add after each download
```

### Debug Mode
For detailed debugging, save HTML content:
```python
# In extract_slideshow_images(), uncomment:
with open('debug.html', 'w') as f:
    f.write(html_content)
```

## 🔄 Migration from Old Scripts

### From CSV to TXT Format
```bash
python convert_csv_to_txt.py your_old_file.csv
# Creates: your_old_file_urls.txt
```

### From German to English Interface
The new script uses English interface but maintains all functionality:
- Progress saving ✓
- Error logging ✓  
- Metadata extraction ✓
- Resume capability ✓

## 📋 URL Types Supported

- ✅ **Videos**: `tiktok.com/@user/video/123` (Full support)
- ⚠️ **Photo Slideshows**: `tiktok.com/@user/photo/123` (Limited support due to TikTok changes)
- ❌ **Tag Pages**: `tiktok.com/tag/viral` (Automatically skipped)
- ❌ **User Profiles**: `tiktok.com/@user` (Automatically skipped)
- ❌ **Music Pages**: `tiktok.com/music/song-123` (Automatically skipped)

## 🤝 Contributing

The codebase is modular and extensible:
- Add new JSON extraction patterns in `extract_slideshow_images()`
- Extend URL validation in `validate_tiktok_url()`
- Add new output formats in the download methods

## 📜 License

See `LICENSE` file for details.

---

**Note**: This tool is for personal use only. Respect TikTok's terms of service and content creators' rights.
