"""
Results display panel
"""

import os
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableView,
    QPushButton,
    QComboBox,
    QLineEdit,
    QGroupBox,
    QFormLayout,
    QAbstractItemView,
    QHeaderView,
    QMessageBox,
    QSplitter,
    QTextEdit,
    QProgressBar,
)
from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QSettings,
    QSortFilterProxyModel,
    QAbstractTableModel,
    QModelIndex,
    QThreadPool,
    QRunnable,
    QObject,
)
from PySide6.QtGui import QColor, QBrush, QFont, QIcon, QCursor

from src.core.database import LeadDatabase
from src.core.export import LeadExporter


class BusinessTableModel(QAbstractTableModel):
    """Table model for displaying business data"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.businesses = []
        self.headers = [
            "Priority",
            "Name",
            "Business Type",
            "Phone",
            "Website",
            "Address",
            "Issues",
        ]

    def load_data(self, businesses):
        """Load business data into the model"""
        self.beginResetModel()
        self.businesses = businesses
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self.businesses)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.businesses)):
            return None

        business = self.businesses[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            if column == 0:
                # Priority
                priority = business.get("priority", 0)
                if priority == 1:
                    return "High"
                elif priority == 2:
                    return "Medium"
                elif priority == 3:
                    return "Low"
                else:
                    return "Unknown"
            elif column == 1:
                # Name
                return business.get("name", "")
            elif column == 2:
                # Business Type
                return business.get("business_type", "")
            elif column == 3:
                # Phone
                return business.get("phone", "")
            elif column == 4:
                # Website
                return business.get("website", "")
            elif column == 5:
                # Address
                return business.get("address", "")
            elif column == 6:
                # Issues
                issues = business.get("issues", [])
                if isinstance(issues, list) and issues:
                    return f"{len(issues)} issues"
                return ""

        elif role == Qt.BackgroundRole:
            priority = business.get("priority", 0)
            if priority == 1:  # High priority
                return QBrush(QColor(255, 230, 230))
            elif priority == 2:  # Medium priority
                return QBrush(QColor(255, 245, 230))
            elif priority == 3:  # Low priority
                return QBrush(QColor(240, 255, 240))

        elif role == Qt.FontRole:
            if column == 1:  # Business name
                font = QFont()
                font.setBold(True)
                return font

        elif role == Qt.UserRole:
            # Return the full business data for custom processing
            return business

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None


class ResultsPanel(QWidget):
    """Results panel for displaying and managing business leads"""

    def __init__(self):
        super().__init__()

        # Initialize settings
        self.settings = QSettings("UK Business Lead Generator", "LeadGen")

        # Initialize model and data
        self.model = BusinessTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(-1)  # Search all columns
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

        # Current database and location
        self.current_database = None
        self.current_location = None

        # Thread pool for background tasks
        self.thread_pool = QThreadPool()

        # Set up UI
        self.setup_ui()

        # Load settings
        self.load_settings()

    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout(self)

        # Splitter for table and details
        self.splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(self.splitter)

        # Upper part: Filter and Table
        upper_widget = QWidget()
        upper_layout = QVBoxLayout(upper_widget)

        # Filter controls
        filter_layout = QHBoxLayout()

        filter_label = QLabel("Filter:")
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Search...")
        self.filter_edit.textChanged.connect(self.on_filter_changed)

        priority_label = QLabel("Priority:")
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["All", "High", "Medium", "Low"])
        self.priority_combo.currentIndexChanged.connect(self.on_priority_changed)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_edit, 1)
        filter_layout.addWidget(priority_label)
        filter_layout.addWidget(self.priority_combo)

        upper_layout.addLayout(filter_layout)

        # Business table
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.table_view.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )  # Name column stretches
        self.table_view.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.Stretch
        )  # Address column stretches
        self.table_view.selectionModel().selectionChanged.connect(
            self.on_selection_changed
        )

        upper_layout.addWidget(self.table_view)

        # Lower part: Business details
        lower_widget = QWidget()
        lower_layout = QVBoxLayout(lower_widget)

        details_layout = QHBoxLayout()

        # Business info
        info_group = QGroupBox("Business Details")
        info_layout = QFormLayout(info_group)

        self.name_label = QLabel()
        info_layout.addRow("Name:", self.name_label)

        self.type_label = QLabel()
        info_layout.addRow("Type:", self.type_label)

        self.address_label = QLabel()
        info_layout.addRow("Address:", self.address_label)

        self.phone_label = QLabel()
        info_layout.addRow("Phone:", self.phone_label)

        self.email_label = QLabel()
        info_layout.addRow("Email:", self.email_label)

        self.website_label = QLabel()
        info_layout.addRow("Website:", self.website_label)

        details_layout.addWidget(info_group)

        # Website analysis
        analysis_group = QGroupBox("Website Analysis")
        analysis_layout = QVBoxLayout(analysis_group)

        metrics_layout = QHBoxLayout()

        self.performance_progress = QProgressBar()
        self.performance_progress.setRange(0, 100)
        self.performance_progress.setValue(0)
        self.performance_progress.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """
        )
        metrics_layout.addWidget(QLabel("Performance:"))
        metrics_layout.addWidget(self.performance_progress)

        self.seo_progress = QProgressBar()
        self.seo_progress.setRange(0, 100)
        self.seo_progress.setValue(0)
        self.seo_progress.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
            }
        """
        )
        metrics_layout.addWidget(QLabel("SEO:"))
        metrics_layout.addWidget(self.seo_progress)

        analysis_layout.addLayout(metrics_layout)

        metrics_layout2 = QHBoxLayout()

        self.accessibility_progress = QProgressBar()
        self.accessibility_progress.setRange(0, 100)
        self.accessibility_progress.setValue(0)
        self.accessibility_progress.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #FFC107;
            }
        """
        )
        metrics_layout2.addWidget(QLabel("Accessibility:"))
        metrics_layout2.addWidget(self.accessibility_progress)

        self.best_practices_progress = QProgressBar()
        self.best_practices_progress.setRange(0, 100)
        self.best_practices_progress.setValue(0)
        self.best_practices_progress.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #9C27B0;
            }
        """
        )
        metrics_layout2.addWidget(QLabel("Best Practices:"))
        metrics_layout2.addWidget(self.best_practices_progress)

        analysis_layout.addLayout(metrics_layout2)

        # Issues
        issues_label = QLabel("Issues:")
        self.issues_text = QTextEdit()
        self.issues_text.setReadOnly(True)
        self.issues_text.setMinimumHeight(80)

        analysis_layout.addWidget(issues_label)
        analysis_layout.addWidget(self.issues_text)

        details_layout.addWidget(analysis_group)

        lower_layout.addLayout(details_layout)

        # Add notes area
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)

        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Add notes about this business...")
        self.notes_text.textChanged.connect(self.on_notes_changed)

        notes_layout.addWidget(self.notes_text)

        action_layout = QHBoxLayout()

        self.open_website_button = QPushButton("Open Website")
        self.open_website_button.clicked.connect(self.on_open_website)
        action_layout.addWidget(self.open_website_button)

        self.save_notes_button = QPushButton("Save Notes")
        self.save_notes_button.clicked.connect(self.on_save_notes)
        action_layout.addWidget(self.save_notes_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.on_delete_business)
        self.delete_button.setStyleSheet("color: red;")
        action_layout.addWidget(self.delete_button)

        notes_layout.addLayout(action_layout)

        lower_layout.addWidget(notes_group)

        # Add widgets to splitter
        self.splitter.addWidget(upper_widget)
        self.splitter.addWidget(lower_widget)
        self.splitter.setSizes([400, 300])  # Default sizes

        # Status widget at the bottom
        self.status_layout = QHBoxLayout()
        self.result_count_label = QLabel("No results")
        self.result_count_label.setAlignment(Qt.AlignLeft)

        self.status_layout.addWidget(self.result_count_label)
        self.status_layout.addStretch()

        # Add buttons for export
        self.csv_button = QPushButton("Export CSV")
        self.csv_button.clicked.connect(self.on_export_csv)
        self.status_layout.addWidget(self.csv_button)

        self.report_button = QPushButton("Generate Report")
        self.report_button.clicked.connect(self.on_generate_report)
        self.status_layout.addWidget(self.report_button)

        main_layout.addLayout(self.status_layout)

        # Initially disable buttons until we have results
        self.update_buttons_state(False)

    def load_settings(self):
        """Load saved settings"""
        # Restore splitter state
        if self.settings.contains("results/splitter_state"):
            self.splitter.restoreState(self.settings.value("results/splitter_state"))

        # Restore filter settings
        priority_index = self.settings.value("results/priority_filter", 0, int)
        if 0 <= priority_index < self.priority_combo.count():
            self.priority_combo.setCurrentIndex(priority_index)

    def save_settings(self):
        """Save current settings"""
        self.settings.setValue("results/splitter_state", self.splitter.saveState())
        self.settings.setValue(
            "results/priority_filter", self.priority_combo.currentIndex()
        )

    def has_results(self):
        """Check if there are any results"""
        return self.model.rowCount() > 0

    def load_results(self):
        """Load results for the current location"""
        # Get the current location from settings
        location = self.settings.value("search/last_location", "")

        if not location:
            self.update_buttons_state(False)
            self.result_count_label.setText("No location specified")
            return

        self.current_location = location

        # Open the database
        db_dir = os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
        db_file = os.path.join(db_dir, f"leads_{location.replace(' ', '_')}.db")

        if not os.path.exists(db_file):
            self.update_buttons_state(False)
            self.result_count_label.setText(f"No results for {location}")
            return

        if self.current_database:
            self.current_database.close()

        self.current_database = LeadDatabase(db_file)

        # Load businesses
        businesses = self.current_database.get_all_businesses()

        # Update model
        self.model.load_data(businesses)

        # Update status
        self.result_count_label.setText(
            f"Found {len(businesses)} businesses in {location}"
        )

        # Enable buttons
        self.update_buttons_state(len(businesses) > 0)

        # Clear details
        self.clear_details()

    def update_buttons_state(self, has_results):
        """Update button states based on whether we have results"""
        self.csv_button.setEnabled(has_results)
        self.report_button.setEnabled(has_results)
        self.open_website_button.setEnabled(False)
        self.save_notes_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    def clear_details(self):
        """Clear business details panel"""
        self.name_label.setText("")
        self.type_label.setText("")
        self.address_label.setText("")
        self.phone_label.setText("")
        self.email_label.setText("")
        self.website_label.setText("")

        self.performance_progress.setValue(0)
        self.seo_progress.setValue(0)
        self.accessibility_progress.setValue(0)
        self.best_practices_progress.setValue(0)

        self.issues_text.clear()
        self.notes_text.clear()

        self.update_buttons_state(self.has_results())

    def show_business_details(self, business):
        """Show details for the selected business"""
        if not business:
            self.clear_details()
            return

        # Basic info
        self.name_label.setText(business.get("name", ""))
        self.type_label.setText(business.get("business_type", ""))
        self.address_label.setText(business.get("address", ""))
        self.phone_label.setText(business.get("phone", ""))
        self.email_label.setText(business.get("email", ""))

        # Website with clickable link
        website = business.get("website", "")
        if website:
            self.website_label.setText(f'<a href="{website}">{website}</a>')
            self.website_label.setOpenExternalLinks(True)
        else:
            self.website_label.setText("None")

        # Website metrics - Ensure we're passing integers to setValue
        self.performance_progress.setValue(
            int(business.get("performance_score", 0) or 0)
        )
        self.seo_progress.setValue(int(business.get("seo_score", 0) or 0))
        self.accessibility_progress.setValue(
            int(business.get("accessibility_score", 0) or 0)
        )
        self.best_practices_progress.setValue(
            int(business.get("best_practices_score", 0) or 0)
        )

        # Issues
        issues = business.get("issues", [])
        if isinstance(issues, list) and issues:
            self.issues_text.setHtml(
                "<ul>" + "".join([f"<li>{issue}</li>" for issue in issues]) + "</ul>"
            )
        else:
            self.issues_text.setPlainText("No issues detected.")

        # Notes
        self.notes_text.setPlainText(business.get("notes", ""))

        # Update buttons
        self.open_website_button.setEnabled(bool(website))
        self.save_notes_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    @Slot()
    def on_filter_changed(self):
        """Handle filter text change"""
        self.proxy_model.setFilterWildcard(self.filter_edit.text())

    @Slot(int)
    def on_priority_changed(self, index):
        """Handle priority filter change"""
        # Update filter proxy model based on the selected priority
        if index == 0:  # All
            # Reset to the default proxy model without custom filtering
            self.proxy_model = QSortFilterProxyModel()
            self.proxy_model.setSourceModel(self.model)
            self.proxy_model.setFilterKeyColumn(-1)  # Search all columns
            self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

            # Apply any existing text filter
            if self.filter_edit.text():
                self.proxy_model.setFilterWildcard(self.filter_edit.text())

            self.table_view.setModel(self.proxy_model)
        else:
            # Create a custom proxy model for priority filtering
            class PriorityProxyModel(QSortFilterProxyModel):
                def __init__(self, priority_value):
                    super().__init__()
                    self.priority_value = priority_value
                    self.filter_text = ""

                def setFilterWildcard(self, pattern):
                    self.filter_text = pattern
                    self.invalidateFilter()

                def filterAcceptsRow(self, source_row, source_parent):
                    # Get the business data for this row
                    index = self.sourceModel().index(source_row, 0, source_parent)
                    business = self.sourceModel().data(index, Qt.UserRole)

                    # Check if priority matches
                    priority_match = business.get("priority", 0) == self.priority_value

                    # If there's a text filter, apply that too
                    if self.filter_text:
                        text_match = False

                        # Check each column for text match
                        for column in range(self.sourceModel().columnCount()):
                            source_index = self.sourceModel().index(
                                source_row, column, source_parent
                            )
                            data = str(
                                self.sourceModel().data(source_index, Qt.DisplayRole)
                                or ""
                            )

                            if self.filter_text.lower() in data.lower():
                                text_match = True
                                break

                        return priority_match and text_match

                    return priority_match

            # Determine which priority value to filter by
            priority_value = index  # 1, 2, or 3 matching the combo box index

            # Create and apply the proxy model
            self.proxy_model = PriorityProxyModel(priority_value)
            self.proxy_model.setSourceModel(self.model)

            # Apply any existing text filter
            if self.filter_edit.text():
                self.proxy_model.setFilterWildcard(self.filter_edit.text())

            self.table_view.setModel(self.proxy_model)

            # Connect selection model signals
            self.table_view.selectionModel().selectionChanged.connect(
                self.on_selection_changed
            )

        # Save settings
        self.save_settings()

    @Slot()
    def on_selection_changed(self):
        """Handle table selection change"""
        indexes = self.table_view.selectionModel().selectedRows()
        if indexes:
            # Get the business data from the selected row
            proxy_index = indexes[0]
            source_index = self.proxy_model.mapToSource(proxy_index)
            business = self.model.data(source_index, Qt.UserRole)

            self.show_business_details(business)
        else:
            self.clear_details()

    @Slot()
    def on_notes_changed(self):
        """Handle notes text change"""
        # Enable save button
        self.save_notes_button.setEnabled(True)

    @Slot()
    def on_save_notes(self):
        """Save notes for the current business"""
        if not self.current_database:
            return

        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            return

        # Get the business data
        proxy_index = indexes[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        business = self.model.data(source_index, Qt.UserRole)

        if not business:
            return

        # Update notes
        business_id = business.get("id")
        notes = self.notes_text.toPlainText()

        success = self.current_database.update_business(business_id, {"notes": notes})

        if success:
            # Update model data
            business["notes"] = notes
            self.model.dataChanged.emit(source_index, source_index)

            QMessageBox.information(
                self, "Notes Saved", "Notes have been saved successfully."
            )
        else:
            QMessageBox.warning(self, "Error", "Failed to save notes.")

    @Slot()
    def on_open_website(self):
        """Open the website in default browser"""
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            return

        # Get the business data
        proxy_index = indexes[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        business = self.model.data(source_index, Qt.UserRole)

        if not business or not business.get("website"):
            return

        # Open website
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl

        url = business.get("website")
        QDesktopServices.openUrl(QUrl(url))

    @Slot()
    def on_delete_business(self):
        """Delete the selected business"""
        if not self.current_database:
            return

        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            return

        # Get the business data
        proxy_index = indexes[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        business = self.model.data(source_index, Qt.UserRole)

        if not business:
            return

        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{business.get('name')}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        # Delete business
        business_id = business.get("id")
        success = self.current_database.delete_business(business_id)

        if success:
            # Remove from model
            self.model.beginRemoveRows(
                QModelIndex(), source_index.row(), source_index.row()
            )
            self.model.businesses.pop(source_index.row())
            self.model.endRemoveRows()

            # Update status
            self.result_count_label.setText(
                f"Found {len(self.model.businesses)} businesses in {self.current_location}"
            )

            # Clear details
            self.clear_details()

            QMessageBox.information(
                self, "Deleted", "Business has been deleted successfully."
            )
        else:
            QMessageBox.warning(self, "Error", "Failed to delete business.")

    @Slot()
    def on_export_csv(self):
        """Export results to CSV"""
        if not self.current_database or not self.has_results():
            QMessageBox.information(self, "Export CSV", "No results to export.")
            return

        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            f"leads_{self.current_location}.csv",
            "CSV Files (*.csv)",
        )

        if not file_path:
            return

        # Create exporter
        exporter = LeadExporter(self.current_database)

        # Export
        count = exporter.export_to_csv(file_path)

        if count > 0:
            QMessageBox.information(
                self, "Export Successful", f"Exported {count} businesses to {file_path}"
            )
        else:
            QMessageBox.warning(self, "Export Failed", "Failed to export data.")

    @Slot()
    def on_generate_report(self):
        """Generate a detailed report"""
        if not self.current_database or not self.has_results():
            QMessageBox.information(self, "Generate Report", "No results to report.")
            return

        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            f"report_{self.current_location}.html",
            "HTML Files (*.html);;Text Files (*.txt)",
        )

        if not file_path:
            return

        # Create exporter
        exporter = LeadExporter(self.current_database)

        # Determine format from extension
        if file_path.lower().endswith(".html"):
            count = exporter.export_to_html(file_path)
        else:
            count = exporter.export_to_text(file_path)

        if count > 0:
            QMessageBox.information(
                self,
                "Report Generated",
                f"Report for {count} businesses saved to {file_path}",
            )

            # Open the file
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl

            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            QMessageBox.warning(
                self, "Report Generation Failed", "Failed to generate report."
            )
