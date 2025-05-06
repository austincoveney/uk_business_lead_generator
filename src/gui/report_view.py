# Report generation view
"""
Report generation view
"""
import os
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QGroupBox, QFormLayout,
    QTextEdit, QCheckBox, QFileDialog, QMessageBox,
    QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt, Signal, Slot, QSettings, QUrl
from PySide6.QtGui import QDesktopServices

from src.core.database import LeadDatabase
from src.core.export import LeadExporter

class ReportView(QWidget):
    """Report view for generating and viewing reports"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize settings
        self.settings = QSettings("UK Business Lead Generator", "LeadGen")
        
        # Initialize variables
        self.current_database = None
        self.current_location = None
        self.current_report_html = ""
        
        # Set up UI
        self.setup_ui()
        
        # Load settings
        self.load_settings()
    
    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout(self)
        
        # Location selection
        location_layout = QHBoxLayout()
        
        location_label = QLabel("Location:")
        self.location_combo = QComboBox()
        self.location_combo.currentIndexChanged.connect(self.on_location_changed)
        
        location_layout.addWidget(location_label)
        location_layout.addWidget(self.location_combo, 1)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_locations)
        location_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(location_layout)
        
        # Tabs for different report views
        self.tab_widget = QTabWidget()
        
        # Summary tab
        self.summary_tab = QWidget()
        summary_layout = QVBoxLayout(self.summary_tab)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        
        summary_layout.addWidget(self.summary_text)
        
        # Report options tab
        self.options_tab = QWidget()
        options_layout = QVBoxLayout(self.options_tab)
        
        # Report type
        type_group = QGroupBox("Report Type")
        type_layout = QVBoxLayout(type_group)
        
        self.detailed_report_checkbox = QCheckBox("Detailed Business Information")
        self.detailed_report_checkbox.setChecked(True)
        type_layout.addWidget(self.detailed_report_checkbox)
        
        self.website_analysis_checkbox = QCheckBox("Website Analysis Results")
        self.website_analysis_checkbox.setChecked(True)
        type_layout.addWidget(self.website_analysis_checkbox)
        
        self.recommendations_checkbox = QCheckBox("Include Recommendations")
        self.recommendations_checkbox.setChecked(True)
        type_layout.addWidget(self.recommendations_checkbox)
        
        options_layout.addWidget(type_group)
        
        # Filter options
        filter_group = QGroupBox("Filter Options")
        filter_layout = QVBoxLayout(filter_group)
        
        self.high_priority_checkbox = QCheckBox("High Priority (No Website)")
        self.high_priority_checkbox.setChecked(True)
        filter_layout.addWidget(self.high_priority_checkbox)
        
        self.medium_priority_checkbox = QCheckBox("Medium Priority (Poor Website)")
        self.medium_priority_checkbox.setChecked(True)
        filter_layout.addWidget(self.medium_priority_checkbox)
        
        self.low_priority_checkbox = QCheckBox("Low Priority (Good Website)")
        self.low_priority_checkbox.setChecked(True)
        filter_layout.addWidget(self.low_priority_checkbox)
        
        options_layout.addWidget(filter_group)
        
        # Format options
        format_group = QGroupBox("Format Options")
        format_layout = QVBoxLayout(format_group)
        
        self.html_checkbox = QCheckBox("HTML Format")
        self.html_checkbox.setChecked(True)
        format_layout.addWidget(self.html_checkbox)
        
        self.text_checkbox = QCheckBox("Text Format")
        self.text_checkbox.setChecked(False)
        format_layout.addWidget(self.text_checkbox)
        
        options_layout.addWidget(format_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.generate_button = QPushButton("Generate Report")
        self.generate_button.clicked.connect(self.on_generate_report)
        buttons_layout.addWidget(self.generate_button)
        
        self.save_button = QPushButton("Save Report")
        self.save_button.clicked.connect(self.on_save_report)
        buttons_layout.addWidget(self.save_button)
        
        options_layout.addLayout(buttons_layout)
        options_layout.addStretch()
        
        # Preview tab
        self.preview_tab = QWidget()
        preview_layout = QVBoxLayout(self.preview_tab)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setHtml("<p>No report generated yet. Go to Options tab and click 'Generate Report'.</p>")
        
        preview_layout.addWidget(self.preview_text)
        
        # Add tabs
        self.tab_widget.addTab(self.summary_tab, "Summary")
        self.tab_widget.addTab(self.options_tab, "Options")
        self.tab_widget.addTab(self.preview_tab, "Preview")
        
        main_layout.addWidget(self.tab_widget)
    
    def load_settings(self):
        """Load saved settings"""
        # Load report options
        self.detailed_report_checkbox.setChecked(
            self.settings.value("report/detailed", True, bool))
        self.website_analysis_checkbox.setChecked(
            self.settings.value("report/website_analysis", True, bool))
        self.recommendations_checkbox.setChecked(
            self.settings.value("report/recommendations", True, bool))
        
        self.high_priority_checkbox.setChecked(
            self.settings.value("report/high_priority", True, bool))
        self.medium_priority_checkbox.setChecked(
            self.settings.value("report/medium_priority", True, bool))
        self.low_priority_checkbox.setChecked(
            self.settings.value("report/low_priority", True, bool))
        
        self.html_checkbox.setChecked(
            self.settings.value("report/html_format", True, bool))
        self.text_checkbox.setChecked(
            self.settings.value("report/text_format", False, bool))
        
        # Load locations
        self.load_locations()
    
    def save_settings(self):
        """Save current settings"""
        # Save report options
        self.settings.setValue("report/detailed", self.detailed_report_checkbox.isChecked())
        self.settings.setValue("report/website_analysis", self.website_analysis_checkbox.isChecked())
        self.settings.setValue("report/recommendations", self.recommendations_checkbox.isChecked())
        
        self.settings.setValue("report/high_priority", self.high_priority_checkbox.isChecked())
        self.settings.setValue("report/medium_priority", self.medium_priority_checkbox.isChecked())
        self.settings.setValue("report/low_priority", self.low_priority_checkbox.isChecked())
        
        self.settings.setValue("report/html_format", self.html_checkbox.isChecked())
        self.settings.setValue("report/text_format", self.text_checkbox.isChecked())
        
        # Save current location
        if self.location_combo.currentIndex() >= 0:
            self.settings.setValue("report/current_location", self.location_combo.currentText())
    
    def load_locations(self):
        """Load available locations from the data directory"""
        # Disconnect signal temporarily to avoid triggering callbacks
        self.location_combo.currentIndexChanged.disconnect(self.on_location_changed)
        
        # Clear the combo box
        self.location_combo.clear()
        
        # Get the data directory
        data_dir = os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
        
        # Check if directory exists
        if not os.path.exists(data_dir):
            self.location_combo.currentIndexChanged.connect(self.on_location_changed)
            return
        
        # Find database files
        import glob
        db_files = glob.glob(os.path.join(data_dir, "leads_*.db"))
        
        locations = []
        for db_file in db_files:
            # Extract location from filename
            filename = os.path.basename(db_file)
            if filename.startswith("leads_") and filename.endswith(".db"):
                location = filename[6:-3].replace("_", " ")
                locations.append(location)
        
        # Add locations to combo box
        if locations:
            self.location_combo.addItems(sorted(locations))
            
            # Try to select the last used location
            last_location = self.settings.value("report/current_location", "")
            if last_location in locations:
                self.location_combo.setCurrentText(last_location)
        
        # Reconnect signal
        self.location_combo.currentIndexChanged.connect(self.on_location_changed)
        
        # Trigger location changed to load data
        self.on_location_changed(self.location_combo.currentIndex())
    
    def on_location_changed(self, index):
        """Handle location selection change"""
        if index < 0:
            self.current_location = None
            self.current_database = None
            self.summary_text.clear()
            self.generate_button.setEnabled(False)
            self.save_button.setEnabled(False)
            return
        
        # Get selected location
        self.current_location = self.location_combo.currentText()
        
        # Close current database if open
        if self.current_database:
            self.current_database.close()
            self.current_database = None
        
        # Open the database
        db_dir = os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
        db_file = os.path.join(db_dir, f"leads_{self.current_location.replace(' ', '_')}.db")
        
        if not os.path.exists(db_file):
            self.summary_text.setPlainText(f"No data found for {self.current_location}")
            self.generate_button.setEnabled(False)
            self.save_button.setEnabled(False)
            return
        
        # Open database
        self.current_database = LeadDatabase(db_file)
        
        # Enable buttons
        self.generate_button.setEnabled(True)
        
        # Load summary
        self.load_summary()
        
        # Save settings
        self.save_settings()
    
    def load_summary(self):
        """Load and display summary information"""
        if not self.current_database or not self.current_location:
            return
        
        # Get all businesses
        businesses = self.current_database.get_all_businesses()
        
        if not businesses:
            self.summary_text.setPlainText(f"No businesses found in {self.current_location}")
            return
        
        # Count by priority
        priority_counts = {1: 0, 2: 0, 3: 0}
        for business in businesses:
            priority = business.get('priority', 0)
            if priority in priority_counts:
                priority_counts[priority] += 1
        
        # Calculate averages for websites
        perf_scores = []
        seo_scores = []
        access_scores = []
        bp_scores = []
        
        for business in businesses:
            if business.get('website'):
                if business.get('performance_score') is not None:
                    perf_scores.append(business['performance_score'])
                if business.get('seo_score') is not None:
                    seo_scores.append(business['seo_score'])
                if business.get('accessibility_score') is not None:
                    access_scores.append(business['accessibility_score'])
                if business.get('best_practices_score') is not None:
                    bp_scores.append(business['best_practices_score'])
        
        # Calculate averages
        avg_perf = sum(perf_scores) / len(perf_scores) if perf_scores else 0
        avg_seo = sum(seo_scores) / len(seo_scores) if seo_scores else 0
        avg_access = sum(access_scores) / len(access_scores) if access_scores else 0
        avg_bp = sum(bp_scores) / len(bp_scores) if bp_scores else 0
        
        # Count businesses with websites
        with_website = len([b for b in businesses if b.get('website')])
        without_website = len(businesses) - with_website
        
        # Build HTML summary
        html = f"""
        <h2>Summary for {self.current_location}</h2>
        <p>Total businesses: {len(businesses)}</p>
        
        <h3>Priority Breakdown</h3>
        <ul>
            <li>High Priority (No Website): {priority_counts[1]}</li>
            <li>Medium Priority (Poor Website): {priority_counts[2]}</li>
            <li>Low Priority (Good Website): {priority_counts[3]}</li>
        </ul>
        
        <h3>Website Presence</h3>
        <ul>
            <li>Businesses with websites: {with_website} ({with_website / len(businesses) * 100:.1f}%)</li>
            <li>Businesses without websites: {without_website} ({without_website / len(businesses) * 100:.1f}%)</li>
        </ul>
        """
        
        if with_website > 0:
            html += f"""
            <h3>Average Website Scores</h3>
            <ul>
                <li>Performance: {avg_perf:.1f}%</li>
                <li>SEO: {avg_seo:.1f}%</li>
                <li>Accessibility: {avg_access:.1f}%</li>
                <li>Best Practices: {avg_bp:.1f}%</li>
            </ul>
            """
        
        # Count business types
        business_types = {}
        for business in businesses:
            btype = business.get('business_type', 'Unknown')
            business_types[btype] = business_types.get(btype, 0) + 1
        
        # Show top 5 business types
        top_types = sorted(business_types.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if top_types:
            html += "<h3>Top Business Types</h3><ul>"
            for btype, count in top_types:
                html += f"<li>{btype}: {count}</li>"
            html += "</ul>"
        
        self.summary_text.setHtml(html)
    
    def on_generate_report(self):
        """Generate a report based on current options"""
        if not self.current_database or not self.current_location:
            return
        
        # Save settings
        self.save_settings()
        
        # Gather options
        detailed = self.detailed_report_checkbox.isChecked()
        website_analysis = self.website_analysis_checkbox.isChecked()
        recommendations = self.recommendations_checkbox.isChecked()
        
        # Get priorities to include
        priorities = []
        if self.high_priority_checkbox.isChecked():
            priorities.append(1)
        if self.medium_priority_checkbox.isChecked():
            priorities.append(2)
        if self.low_priority_checkbox.isChecked():
            priorities.append(3)
        
        # Get all businesses
        all_businesses = self.current_database.get_all_businesses()
        
        # Filter by priority
        if priorities:
            businesses = [b for b in all_businesses if b.get('priority', 0) in priorities]
        else:
            businesses = all_businesses
        
        if not businesses:
            self.preview_text.setHtml(
                "<p>No businesses match the selected filters.</p>"
            )
            self.tab_widget.setCurrentIndex(2)  # Switch to Preview tab
            self.save_button.setEnabled(False)
            return
        
        # Build report content
        if self.html_checkbox.isChecked():
            # Generate HTML report
            html = self.generate_html_report(
                businesses, detailed, website_analysis, recommendations
            )
            self.preview_text.setHtml(html)
            self.current_report_html = html
        else:
            # Generate text report
            text = self.generate_text_report(
                businesses, detailed, website_analysis, recommendations
            )
            self.preview_text.setPlainText(text)
            self.current_report_html = ""
        
        # Switch to preview tab
        self.tab_widget.setCurrentIndex(2)
        
        # Enable save button
        self.save_button.setEnabled(True)
    
    def generate_html_report(self, businesses, detailed, website_analysis, recommendations):
        """Generate HTML report"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Lead Report - {self.current_location}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; color: #333; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        .report-header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
        .summary {{ margin-bottom: 30px; }}
        .business {{ margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
        .business h2 {{ margin-top: 0; }}
        .priority-1 {{ border-left: 5px solid #e74c3c; }}
        .priority-2 {{ border-left: 5px solid #f39c12; }}
        .priority-3 {{ border-left: 5px solid #2ecc71; }}
        .metrics {{ display: flex; flex-wrap: wrap; gap: 15px; margin: 15px 0; }}
        .metric {{ 
            flex: 1; 
            min-width: 100px; 
            padding: 15px; 
            background-color: #f8f9fa; 
            border-radius: 5px; 
            text-align: center;
        }}
        .metric-value {{ font-size: 24px; font-weight: bold; margin: 10px 0; }}
        .high {{ color: #2ecc71; }}
        .medium {{ color: #f39c12; }}
        .low {{ color: #e74c3c; }}
        .issues {{ margin-top: 15px; }}
        .issues h3 {{ color: #e74c3c; }}
        .contact-info {{ margin-top: 15px; background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
        .recommendations {{ 
            background-color: #e8f4f8; 
            padding: 15px; 
            border-radius: 5px; 
            margin-top: 20px;
            border-left: 5px solid #3498db;
        }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        tr:hover {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="report-header">
        <h1>Business Lead Report</h1>
        <p><strong>Location:</strong> {self.current_location}</p>
        <p><strong>Date:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <p><strong>Total Businesses:</strong> {len(businesses)}</p>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
"""
        
        # Priority breakdown
        priority_counts = {1: 0, 2: 0, 3: 0}
        for business in businesses:
            priority = business.get('priority', 0)
            if priority in priority_counts:
                priority_counts[priority] += 1
                
        html += f"""
        <p>This report contains {len(businesses)} businesses in {self.current_location}, categorized by website presence and quality:</p>
        <ul>
            <li><strong>High Priority Leads (No Website):</strong> {priority_counts[1]}</li>
            <li><strong>Medium Priority Leads (Poor Website):</strong> {priority_counts[2]}</li>
            <li><strong>Low Priority Leads (Good Website):</strong> {priority_counts[3]}</li>
        </ul>
"""
        
        # Website metrics averages if applicable
        websites = [b for b in businesses if b.get('website')]
        if websites and website_analysis:
            avg_perf = sum(b.get('performance_score', 0) for b in websites) / len(websites)
            avg_seo = sum(b.get('seo_score', 0) for b in websites) / len(websites)
            avg_access = sum(b.get('accessibility_score', 0) for b in websites) / len(websites)
            avg_bp = sum(b.get('best_practices_score', 0) for b in websites) / len(websites)
            
            html += f"""
        <p>Analysis of {len(websites)} websites reveals the following average scores:</p>
        <div class="metrics">
            <div class="metric">
                <div>Performance</div>
                <div class="metric-value {self._get_color_class(avg_perf)}">{avg_perf:.1f}%</div>
            </div>
            <div class="metric">
                <div>SEO</div>
                <div class="metric-value {self._get_color_class(avg_seo)}">{avg_seo:.1f}%</div>
            </div>
            <div class="metric">
                <div>Accessibility</div>
                <div class="metric-value {self._get_color_class(avg_access)}">{avg_access:.1f}%</div>
            </div>
            <div class="metric">
                <div>Best Practices</div>
                <div class="metric-value {self._get_color_class(avg_bp)}">{avg_bp:.1f}%</div>
            </div>
        </div>
"""
        
        # Recommendations section
        if recommendations:
            html += """
        <div class="recommendations">
            <h3>Outreach Recommendations</h3>
            <p>Based on the analysis, we recommend the following approach:</p>
            <ol>
"""
            if priority_counts[1] > 0:
                html += f"""
                <li><strong>Target businesses with no website ({priority_counts[1]} leads)</strong> - These represent the highest-value opportunities, as they currently have no web presence. Highlight the benefits of establishing an online presence and showcase similar businesses you've helped.</li>
"""
            
            if priority_counts[2] > 0:
                html += f"""
                <li><strong>Contact businesses with poor websites ({priority_counts[2]} leads)</strong> - These businesses already recognize the need for a web presence but could benefit from significant improvements. Focus on specific issues found in the analysis and provide concrete examples of how you could enhance their online presence.</li>
"""
            
            if priority_counts[3] > 0:
                html += f"""
                <li><strong>Monitor businesses with good websites ({priority_counts[3]} leads)</strong> - While these leads are lower priority, they may benefit from specialized services or future updates. Consider reaching out for specific enhancements or maintenance services.</li>
"""
            
            html += """
            </ol>
        </div>
"""
        
        html += """
    </div>
    
    <h2>Business Details</h2>
"""
        
        # Add table view of businesses
        html += """
    <table>
        <tr>
            <th>Priority</th>
            <th>Business Name</th>
            <th>Business Type</th>
            <th>Contact Info</th>
            <th>Website</th>
        </tr>
"""
        
        # Sort businesses by priority
        businesses_sorted = sorted(businesses, key=lambda b: (b.get('priority', 999), b.get('name', '')))
        
        for business in businesses_sorted:
            priority = business.get('priority', 0)
            priority_text = "High" if priority == 1 else "Medium" if priority == 2 else "Low" if priority == 3 else "Unknown"
            
            html += f"""
        <tr>
            <td>{priority_text}</td>
            <td>{business.get('name', '')}</td>
            <td>{business.get('business_type', '')}</td>
            <td>Phone: {business.get('phone', 'N/A')}</td>
            <td>{"Yes" if business.get('website') else "No"}</td>
        </tr>
"""
        
        html += """
    </table>
"""
        
        # Detailed individual business listings
        if detailed:
            html += "<h2>Detailed Business Information</h2>"
            
            for business in businesses_sorted:
                priority = business.get('priority', 0)
                
                html += f"""
    <div class="business priority-{priority}">
        <h2>{business.get('name', '')}</h2>
        <p><strong>Priority:</strong> {"High (No Website)" if priority == 1 else "Medium (Poor Website)" if priority == 2 else "Low (Good Website)" if priority == 3 else "Unknown"}</p>
"""
                
                if business.get('business_type'):
                    html += f'<p><strong>Business Type:</strong> {business.get("business_type")}</p>\n'
                
                # Contact information
                html += '<div class="contact-info">\n'
                
                if business.get('address'):
                    html += f'<p><strong>Address:</strong> {business.get("address")}</p>\n'
                
                if business.get('phone'):
                    html += f'<p><strong>Phone:</strong> {business.get("phone")}</p>\n'
                
                if business.get('email'):
                    html += f'<p><strong>Email:</strong> {business.get("email")}</p>\n'
                
                if business.get('website'):
                    html += f'<p><strong>Website:</strong> <a href="{business.get("website")}" target="_blank">{business.get("website")}</a></p>\n'
                
                html += '</div>\n'
                
                # Website analysis
                if website_analysis and business.get('website'):
                    html += '<h3>Website Analysis</h3>\n'
                    
                    html += '<div class="metrics">\n'
                    
                    metrics = [
                        ('Performance', business.get('performance_score', 0)),
                        ('SEO', business.get('seo_score', 0)),
                        ('Accessibility', business.get('accessibility_score', 0)),
                        ('Best Practices', business.get('best_practices_score', 0))
                    ]
                    
                    for name, score in metrics:
                        html += f'''
                <div class="metric">
                    <div>{name}</div>
                    <div class="metric-value {self._get_color_class(score)}">{score}%</div>
                </div>'''
                    
                    html += '\n</div>\n'
                    
                    # Issues
                    issues = business.get('issues', [])
                    if issues:
                        html += '<div class="issues">\n'
                        html += '<h3>Issues Detected</h3>\n'
                        html += '<ul>\n'
                        
                        for issue in issues:
                            html += f'<li>{issue}</li>\n'
                            
                        html += '</ul>\n'
                        html += '</div>\n'
                
                # Notes
                if business.get('notes'):
                    html += f'<p><strong>Notes:</strong> {business.get("notes")}</p>\n'
                
                html += '</div>\n'
        
        html += """
</body>
</html>
"""
        
        return html
    
    def generate_text_report(self, businesses, detailed, website_analysis, recommendations):
        """Generate plain text report"""
        # Header
        text = f"BUSINESS LEAD REPORT - {self.current_location}\n"
        text += "=" * 80 + "\n\n"
        text += f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        text += f"Total Businesses: {len(businesses)}\n\n"
        
        # Priority breakdown
        priority_counts = {1: 0, 2: 0, 3: 0}
        for business in businesses:
            priority = business.get('priority', 0)
            if priority in priority_counts:
                priority_counts[priority] += 1
                
        text += "PRIORITY BREAKDOWN:\n"
        text += f"- High Priority (No Website): {priority_counts[1]}\n"
        text += f"- Medium Priority (Poor Website): {priority_counts[2]}\n"
        text += f"- Low Priority (Good Website): {priority_counts[3]}\n\n"
        
        # Website metrics if applicable
        websites = [b for b in businesses if b.get('website')]
        if websites and website_analysis:
            avg_perf = sum(b.get('performance_score', 0) for b in websites) / len(websites)
            avg_seo = sum(b.get('seo_score', 0) for b in websites) / len(websites)
            avg_access = sum(b.get('accessibility_score', 0) for b in websites) / len(websites)
            avg_bp = sum(b.get('best_practices_score', 0) for b in websites) / len(websites)
            
            text += f"WEBSITE METRICS (AVERAGE OF {len(websites)} WEBSITES):\n"
            text += f"- Performance: {avg_perf:.1f}%\n"
            text += f"- SEO: {avg_seo:.1f}%\n"
            text += f"- Accessibility: {avg_access:.1f}%\n"
            text += f"- Best Practices: {avg_bp:.1f}%\n\n"
        
        # Recommendations
        if recommendations:
            text += "OUTREACH RECOMMENDATIONS:\n"
            
            if priority_counts[1] > 0:
                text += f"1. Target businesses with no website ({priority_counts[1]} leads)\n"
                text += "   These represent the highest-value opportunities, as they currently\n"
                text += "   have no web presence. Highlight the benefits of establishing an\n"
                text += "   online presence and showcase similar businesses you've helped.\n\n"
            
            if priority_counts[2] > 0:
                text += f"2. Contact businesses with poor websites ({priority_counts[2]} leads)\n"
                text += "   These businesses already recognize the need for a web presence but\n"
                text += "   could benefit from significant improvements. Focus on specific issues\n"
                text += "   found in the analysis and provide concrete examples of improvements.\n\n"
            
            if priority_counts[3] > 0:
                text += f"3. Monitor businesses with good websites ({priority_counts[3]} leads)\n"
                text += "   While these leads are lower priority, they may benefit from specialized\n"
                text += "   services or future updates. Consider reaching out for specific\n" 
                text += "   enhancements or maintenance services.\n\n"
        
        # Business summaries
        text += "BUSINESS SUMMARY:\n"
        text += "-" * 80 + "\n\n"
        
        # Sort businesses by priority
        businesses_sorted = sorted(businesses, key=lambda b: (b.get('priority', 999), b.get('name', '')))
        
        for i, business in enumerate(businesses_sorted):
            priority = business.get('priority', 0)
            priority_text = "High" if priority == 1 else "Medium" if priority == 2 else "Low" if priority == 3 else "Unknown"
            
            text += f"{i+1}. {business.get('name', '')} - {priority_text} Priority\n"
            
            if business.get('business_type'):
                text += f"   Type: {business.get('business_type')}\n"
                
            if business.get('phone'):
                text += f"   Phone: {business.get('phone')}\n"
                
            if business.get('website'):
                text += f"   Website: {business.get('website')}\n"
                
            text += "\n"
        
        # Detailed listings
        if detailed:
            text += "\nDETAILED BUSINESS INFORMATION:\n"
            text += "=" * 80 + "\n\n"
            
            for business in businesses_sorted:
                priority = business.get('priority', 0)
                priority_text = "High (No Website)" if priority == 1 else "Medium (Poor Website)" if priority == 2 else "Low (Good Website)" if priority == 3 else "Unknown"
                
                text += f"BUSINESS: {business.get('name', '')}\n"
                text += f"PRIORITY: {priority_text}\n"
                
                if business.get('business_type'):
                    text += f"TYPE: {business.get('business_type')}\n"
                
                if business.get('address'):
                    text += f"ADDRESS: {business.get('address')}\n"
                
                if business.get('phone'):
                    text += f"PHONE: {business.get('phone')}\n"
                
                if business.get('email'):
                    text += f"EMAIL: {business.get('email')}\n"
                
                if business.get('website'):
                    text += f"WEBSITE: {business.get('website')}\n"
                    
                    # Website analysis
                    if website_analysis:
                        text += "\nWEBSITE ANALYSIS:\n"
                        text += f"- Performance: {business.get('performance_score', 0)}%\n"
                        text += f"- SEO: {business.get('seo_score', 0)}%\n"
                        text += f"- Accessibility: {business.get('accessibility_score', 0)}%\n"
                        text += f"- Best Practices: {business.get('best_practices_score', 0)}%\n"
                        
                        # Issues
                        issues = business.get('issues', [])
                        if issues:
                            text += "\nISSUES DETECTED:\n"
                            for issue in issues:
                                text += f"- {issue}\n"
                
                # Notes
                if business.get('notes'):
                    text += f"\nNOTES: {business.get('notes')}\n"
                
                text += "-" * 80 + "\n\n"
        
        return text
    
    def _get_color_class(self, score):
        """Get color class based on score"""
        if score >= 80:
            return "high"
        elif score >= 50:
            return "medium"
        else:
            return "low"
    
    def on_save_report(self):
        """Save the generated report to a file"""
        if not self.current_location:
            return
            
        if self.html_checkbox.isChecked():
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save HTML Report",
                f"report_{self.current_location.replace(' ', '_')}.html",
                "HTML Files (*.html)"
            )
            
            if not file_path:
                return
                
            # Save HTML report
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.current_report_html)
                
            # Ask if user wants to open the file
            result = QMessageBox.question(
                self,
                "Report Saved",
                f"Report saved to {file_path}\nWould you like to open it now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if result == QMessageBox.Yes:
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                
        elif self.text_checkbox.isChecked():
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Text Report",
                f"report_{self.current_location.replace(' ', '_')}.txt",
                "Text Files (*.txt)"
            )
            
            if not file_path:
                return
                
            # Save text report
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.preview_text.toPlainText())
                
            # Inform user
            QMessageBox.information(
                self,
                "Report Saved",
                f"Report saved to {file_path}"
            )