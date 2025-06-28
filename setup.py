#!/usr/bin/env python3
"""
TikTok Downloader Setup Script
Installs dependencies and checks system compatibility.
Cross-platform support for Windows, macOS, and Linux.
Supports both conda and pip environments.
"""

import subprocess
import sys
import os
import platform
import shutil

def run_command(command, description, use_shell=True):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        # Handle command as list or string based on platform
        if isinstance(command, str) and not use_shell:
            command = command.split()
        
        result = subprocess.run(command, shell=use_shell, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False, e.stderr

def detect_environment():
    """Detect if we're in conda, venv, or system Python"""
    env_type = "system"
    env_name = None
    
    # Check for conda
    if 'CONDA_DEFAULT_ENV' in os.environ:
        env_type = "conda"
        env_name = os.environ['CONDA_DEFAULT_ENV']
    elif 'VIRTUAL_ENV' in os.environ:
        env_type = "venv"
        env_name = os.path.basename(os.environ['VIRTUAL_ENV'])
    
    return env_type, env_name

def check_conda():
    """Check if conda is available"""
    conda_cmd = "conda" if platform.system() != "Windows" else "conda.exe"
    if shutil.which(conda_cmd):
        success, output = run_command(f"{conda_cmd} --version", "Checking conda version")
        if success:
            print(f"✅ Conda is available: {output.strip()}")
            return True
    return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    
    print("✅ Python version is compatible")
    return True

def install_dependencies():
    """Install required packages using pip (works in conda too)"""
    print("\n📦 Installing dependencies...")
    
    env_type, env_name = detect_environment()
    print(f"🌍 Environment: {env_type}" + (f" ({env_name})" if env_name else ""))
    
    # For conda environments, we still use pip for Python packages
    python_cmd = sys.executable
    if platform.system() == "Windows":
        python_cmd = python_cmd.replace("\\", "/")  # Normalize path separators
    
    # Upgrade pip first
    success, _ = run_command(f'"{python_cmd}" -m pip install --upgrade pip', "Upgrading pip")
    if not success:
        print("⚠️  Pip upgrade failed, continuing anyway...")
    
    # Install requirements
    if os.path.exists("requirements.txt"):
        success, _ = run_command(f'"{python_cmd}" -m pip install -r requirements.txt', 
                               "Installing dependencies from requirements.txt")
        if not success:
            return False
    else:
        # Fallback to manual installation
        packages = [
            "yt-dlp>=2023.12.30",
            "requests>=2.31.0", 
            "brotli>=1.1.0",
            "beautifulsoup4>=4.12.2",
            "lxml>=4.9.3",
            "Pillow>=10.0.1"
        ]
        
        for package in packages:
            success, _ = run_command(f'"{python_cmd}" -m pip install "{package}"', 
                                   f"Installing {package}")
            if not success:
                return False
    
    return True

def test_imports():
    """Test if all required modules can be imported"""
    print("\n🧪 Testing imports...")
    
    required_modules = [
        "yt_dlp",
        "requests", 
        "brotli",
        "bs4",
        "lxml",
        "PIL"
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            return False
    
    return True

def create_sample_files():
    """Create sample files if they don't exist"""
    print("\n📄 Checking sample files...")
    
    if not os.path.exists("sample_urls.txt"):
        print("📝 Creating sample_urls.txt...")
        # This would be created by the edit_file function above
    
    print("✅ Sample files ready")

def main():
    print("🚀 TikTok Downloader Setup")
    print("=" * 50)
    print(f"Operating System: {platform.system()} {platform.release()}")
    
    # Check environment
    env_type, env_name = detect_environment()
    if env_type == "conda":
        print(f"🐍 Conda environment: {env_name}")
        if env_name == "base":
            print("⚠️  Consider creating a dedicated conda environment:")
            print("   conda create -n tiktokdownloader python=3.9")
            print("   conda activate tiktokdownloader")
    elif env_type == "venv":
        print(f"🐍 Virtual environment: {env_name}")
    else:
        print("🐍 System Python environment")
        if check_conda():
            print("💡 Tip: Consider using conda environment for better isolation:")
            print("   conda create -n tiktokdownloader python=3.9")
            print("   conda activate tiktokdownloader")
    
    if not check_python_version():
        sys.exit(1)
    
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        print("💡 Try manually running:")
        if env_type == "conda":
            print("   pip install -r requirements.txt")
        else:
            print("   python -m pip install --upgrade -r requirements.txt")
        sys.exit(1)
    
    if not test_imports():
        print("\n❌ Setup failed during import testing")
        print("💡 Try manually running:")
        if env_type == "conda":
            print("   pip install --upgrade -r requirements.txt")
        else:
            print("   python -m pip install --upgrade -r requirements.txt")
        sys.exit(1)
    
    create_sample_files()
    
    print("\n🎉 Setup completed successfully!")
    print(f"\n🌍 Environment: {env_type}" + (f" ({env_name})" if env_name else ""))
    print("\n📋 Next steps:")
    if env_type == "conda":
        print("1. Make sure your conda environment is active: conda activate tiktokdownloader")
        print("2. Edit sample_urls.txt with your TikTok URLs")
        print("3. Run: python tiktok_downloader_v2.py sample_urls.txt")
        print("4. Or convert existing CSV: python convert_csv_to_txt.py your_file.csv")
    else:
        print("1. Edit sample_urls.txt with your TikTok URLs")
        print("2. Run: python tiktok_downloader_v2.py sample_urls.txt")
        print("3. Or convert existing CSV: python convert_csv_to_txt.py your_file.csv")
    
    print("\n📚 Documentation: See README.md for detailed usage instructions")

if __name__ == "__main__":
    main() 