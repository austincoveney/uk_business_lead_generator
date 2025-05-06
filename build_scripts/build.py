#!/usr/bin/env python3
"""
Build script for UK Business Lead Generator
"""
import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

def build_application():
    """Build the executable using PyInstaller"""
    print("Building UK Business Lead Generator...")
    
    # Determine system platform
    is_windows = platform.system() == "Windows"
    is_macos = platform.system() == "Darwin"
    is_linux = platform.system() == "Linux"
    
    # Define paths
    root_dir = Path(__file__).resolve().parent
    icon_path = root_dir / "src" / "assets" / "icon.ico" if is_windows else root_dir / "src" / "assets" / "icon.icns"
    
    # Install required packages if needed
    print("Checking dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller.__main__
        print("PyInstaller is already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Prepare PyInstaller command
    pyinstaller_args = [
        "src/main.py",                       # Script to package
        "--name=UK_Business_Lead_Generator", # Output name
        "--onefile",                         # Create a single executable
        "--windowed",                        # Hide console window
        f"--icon={icon_path}",               # Application icon
        "--clean",                           # Clean before building
    ]
    
    # Add data files
    pyinstaller_args.extend([
        "--add-data=src/assets/*;assets",    # Include assets
    ])
    
    if is_windows:
        pyinstaller_args.extend([
            "--add-binary=path/to/chromedriver.exe;.",  # Include ChromeDriver for Windows
        ])
    elif is_macos:
        pyinstaller_args.extend([
            "--add-binary=path/to/chromedriver;.",      # Include ChromeDriver for macOS
        ])
    elif is_linux:
        pyinstaller_args.extend([
            "--add-binary=path/to/chromedriver;.",      # Include ChromeDriver for Linux
        ])
    
    # Add hidden imports
    pyinstaller_args.extend([
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=selenium",
        "--hidden-import=bs4",
    ])
    
    # Run PyInstaller
    print("Building executable with PyInstaller...")
    subprocess.run([sys.executable, "-m", "PyInstaller.__main__"] + pyinstaller_args)
    
    print("Build completed. Executable is in the dist folder.")

if __name__ == "__main__":
    build_application()