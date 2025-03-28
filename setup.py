#!/usr/bin/env python3
"""
setup.py - Installs all requirements for the Pocket-Evernote pipeline including Playwright
"""
import os
import sys
import subprocess
import platform

def is_wsl():
    """Detect if running in Windows Subsystem for Linux."""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    except:
        return False

def install_system_dependencies():
    """Install system dependencies for Playwright."""
    if platform.system() != "Linux":
        return
        
    print("Checking system dependencies for Playwright...")
    
    # Special handling for WSL (Windows Subsystem for Linux)
    if is_wsl():
        print("Detected WSL environment - installing WSL-specific dependencies...")
        # For Ubuntu on WSL, we need to install specific packages with t64 suffix
        wsl_dependencies = [
            "libx11-xcb1", "libxcb-dri3-0", "libxcomposite1", "libxcursor1", 
            "libxdamage1", "libxi6", "libxtst6", "libnss3", "libcups2t64", 
            "libxss1", "libxrandr2", "libasound2t64", "libatk1.0-0t64", 
            "libatk-bridge2.0-0t64", "libpango-1.0-0", "libpangocairo-1.0-0", "libgbm1"
        ]
        
        # Install each package separately to avoid errors if one is missing
        for pkg in wsl_dependencies:
            os.system(f"sudo apt-get install -y {pkg}")
            
    else:
        # Standard Linux installation
        print("Installing standard Linux dependencies for Playwright...")
        os.system("sudo apt-get update")
        os.system("sudo apt-get install -y libx11-xcb1 libxcb-dri3-0 libxcomposite1 "
                 "libxcursor1 libxdamage1 libxi6 libxtst6 libnss3 libcups2 libxss1 "
                 "libxrandr2 libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 "
                 "libpangocairo-1.0-0 libgbm1")
    
    # Try the playwright install-deps command as a fallback
    print("Trying playwright install-deps as a fallback...")
    if platform.system() == "Linux":
        os.system("python3 -m playwright install-deps chromium || true")
    else:
        os.system("python -m playwright install-deps chromium || true")

def install_requirements():
    """Install all requirements for the Pocket-Evernote pipeline."""
    print("Installing Python dependencies...")
    
    # Determine the correct pip command
    pip_cmd = "pip"
    if platform.system() == "Linux":
        # Try pip3 on Linux
        pip_cmd = "pip3" if os.system("which pip3 > /dev/null 2>&1") == 0 else "pip"
    
    # Install requirements
    result = os.system(f"{pip_cmd} install -r requirements.txt")
    if result != 0:
        print(f"Error installing dependencies with {pip_cmd}. Trying with python -m pip...")
        # Try with python module if direct pip fails
        if platform.system() == "Linux":
            os.system("python3 -m pip install -r requirements.txt")
        else:
            os.system("python -m pip install -r requirements.txt")
    
    # Check if playwright is installed
    try:
        import playwright
        print("Playwright is already installed.")
    except ImportError:
        print("Installing Playwright...")
        if platform.system() == "Linux":
            os.system("python3 -m pip install playwright")
        else:
            os.system("python -m pip install playwright")
    
    # Install system dependencies for Playwright
    install_system_dependencies()
    
    # Install Playwright browsers
    print("Installing Playwright Chromium browser (this may take a few minutes)...")
    if platform.system() == "Linux":
        os.system("python3 -m playwright install chromium")
    else:
        os.system("python -m playwright install chromium")
    
    print("\nSetup complete! You can now run the pipeline with:")
    if platform.system() == "Linux":
        print("python3 pipeline_runner.py")
    else:
        print("python pipeline_runner.py")

if __name__ == "__main__":
    install_requirements()