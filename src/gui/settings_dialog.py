# Settings dialog
"""
Settings dialog
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QCheckBox, 
    QPushButton, QTabWidget, QGroupBox, QWidget,  # Added QWidget here
    QFileDialog, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, QSettings

class SettingsDialog(QDialog):
    """Settings dialog for the application"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        
        # Load settings
        self.settings = QSettings("UK Business Lead Generator", "LeadGen")
        
        # Set up UI
        self.setup_ui()
        
        # Load current settings
        self.load_settings()
    
    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout(self)
        
        # Create tabs
        tab_widget = QTabWidget()
        
        # General settings tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Data folder settings
        data_group = QGroupBox("Data Storage")
        data_layout = QFormLayout(data_group)
        
        self.data_folder_edit = QLineEdit()
        self.data_folder_edit.setReadOnly(True)
        
        data_folder_layout = QHBoxLayout()
        data_folder_layout.addWidget(self.data_folder_edit)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.on_browse_clicked)
        data_folder_layout.addWidget(self.browse_button)
        
        data_layout.addRow("Data Folder:", data_folder_layout)
        
        # Keep data checkbox
        self.keep_data_checkbox = QCheckBox("Keep data when uninstalling")
        self.keep_data_checkbox.setChecked(True)
        data_layout.addRow("", self.keep_data_checkbox)
        
        general_layout.addWidget(data_group)
        
        # Search settings
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout(search_group)
        
        self.results_limit_spin = QSpinBox()
        self.results_limit_spin.setRange(5, 100)
        self.results_limit_spin.setValue(20)
        self.results_limit_spin.setSingleStep(5)
        search_layout.addRow("Default Results Limit:", self.results_limit_spin)
        
        self.analyze_websites_checkbox = QCheckBox("Analyze websites by default")
        self.analyze_websites_checkbox.setChecked(True)
        search_layout.addRow("", self.analyze_websites_checkbox)
        
        self.use_selenium_checkbox = QCheckBox("Use Selenium for better results (recommended)")
        self.use_selenium_checkbox.setChecked(True)
        search_layout.addRow("", self.use_selenium_checkbox)
        
        general_layout.addWidget(search_group)
        
        # Add stretch
        general_layout.addStretch()
        
        # Analysis settings tab
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)
        
        # Lighthouse settings
        lighthouse_group = QGroupBox("Lighthouse Integration")
        lighthouse_layout = QFormLayout(lighthouse_group)
        
        self.use_lighthouse_checkbox = QCheckBox("Use Lighthouse for website analysis")
        self.use_lighthouse_checkbox.setChecked(True)
        lighthouse_layout.addRow("", self.use_lighthouse_checkbox)
        
        self.lighthouse_path_edit = QLineEdit()
        lighthouse_layout.addRow("Lighthouse Path:", self.lighthouse_path_edit)
        
        self.lighthouse_timeout_spin = QSpinBox()
        self.lighthouse_timeout_spin.setRange(30, 300)
        self.lighthouse_timeout_spin.setValue(60)
        self.lighthouse_timeout_spin.setSingleStep(10)
        self.lighthouse_timeout_spin.setSuffix
        self.lighthouse_timeout_spin.setSuffix(" seconds")
        lighthouse_layout.addRow("Lighthouse Timeout:", self.lighthouse_timeout_spin)
        
        analysis_layout.addWidget(lighthouse_group)
        
        # Fallback settings
        fallback_group = QGroupBox("Fallback Analysis")
        fallback_layout = QFormLayout(fallback_group)
        
        self.fallback_checkbox = QCheckBox("Use basic analysis when Lighthouse is unavailable")
        self.fallback_checkbox.setChecked(True)
        fallback_layout.addRow("", self.fallback_checkbox)
        
        analysis_layout.addWidget(fallback_group)
        
        # Thread settings
        thread_group = QGroupBox("Performance")
        thread_layout = QFormLayout(thread_group)
        
        self.max_threads_spin = QSpinBox()
        self.max_threads_spin.setRange(1, 8)
        self.max_threads_spin.setValue(3)
        thread_layout.addRow("Maximum Analysis Threads:", self.max_threads_spin)
        
        analysis_layout.addWidget(thread_group)
        
        # Add stretch
        analysis_layout.addStretch()
        
        # Export settings tab
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        
        # Default export format
        format_group = QGroupBox("Default Export Format")
        format_layout = QFormLayout(format_group)
        
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["CSV", "Text Report", "HTML Report", "JSON"])
        format_layout.addRow("Default Format:", self.export_format_combo)
        
        export_layout.addWidget(format_group)
        
        # Default export path
        path_group = QGroupBox("Default Export Path")
        path_layout = QFormLayout(path_group)
        
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setReadOnly(True)
        
        export_path_layout = QHBoxLayout()
        export_path_layout.addWidget(self.export_path_edit)
        
        self.export_browse_button = QPushButton("Browse...")
        self.export_browse_button.clicked.connect(self.on_export_browse_clicked)
        export_path_layout.addWidget(self.export_browse_button)
        
        path_layout.addRow("Export Folder:", export_path_layout)
        
        export_layout.addWidget(path_group)
        
        # Add stretch
        export_layout.addStretch()
        
        # Add tabs to tab widget
        tab_widget.addTab(general_tab, "General")
        tab_widget.addTab(analysis_tab, "Analysis")
        tab_widget.addTab(export_tab, "Export")
        
        main_layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def load_settings(self):
        """Load current settings values"""
        # General settings
        data_folder = self.settings.value(
            "general/data_folder",
            os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
        )
        self.data_folder_edit.setText(data_folder)
        
        self.keep_data_checkbox.setChecked(
            self.settings.value("general/keep_data_on_uninstall", True, bool)
        )
        
        # Search settings
        self.results_limit_spin.setValue(
            self.settings.value("search/limit", 20, int)
        )
        
        self.analyze_websites_checkbox.setChecked(
            self.settings.value("search/analyze_websites", True, bool)
        )
        
        self.use_selenium_checkbox.setChecked(
            self.settings.value("search/use_selenium", True, bool)
        )
        
        # Analysis settings
        self.use_lighthouse_checkbox.setChecked(
            self.settings.value("analysis/use_lighthouse", True, bool)
        )
        
        self.lighthouse_path_edit.setText(
            self.settings.value("analysis/lighthouse_path", "")
        )
        
        self.lighthouse_timeout_spin.setValue(
            self.settings.value("analysis/lighthouse_timeout", 60, int)
        )
        
        self.fallback_checkbox.setChecked(
            self.settings.value("analysis/use_fallback", True, bool)
        )
        
        self.max_threads_spin.setValue(
            self.settings.value("analysis/max_threads", 3, int)
        )
        
        # Export settings
        export_format = self.settings.value("export/default_format", "CSV")
        index = self.export_format_combo.findText(export_format)
        if index >= 0:
            self.export_format_combo.setCurrentIndex(index)
        
        export_path = self.settings.value(
            "export/default_path",
            os.path.join(os.path.expanduser("~"), "UKLeadGen", "exports")
        )
        self.export_path_edit.setText(export_path)
    
    def save_settings(self):
        """Save settings values"""
        # General settings
        self.settings.setValue("general/data_folder", self.data_folder_edit.text())
        self.settings.setValue("general/keep_data_on_uninstall", self.keep_data_checkbox.isChecked())
        
        # Search settings
        self.settings.setValue("search/limit", self.results_limit_spin.value())
        self.settings.setValue("search/analyze_websites", self.analyze_websites_checkbox.isChecked())
        self.settings.setValue("search/use_selenium", self.use_selenium_checkbox.isChecked())
        
        # Analysis settings
        self.settings.setValue("analysis/use_lighthouse", self.use_lighthouse_checkbox.isChecked())
        self.settings.setValue("analysis/lighthouse_path", self.lighthouse_path_edit.text())
        self.settings.setValue("analysis/lighthouse_timeout", self.lighthouse_timeout_spin.value())
        self.settings.setValue("analysis/use_fallback", self.fallback_checkbox.isChecked())
        self.settings.setValue("analysis/max_threads", self.max_threads_spin.value())
        
        # Export settings
        self.settings.setValue("export/default_format", self.export_format_combo.currentText())
        self.settings.setValue("export/default_path", self.export_path_edit.text())
    
    def accept(self):
        """Handle accept (save) button click"""
        # Save settings
        self.save_settings()
        
        # Create directories if they don't exist
        try:
            data_folder = self.data_folder_edit.text()
            os.makedirs(data_folder, exist_ok=True)
            
            export_path = self.export_path_edit.text()
            os.makedirs(export_path, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to create directories: {str(e)}"
            )
        
        super().accept()
    
    def on_browse_clicked(self):
        """Handle browse button click for data folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Data Folder",
            self.data_folder_edit.text()
        )
        
        if folder:
            self.data_folder_edit.setText(folder)
    
    def on_export_browse_clicked(self):
        """Handle browse button click for export folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Export Folder",
            self.export_path_edit.text()
        )
        
        if folder:
            self.export_path_edit.setText(folder)