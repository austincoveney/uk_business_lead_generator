#!/usr/bin/env python3
"""
UK Business Lead Generator - Main Application Entry Point
"""
import sys
import os
import logging
from pathlib import Path

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, Qt, QSettings

# Use absolute imports instead of relative imports
from src.gui.main_window import MainWindow
from src.utils.helpers import setup_logging, get_resource_path

def main():
    """Main application entry point"""
    # Set up application details
    QCoreApplication.setOrganizationName("UK Business Lead Generator")
    QCoreApplication.setApplicationName("UKLeadGen")
    QCoreApplication.setApplicationVersion("1.0.0")
    
    # Set up logging
    setup_logging()
    
    # Create data directories
    data_dir = os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
    export_dir = os.path.join(os.path.expanduser("~"), "UKLeadGen", "exports")
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(export_dir, exist_ok=True)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    main_window = MainWindow()
    main_window.show()
    
    # Run application
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())