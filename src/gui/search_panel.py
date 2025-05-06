"""
Search settings panel
"""

import os
import threading
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QProgressBar,
    QGroupBox,
    QRadioButton,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal, Slot, QSettings

from src.core.scraper import BusinessScraper
from src.core.analyzer import WebsiteAnalyzer
from src.core.database import LeadDatabase
from src.utils.helpers import validate_uk_location


class SearchPanel(QWidget):
    """Search panel for configuring and starting lead generation"""

    # Signals
    search_started = Signal()
    search_completed = Signal(int)  # int: number of results
    search_error = Signal(str)  # str: error message

    def __init__(self):
        super().__init__()

        # Initialize settings
        self.settings = QSettings("UK Business Lead Generator", "LeadGen")

        # Set up UI
        self.setup_ui()

        # Load settings
        self.load_settings()

        # Initialize thread reference
        self.search_thread = None

    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout(self)

        # Create form layout for search options
        form_layout = QFormLayout()

        # Location field
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Enter city, town, or postal code")
        form_layout.addRow("Location:", self.location_input)

        # Category field
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems(
            [
                "All Businesses",
                "Restaurants",
                "Retail Shops",
                "Hotels",
                "Cafes",
                "Pubs",
                "Beauty Salons",
                "Estate Agents",
                "Solicitors",
                "Accountants",
                "Doctors",
                "Dentists",
                "Plumbers",
                "Electricians",
                "Builders",
            ]
        )
        form_layout.addRow("Business Category:", self.category_input)

        # Limit field
        self.limit_input = QSpinBox()
        self.limit_input.setRange(5, 100)
        self.limit_input.setValue(20)
        self.limit_input.setSingleStep(5)
        form_layout.addRow("Maximum Results:", self.limit_input)

        # Add form to main layout
        main_layout.addLayout(form_layout)

        # Options group
        options_group = QGroupBox("Search Options")
        options_layout = QVBoxLayout(options_group)

        # Website analysis options
        self.analyze_websites_checkbox = QCheckBox("Analyze Websites")
        self.analyze_websites_checkbox.setChecked(True)
        options_layout.addWidget(self.analyze_websites_checkbox)

        # Priority options
        priority_layout = QHBoxLayout()
        priority_label = QLabel("Focus on:")
        priority_layout.addWidget(priority_label)

        self.priority_all_radio = QRadioButton("All Businesses")
        self.priority_no_website_radio = QRadioButton("No Website")
        self.priority_poor_website_radio = QRadioButton("Poor Website")

        self.priority_all_radio.setChecked(True)

        priority_layout.addWidget(self.priority_all_radio)
        priority_layout.addWidget(self.priority_no_website_radio)
        priority_layout.addWidget(self.priority_poor_website_radio)

        options_layout.addLayout(priority_layout)

        main_layout.addWidget(options_group)

        # Search button and progress bar
        button_layout = QHBoxLayout()

        self.search_button = QPushButton("Generate Leads")
        self.search_button.clicked.connect(self.on_search_clicked)
        button_layout.addWidget(self.search_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        button_layout.addWidget(self.progress_bar)

        main_layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel()
        main_layout.addWidget(self.status_label)

        # Add stretch at the end
        main_layout.addStretch()

    def start_search(self, location, category, limit, analyze_websites, priority_focus):
        """Start the search process in a background thread"""
        # Update UI
        self.search_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Initializing search...")

        # Emit search started signal
        self.search_started.emit()

        # Start search thread
        self.search_thread = threading.Thread(
            target=self.perform_search,
            args=(location, category, limit, analyze_websites, priority_focus),
        )
        self.search_thread.daemon = True
        self.search_thread.start()

    def load_settings(self):
        """Load saved settings"""
        self.location_input.setText(self.settings.value("search/last_location", ""))

        category_index = self.settings.value("search/last_category_index", 0, int)
        if 0 <= category_index < self.category_input.count():
            self.category_input.setCurrentIndex(category_index)

        self.limit_input.setValue(self.settings.value("search/limit", 20, int))
        self.analyze_websites_checkbox.setChecked(
            self.settings.value("search/analyze_websites", True, bool)
        )

        priority_focus = self.settings.value("search/priority_focus", "all")
        if priority_focus == "no_website":
            self.priority_no_website_radio.setChecked(True)
        elif priority_focus == "poor_website":
            self.priority_poor_website_radio.setChecked(True)
        else:
            self.priority_all_radio.setChecked(True)

    def save_settings(self):
        """Save current settings"""
        self.settings.setValue("search/last_location", self.location_input.text())
        self.settings.setValue(
            "search/last_category_index", self.category_input.currentIndex()
        )
        self.settings.setValue("search/limit", self.limit_input.value())
        self.settings.setValue(
            "search/analyze_websites", self.analyze_websites_checkbox.isChecked()
        )

        if self.priority_no_website_radio.isChecked():
            self.settings.setValue("search/priority_focus", "no_website")
        elif self.priority_poor_website_radio.isChecked():
            self.settings.setValue("search/priority_focus", "poor_website")
        else:
            self.settings.setValue("search/priority_focus", "all")

    def clear_form(self):
        """Clear the search form"""
        self.location_input.clear()
        self.category_input.setCurrentIndex(0)
        self.limit_input.setValue(20)
        self.analyze_websites_checkbox.setChecked(True)
        self.priority_all_radio.setChecked(True)
        self.status_label.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

    def update_status(self, message, progress):
        """Update status and progress from the background thread"""
        from PySide6.QtCore import QMetaObject, Qt, Q_ARG

        # Update status label
        QMetaObject.invokeMethod(
            self.status_label, "setText", Qt.QueuedConnection, Q_ARG(str, message)
        )

        # Update progress bar
        QMetaObject.invokeMethod(
            self.progress_bar, "setValue", Qt.QueuedConnection, Q_ARG(int, progress)
        )

    @Slot()
    def on_search_clicked(self):
        """Handle search button click"""
        # Get search parameters
        location = self.location_input.text().strip()

        # Validate location
        if not location:
            QMessageBox.warning(self, "Missing Location", "Please enter a location.")
            return

        if not validate_uk_location(location):
            result = QMessageBox.question(
                self,
                "Confirm Location",
                f"The location '{location}' doesn't look like a standard UK location format. "
                "Are you sure this is a valid UK location?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if result != QMessageBox.Yes:
                return

        # Get other parameters
        category = self.category_input.currentText()
        if category == "All Businesses":
            category = None

        limit = self.limit_input.value()
        analyze_websites = self.analyze_websites_checkbox.isChecked()

        # Determine priority focus
        if self.priority_no_website_radio.isChecked():
            priority_focus = "no_website"
        elif self.priority_poor_website_radio.isChecked():
            priority_focus = "poor_website"
        else:
            priority_focus = "all"

        # Save settings
        self.save_settings()

        # Start search in a background thread
        self.start_search(location, category, limit, analyze_websites, priority_focus)

    def perform_search(
        self, location, category, limit, analyze_websites, priority_focus
    ):
        """Perform search operation in the background thread"""
        try:
            # Create database for this location
            db_dir = os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
            os.makedirs(db_dir, exist_ok=True)

            db_file = os.path.join(db_dir, f"leads_{location.replace(' ', '_')}.db")
            database = LeadDatabase(db_file)

            # Update status
            self.update_status("Initializing scraper...", 5)

            # Create scraper
            scraper = BusinessScraper(use_selenium=True)

            # Create analyzer if needed
            analyzer = None
            if analyze_websites:
                self.update_status("Initializing website analyzer...", 10)
                analyzer = WebsiteAnalyzer(use_lighthouse=True)

            # Start search
            self.update_status(f"Searching for businesses in {location}...", 15)

            businesses = scraper.find_businesses(location, category, limit)

            if not businesses:
                self.update_status("No businesses found.", 100)
                self.search_completed.emit(0)
                self.search_button.setEnabled(True)
                return

            # Update status
            self.update_status(f"Found {len(businesses)} businesses. Processing...", 35)

            # Keep track of businesses to add to database
            businesses_to_add = []

            # Process each business
            for i, business in enumerate(businesses):
                progress = 35 + int(55 * (i + 1) / len(businesses))
                self.update_status(
                    f"Processing {business['name']} ({i+1}/{len(businesses)})...",
                    progress,
                )

                # Set default priority (will be updated if we analyze the website)
                if "website" not in business or not business["website"]:
                    business["priority"] = 1  # No website
                    business["notes"] = "No website detected"

                    # If we're focusing on businesses with no websites, add this one
                    if priority_focus == "all" or priority_focus == "no_website":
                        businesses_to_add.append(business)
                else:
                    # For businesses with websites
                    try:
                        if analyze_websites:
                            # Analyze website
                            analysis_results = analyzer.analyze_website(
                                business["website"]
                            )

                            # Update business with analysis results
                            business.update(analysis_results)

                            # Check if we should include this business based on priority focus
                            if priority_focus == "all":
                                businesses_to_add.append(business)
                            elif (
                                priority_focus == "poor_website"
                                and business["priority"] == 2
                            ):
                                businesses_to_add.append(business)
                            elif (
                                priority_focus == "no_website"
                                and business["priority"] == 1
                            ):
                                businesses_to_add.append(business)
                        else:
                            # Default priority without analysis
                            business["priority"] = (
                                2  # Assume poor website until proven otherwise
                            )

                            # Check if we should include this business based on priority focus
                            if (
                                priority_focus == "all"
                                or priority_focus == "poor_website"
                            ):
                                businesses_to_add.append(business)
                    except Exception as e:
                        business["notes"] = f"Error analyzing website: {str(e)}"

                        # Set default priority for analysis failures
                        business["priority"] = 2  # Assume poor website

                        # Check if we should include this business based on priority focus
                        if priority_focus == "all" or priority_focus == "poor_website":
                            businesses_to_add.append(business)

            # Add all filtered businesses to database
            for business in businesses_to_add:
                database.add_business(business)

            # Final update
            businesses = database.get_all_businesses()
            self.update_status(
                f"Search completed. Found {len(businesses)} businesses.", 100
            )

            # Clean up
            database.close()
            if scraper:
                scraper.close()

            # Emit completed signal
            self.search_completed.emit(len(businesses))

        except Exception as e:
            # Log and emit error
            import traceback

            traceback.print_exc()
            self.search_error.emit(str(e))

        finally:
            # Update UI from main thread
            from PySide6.QtCore import QMetaObject, Qt, Q_ARG

            QMetaObject.invokeMethod(
                self.search_button, "setEnabled", Qt.QueuedConnection, Q_ARG(bool, True)
            )
