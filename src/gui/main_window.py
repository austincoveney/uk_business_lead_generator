"""
Main application window
"""
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, 
    QWidget, QToolBar, QStatusBar, QMessageBox,
    QMenu, QFileDialog
)
from PySide6.QtGui import QIcon, QKeySequence, QAction, QCursor
from PySide6.QtCore import Qt, Signal, Slot, QSettings

from src.gui.search_panel import SearchPanel
from src.gui.results_panel import ResultsPanel
from src.gui.report_view import ReportView
from src.gui.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("UK Business Lead Generator")
        self.setMinimumSize(1000, 700)
        
        # Initialize settings
        self.settings = QSettings("UK Business Lead Generator", "LeadGen")
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create panels
        self.search_panel = SearchPanel()
        self.results_panel = ResultsPanel()
        self.report_view = ReportView()
        
        # Add panels to tabs
        self.tab_widget.addTab(self.search_panel, "Search")
        self.tab_widget.addTab(self.results_panel, "Results")
        self.tab_widget.addTab(self.report_view, "Reports")
        
        # Create toolbar
        self.setup_toolbar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Connect signals
        self.search_panel.search_started.connect(self.on_search_started)
        self.search_panel.search_completed.connect(self.on_search_completed)
        self.search_panel.search_error.connect(self.on_search_error)
        
        # Apply saved settings
        self.restore_settings()
    
    def setup_toolbar(self):
        """Set up the main toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("mainToolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # New search action
        new_search_action = QAction("New Search", self)
        new_search_action.setStatusTip("Start a new search")
        new_search_action.triggered.connect(self.on_new_search)
        toolbar.addAction(new_search_action)
        
        toolbar.addSeparator()
        
        # Export action
        export_action = QAction("Export", self)
        export_action.setStatusTip("Export results")
        export_action.triggered.connect(self.on_export)
        toolbar.addAction(export_action)
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.setStatusTip("Configure application settings")
        settings_action.triggered.connect(self.on_settings)
        toolbar.addAction(settings_action)
        
        # Help action
        help_action = QAction("Help", self)
        help_action.setStatusTip("Show help")
        help_action.triggered.connect(self.on_help)
        toolbar.addAction(help_action)
    
    def restore_settings(self):
        """Restore saved window settings"""
        # Restore window geometry
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        
        # Restore window state
        if self.settings.contains("windowState"):
            self.restoreState(self.settings.value("windowState"))
    
    def save_settings(self):
        """Save window settings"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save settings before closing
        self.save_settings()
        event.accept()
    
    @Slot()
    def on_new_search(self):
        """Handle new search action"""
        self.tab_widget.setCurrentIndex(0)  # Switch to Search tab
        self.search_panel.clear_form()
    
    @Slot()
    def on_export(self):
        """Handle export action"""
        # Check if we have results to export
        if not self.results_panel.has_results():
            QMessageBox.information(self, "Export", "No results to export.")
            return
        
        # Show export options menu
        export_menu = QMenu(self)
        
        csv_action = export_menu.addAction("Export to CSV")
        text_action = export_menu.addAction("Export to Text Report")
        html_action = export_menu.addAction("Export to HTML Report")
        json_action = export_menu.addAction("Export to JSON")
        
        # Show menu at current mouse position
        action = export_menu.exec(QCursor.pos())
        
        if action == csv_action:
            self.export_csv()
        elif action == text_action:
            self.export_text()
        elif action == html_action:
            self.export_html()
        elif action == json_action:
            self.export_json()
    
    def export_csv(self):
        """Export results to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to CSV", "", "CSV Files (*.csv)")
        
        if file_path:
            if not file_path.endswith('.csv'):
                file_path += '.csv'
            
            success = self.results_panel.export_to_csv(file_path)
            
            if success:
                self.status_bar.showMessage(f"Exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Error", "Failed to export to CSV.")
    
    def export_text(self):
        """Export results to text report"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to Text Report", "", "Text Files (*.txt)")
        
        if file_path:
            if not file_path.endswith('.txt'):
                file_path += '.txt'
            
            success = self.results_panel.export_to_text(file_path)
            
            if success:
                self.status_bar.showMessage(f"Exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Error", "Failed to export to text report.")
    
    def export_html(self):
        """Export results to HTML report"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to HTML Report", "", "HTML Files (*.html)")
        
        if file_path:
            if not file_path.endswith('.html'):
                file_path += '.html'
            
            success = self.results_panel.export_to_html(file_path)
            
            if success:
                self.status_bar.showMessage(f"Exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Error", "Failed to export to HTML report.")
    
    def export_json(self):
        """Export results to JSON"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to JSON", "", "JSON Files (*.json)")
        
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
            
            success = self.results_panel.export_to_json(file_path)
            
            if success:
                self.status_bar.showMessage(f"Exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Error", "Failed to export to JSON.")
    
    @Slot()
    def on_settings(self):
        """Handle settings action"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Apply settings if dialog was accepted
            self.search_panel.load_settings()
            self.results_panel.load_settings()
            self.report_view.load_settings()
    
    @Slot()
    def on_help(self):
        """Handle help action"""
        QMessageBox.information(
            self, 
            "Help",
            "UK Business Lead Generator\n\n"
            "1. Enter a UK location (city, town, or postal code) in the Search tab\n"
            "2. Optionally specify a business category\n"
            "3. Click 'Generate Leads' to start the search\n"
            "4. View results in the Results tab\n"
            "5. Generate reports or export data using the toolbar\n\n"
            "For more information, please refer to the documentation."
        )
    
    @Slot()
    def on_search_started(self):
        """Handle search started signal"""
        self.status_bar.showMessage("Searching...")
    
    @Slot(int)
    def on_search_completed(self, count):
        """Handle search completed signal"""
        self.status_bar.showMessage(f"Search completed. Found {count} businesses.")
        self.tab_widget.setCurrentIndex(1)  # Switch to Results tab
        
        # Update results panel
        self.results_panel.load_results()
    
    @Slot(str)
    def on_search_error(self, error_message):
        """Handle search error signal"""
        self.status_bar.showMessage("Search failed.")
        QMessageBox.warning(self, "Search Error", error_message)