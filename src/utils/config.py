# Configuration handling
"""
Configuration utility for UK Business Lead Generator
"""
import os
import json
from pathlib import Path
from PySide6.QtCore import QSettings

class Config:
    """Configuration manager"""
    
    def __init__(self):
        """Initialize configuration"""
        self.settings = QSettings("UK Business Lead Generator", "LeadGen")
        self._init_default_settings()
    
    def _init_default_settings(self):
        """Initialize default settings if not already set"""
        # General settings
        if not self.settings.contains("general/data_folder"):
            self.settings.setValue(
                "general/data_folder",
                os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
            )
        
        if not self.settings.contains("general/keep_data_on_uninstall"):
            self.settings.setValue("general/keep_data_on_uninstall", True)
        
        # Search settings
        if not self.settings.contains("search/limit"):
            self.settings.setValue("search/limit", 20)
        
        if not self.settings.contains("search/analyze_websites"):
            self.settings.setValue("search/analyze_websites", True)
        
        if not self.settings.contains("search/use_selenium"):
            self.settings.setValue("search/use_selenium", True)
        
        # Analysis settings
        if not self.settings.contains("analysis/use_lighthouse"):
            self.settings.setValue("analysis/use_lighthouse", True)
        
        if not self.settings.contains("analysis/lighthouse_timeout"):
            self.settings.setValue("analysis/lighthouse_timeout", 60)
        
        if not self.settings.contains("analysis/use_fallback"):
            self.settings.setValue("analysis/use_fallback", True)
        
        if not self.settings.contains("analysis/max_threads"):
            self.settings.setValue("analysis/max_threads", 3)
        
        # Export settings
        if not self.settings.contains("export/default_format"):
            self.settings.setValue("export/default_format", "CSV")
        
        if not self.settings.contains("export/default_path"):
            self.settings.setValue(
                "export/default_path",
                os.path.join(os.path.expanduser("~"), "UKLeadGen", "exports")
            )
    
    def get(self, key, default=None):
        """
        Get a configuration value
        
        Args:
            key: Setting key (e.g., "general/data_folder")
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        return self.settings.value(key, default)
    
    def set(self, key, value):
        """
        Set a configuration value
        
        Args:
            key: Setting key (e.g., "general/data_folder")
            value: Setting value
        """
        self.settings.setValue(key, value)
    
    def get_data_folder(self):
        """Get the data folder path"""
        return self.get("general/data_folder")
    
    def get_export_folder(self):
        """Get the export folder path"""
        return self.get("export/default_path")
    
    def get_search_limit(self):
        """Get the default search limit"""
        return self.get("search/limit", 20)
    
    def should_analyze_websites(self):
        """Check if websites should be analyzed by default"""
        return self.get("search/analyze_websites", True)
    
    def should_use_selenium(self):
        """Check if Selenium should be used"""
        return self.get("search/use_selenium", True)
    
    def should_use_lighthouse(self):
        """Check if Lighthouse should be used"""
        return self.get("analysis/use_lighthouse", True)
    
    def get_lighthouse_timeout(self):
        """Get the Lighthouse timeout"""
        return self.get("analysis/lighthouse_timeout", 60)
    
    def should_use_fallback(self):
        """Check if fallback analysis should be used"""
        return self.get("analysis/use_fallback", True)
    
    def get_max_threads(self):
        """Get the maximum number of analysis threads"""
        return self.get("analysis/max_threads", 3)
    
    def get_default_export_format(self):
        """Get the default export format"""
        return self.get("export/default_format", "CSV")