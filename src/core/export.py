# Export functionality
"""
Export functionality for lead data
"""
import os
import csv
import json
import datetime

class LeadExporter:
    """Handles exporting lead data to various formats"""
    
    def __init__(self, database):
        """
        Initialize the exporter
        
        Args:
            database: LeadDatabase instance
        """
        self.database = database
    
    def export_to_csv(self, filepath):
        """
        Export leads to CSV
        
        Args:
            filepath: Path to save the CSV file
            
        Returns:
            Number of exported records
        """
        return self.database.export_to_csv(filepath)
    
    def export_to_text(self, filepath):
        """
        Export leads to a plain text report
        
        Args:
            filepath: Path to save the text file
            
        Returns:
            Number of exported records
        """
        return self.database.export_to_text(filepath)
    
    def export_to_json(self, filepath):
        """
        Export leads to JSON
        
        Args:
            filepath: Path to save the JSON file
            
        Returns:
            Number of exported records
        """
        try:
            businesses = self.database.get_all_businesses()
            
            if not businesses:
                return 0
            
            # Add timestamp and metadata
            export_data = {
                "metadata": {
                    "generated_at": datetime.datetime.now().isoformat(),
                    "count": len(businesses)
                },
                "businesses": businesses
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            # Write the JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return len(businesses)
            
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return 0
    
    def export_to_html(self, filepath):
        """
        Export leads to HTML report
        
        Args:
            filepath: Path to save the HTML file
            
        Returns:
            Number of exported records
        """
        try:
            businesses = self.database.get_all_businesses()
            
            if not businesses:
                return 0
            
            # Priority labels for display
            priority_labels = {
                1: "High Priority (No Website)",
                2: "Medium Priority (Poor Website)",
                3: "Low Priority (Good Website)",
                0: "Unknown Priority"
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write HTML header
                f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Lead Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1, h2 { color: #2c3e50; }
        .report-header { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .business { margin-bottom: 30px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .business h2 { margin-top: 0; }
        .priority-1 { border-left: 5px solid #e74c3c; }
        .priority-2 { border-left: 5px solid #f39c12; }
        .priority-3 { border-left: 5px solid #2ecc71; }
        .metrics { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }
        .metric { flex: 1; min-width: 100px; padding: 10px; background-color: #f8f9fa; border-radius: 5px; text-align: center; }
        .metric-title { font-weight: bold; margin-bottom: 5px; }
        .issues { margin-top: 10px; }
        .issue { color: #e74c3c; margin-bottom: 3px; }
        .contact { margin-top: 10px; }
    </style>
</head>
<body>
    <div class="report-header">
        <h1>Business Lead Report</h1>
        <p>Generated on: """ + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        <p>Total businesses: """ + str(len(businesses)) + """</p>
    </div>
""")
                
                # Write businesses
                for business in businesses:
                    priority = business.get('priority', 0)
                    
                    f.write(f'<div class="business priority-{priority}">\n')
                    f.write(f'<h2>{business.get("name", "Unknown")}</h2>\n')
                    f.write(f'<p><strong>Priority:</strong> {priority_labels.get(priority, "Unknown")}</p>\n')
                    
                    if business.get('business_type'):
                        f.write(f'<p><strong>Type:</strong> {business.get("business_type")}</p>\n')
                        
                    if business.get('address'):
                        f.write(f'<p><strong>Address:</strong> {business.get("address")}</p>\n')
                        
                    if business.get('phone'):
                        f.write(f'<p><strong>Phone:</strong> {business.get("phone")}</p>\n')
                        
                    if business.get('email'):
                        f.write(f'<p><strong>Email:</strong> {business.get("email")}</p>\n')
                        
                    if business.get('website'):
                        f.write(f'<p><strong>Website:</strong> <a href="{business.get("website")}" target="_blank">{business.get("website")}</a></p>\n')
                        
                        # Add website metrics if available
                        has_metrics = any(key in business for key in [
                            'performance_score', 'seo_score', 'accessibility_score', 'best_practices_score'
                        ])
                        
                        if has_metrics:
                            f.write('<div class="metrics">\n')
                            
                            metrics = [
                                ('Performance', business.get('performance_score', 0)),
                                ('SEO', business.get('seo_score', 0)),
                                ('Accessibility', business.get('accessibility_score', 0)),
                                ('Best Practices', business.get('best_practices_score', 0))
                            ]
                            
                            for name, score in metrics:
                                color = "#e74c3c" if score < 50 else "#f39c12" if score < 80 else "#2ecc71"
                                f.write(f'<div class="metric">\n')
                                f.write(f'<div class="metric-title">{name}</div>\n')
                                f.write(f'<div style="color: {color}; font-size: 18px; font-weight: bold;">{score}%</div>\n')
                                f.write('</div>\n')
                                
                            f.write('</div>\n')
                    
                    # Add issues if available
                    if business.get('issues'):
                        f.write('<div class="issues">\n')
                        f.write('<p><strong>Issues:</strong></p>\n')
                        f.write('<ul>\n')
                        for issue in business.get('issues', []):
                            f.write(f'<li class="issue">{issue}</li>\n')
                        f.write('</ul>\n')
                        f.write('</div>\n')
                    
                    # Add notes if available
                    if business.get('notes'):
                        f.write(f'<p><strong>Notes:</strong> {business.get("notes")}</p>\n')
                    
                    # Get contact attempts if available
                    contact_attempts = self.database.get_contact_attempts(business.get('id'))
                    if contact_attempts:
                        f.write('<div class="contact">\n')
                        f.write('<p><strong>Contact History:</strong></p>\n')
                        f.write('<ul>\n')
                        for attempt in contact_attempts:
                            f.write(f'<li>{attempt.get("date")}: {attempt.get("method")} - {attempt.get("outcome")}</li>\n')
                        f.write('</ul>\n')
                        f.write('</div>\n')
                    
                    f.write('</div>\n')
                
                # Write HTML footer
                f.write("""
</body>
</html>
""")
            
            return len(businesses)
            
        except Exception as e:
            print(f"Error exporting to HTML: {e}")
            return 0