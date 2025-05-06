# Database operations
"""
Database module for storing and retrieving business leads
"""
import os
import sqlite3
import json
from datetime import datetime


class LeadDatabase:
    """Database manager for business leads"""
    
    def __init__(self, db_path="leads.db"):
        """Initialize the database connection"""
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish database connection"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            raise
    
    def _create_tables(self):
        """Create necessary database tables if they don't exist"""
        try:
            cursor = self.conn.cursor()
            
            # Businesses table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                city TEXT,
                postal_code TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                business_type TEXT,
                priority INTEGER DEFAULT 0,
                notes TEXT,
                discovered_date TEXT,
                last_updated TEXT
            )
            ''')
            
            # Website metrics table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS website_metrics (
                business_id INTEGER PRIMARY KEY,
                performance_score INTEGER DEFAULT 0,
                seo_score INTEGER DEFAULT 0,
                accessibility_score INTEGER DEFAULT 0,
                best_practices_score INTEGER DEFAULT 0,
                analysis_date TEXT,
                issues TEXT,  -- Stored as JSON
                FOREIGN KEY (business_id) REFERENCES businesses (id)
            )
            ''')
            
            # Contact attempts table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER,
                date TEXT,
                method TEXT,
                notes TEXT,
                outcome TEXT,
                FOREIGN KEY (business_id) REFERENCES businesses (id)
            )
            ''')
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            self.conn.rollback()
            raise
    
    def add_business(self, business_data):
        """
        Add a business to the database
        
        Args:
            business_data: Dictionary with business information
            
        Returns:
            ID of the inserted business
        """
        try:
            cursor = self.conn.cursor()
            
            # Prepare current timestamp
            now = datetime.now().isoformat()
            
            # Insert into businesses table
            cursor.execute('''
            INSERT INTO businesses (
                name, address, city, postal_code, phone, email, website, 
                business_type, priority, notes, discovered_date, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                business_data.get('name', ''),
                business_data.get('address', ''),
                business_data.get('city', ''),
                business_data.get('postal_code', ''),
                business_data.get('phone', ''),
                business_data.get('email', ''),
                business_data.get('website', ''),
                business_data.get('business_type', ''),
                business_data.get('priority', 0),
                business_data.get('notes', ''),
                now,
                now
            ))
            
            business_id = cursor.lastrowid
            
            # Insert metrics if available
            if any(key in business_data for key in [
                'performance_score', 'seo_score', 'accessibility_score', 'best_practices_score', 'issues'
            ]):
                # Convert issues list to JSON if present
                issues_json = json.dumps(business_data.get('issues', []))
                
                cursor.execute('''
                INSERT INTO website_metrics (
                    business_id, performance_score, seo_score, 
                    accessibility_score, best_practices_score,
                    analysis_date, issues
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    business_id,
                    business_data.get('performance_score', 0),
                    business_data.get('seo_score', 0),
                    business_data.get('accessibility_score', 0),
                    business_data.get('best_practices_score', 0),
                    now,
                    issues_json
                ))
            
            self.conn.commit()
            return business_id
            
        except sqlite3.Error as e:
            print(f"Error adding business: {e}")
            self.conn.rollback()
            return None
    
    def get_business(self, business_id):
        """
        Get a business by ID
        
        Args:
            business_id: ID of the business to retrieve
            
        Returns:
            Business data dictionary or None if not found
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT 
                b.*, 
                m.performance_score, m.seo_score, 
                m.accessibility_score, m.best_practices_score,
                m.analysis_date, m.issues
            FROM 
                businesses b
            LEFT JOIN 
                website_metrics m ON b.id = m.business_id
            WHERE 
                b.id = ?
            ''', (business_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
                
            # Convert to dictionary
            business = dict(row)
            
            # Parse JSON fields
            if business.get('issues'):
                try:
                    business['issues'] = json.loads(business['issues'])
                except:
                    business['issues'] = []
            
            return business
            
        except sqlite3.Error as e:
            print(f"Error retrieving business: {e}")
            return None
    
    def get_all_businesses(self, priority=None, search_term=None):
        """
        Get all businesses, optionally filtered
        
        Args:
            priority: Optional priority filter (1, 2, or 3)
            search_term: Optional search term for name/address
            
        Returns:
            List of business dictionaries
        """
        try:
            cursor = self.conn.cursor()
            
            query = '''
            SELECT 
                b.*, 
                m.performance_score, m.seo_score, 
                m.accessibility_score, m.best_practices_score
            FROM 
                businesses b
            LEFT JOIN 
                website_metrics m ON b.id = m.business_id
            '''
            
            params = []
            where_clauses = []
            
            if priority is not None:
                where_clauses.append("b.priority = ?")
                params.append(priority)
                
            if search_term:
                where_clauses.append('''
                (b.name LIKE ? OR b.address LIKE ? OR 
                 b.city LIKE ? OR b.postal_code LIKE ?)
                ''')
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                
            query += " ORDER BY b.priority, b.name"
            
            cursor.execute(query, params)
            
            businesses = [dict(row) for row in cursor.fetchall()]
            return businesses
            
        except sqlite3.Error as e:
            print(f"Error retrieving businesses: {e}")
            return []
    
    def update_business(self, business_id, business_data):
        """
        Update a business in the database
        
        Args:
            business_id: ID of the business to update
            business_data: Dictionary with updated business information
            
        Returns:
            Boolean indicating success
        """
        try:
            cursor = self.conn.cursor()
            
            # Update timestamp
            now = datetime.now().isoformat()
            
            # Build update query dynamically based on provided fields
            update_fields = []
            params = []
            
            fields = [
                'name', 'address', 'city', 'postal_code', 'phone', 
                'email', 'website', 'business_type', 'priority', 'notes'
            ]
            
            for field in fields:
                if field in business_data:
                    update_fields.append(f"{field} = ?")
                    params.append(business_data[field])
            
            # Add last_updated timestamp
            update_fields.append("last_updated = ?")
            params.append(now)
            
            # Add business_id to params
            params.append(business_id)
            
            if update_fields:
                query = f'''
                UPDATE businesses 
                SET {", ".join(update_fields)}
                WHERE id = ?
                '''
                
                cursor.execute(query, params)
            
            # Update metrics if provided
            metric_fields = [
                'performance_score', 'seo_score', 
                'accessibility_score', 'best_practices_score', 'issues'
            ]
            
            if any(field in business_data for field in metric_fields):
                # Check if metrics record exists
                cursor.execute(
                    "SELECT 1 FROM website_metrics WHERE business_id = ?", 
                    (business_id,)
                )
                
                metrics_exist = cursor.fetchone() is not None
                
                # Convert issues to JSON if present
                issues_json = None
                if 'issues' in business_data:
                    issues_json = json.dumps(business_data['issues'])
                
                if metrics_exist:
                    # Update existing metrics
                    update_fields = []
                    params = []
                    
                    for field in ['performance_score', 'seo_score', 'accessibility_score', 'best_practices_score']:
                        if field in business_data:
                            update_fields.append(f"{field} = ?")
                            params.append(business_data[field])
                    
                    if issues_json:
                        update_fields.append("issues = ?")
                        params.append(issues_json)
                    
                    # Add analysis date
                    update_fields.append("analysis_date = ?")
                    params.append(now)
                    
                    # Add business_id to params
                    params.append(business_id)
                    
                    if update_fields:
                        query = f'''
                        UPDATE website_metrics 
                        SET {", ".join(update_fields)}
                        WHERE business_id = ?
                        '''
                        
                        cursor.execute(query, params)
                else:
                    # Insert new metrics
                    cursor.execute('''
                    INSERT INTO website_metrics (
                        business_id, performance_score, seo_score, 
                        accessibility_score, best_practices_score,
                        analysis_date, issues
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        business_id,
                        business_data.get('performance_score', 0),
                        business_data.get('seo_score', 0),
                        business_data.get('accessibility_score', 0),
                        business_data.get('best_practices_score', 0),
                        now,
                        issues_json or '[]'
                    ))
            
            self.conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error updating business: {e}")
            self.conn.rollback()
            return False
    
    def delete_business(self, business_id):
        """
        Delete a business from the database
        
        Args:
            business_id: ID of the business to delete
            
        Returns:
            Boolean indicating success
        """
        try:
            cursor = self.conn.cursor()
            
            # Delete related metrics
            cursor.execute("DELETE FROM website_metrics WHERE business_id = ?", (business_id,))
            
            # Delete contact attempts
            cursor.execute("DELETE FROM contact_attempts WHERE business_id = ?", (business_id,))
            
            # Delete the business
            cursor.execute("DELETE FROM businesses WHERE id = ?", (business_id,))
            
            self.conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error deleting business: {e}")
            self.conn.rollback()
            return False
    
    def add_contact_attempt(self, business_id, method, notes, outcome):
        """
        Add a contact attempt record
        
        Args:
            business_id: ID of the business
            method: Contact method (email, phone, etc.)
            notes: Notes about the contact
            outcome: Outcome of the contact
            
        Returns:
            ID of the contact attempt or None on error
        """
        try:
            cursor = self.conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
            INSERT INTO contact_attempts (business_id, date, method, notes, outcome)
            VALUES (?, ?, ?, ?, ?)
            ''', (business_id, now, method, notes, outcome))
            
            self.conn.commit()
            return cursor.lastrowid
            
        except sqlite3.Error as e:
            print(f"Error adding contact attempt: {e}")
            self.conn.rollback()
            return None
    
    def get_contact_attempts(self, business_id):
        """
        Get all contact attempts for a business
        
        Args:
            business_id: ID of the business
            
        Returns:
            List of contact attempt dictionaries
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT * FROM contact_attempts
            WHERE business_id = ?
            ORDER BY date DESC
            ''', (business_id,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"Error retrieving contact attempts: {e}")
            return []
    
    def export_to_csv(self, filepath):
        """
        Export all businesses to CSV
        
        Args:
            filepath: Path to save the CSV file
            
        Returns:
            Number of exported records
        """
        try:
            import csv
            
            businesses = self.get_all_businesses()
            
            if not businesses:
                return 0
            
            # Determine fields to export
            fieldnames = [
                'id', 'name', 'address', 'city', 'postal_code', 'phone', 
                'email', 'website', 'business_type', 'priority', 'notes',
                'performance_score', 'seo_score', 'accessibility_score', 'best_practices_score'
            ]
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for business in businesses:
                    # Only write fields that are in fieldnames
                    row = {field: business.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            return len(businesses)
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return 0
    
    def export_to_text(self, filepath):
        """
        Export detailed business reports to a text file
        
        Args:
            filepath: Path to save the text file
            
        Returns:
            Number of exported records
        """
        try:
            businesses = self.get_all_businesses()
            
            if not businesses:
                return 0
            
            # Priority labels
            priority_labels = {
                1: "High Priority (No Website)",
                2: "Medium Priority (Poor Website)",
                3: "Low Priority (Good Website)"
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write("UK BUSINESS LEAD GENERATOR - DETAILED REPORT\n")
                file.write("=" * 50 + "\n\n")
                file.write(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write(f"Total businesses: {len(businesses)}\n\n")
                
                for business in businesses:
                    file.write("-" * 50 + "\n")
                    file.write(f"BUSINESS: {business.get('name', 'Unknown')}\n")
                    file.write(f"TYPE: {business.get('business_type', 'Unknown')}\n")
                    file.write(f"PRIORITY: {priority_labels.get(business.get('priority', 0), 'Unknown')}\n")
                    file.write(f"ADDRESS: {business.get('address', 'Unknown')}\n")
                    
                    if business.get('city'):
                        file.write(f"CITY: {business.get('city')}\n")
                    
                    if business.get('postal_code'):
                        file.write(f"POSTAL CODE: {business.get('postal_code')}\n")
                    
                    if business.get('phone'):
                        file.write(f"PHONE: {business.get('phone')}\n")
                    
                    if business.get('email'):
                        file.write(f"EMAIL: {business.get('email')}\n")
                    
                    if business.get('website'):
                        file.write(f"WEBSITE: {business.get('website')}\n")
                        
                        # Add website metrics if available
                        if business.get('performance_score') is not None:
                            file.write("\nWEBSITE ANALYSIS:\n")
                            file.write(f"  Performance: {business.get('performance_score')}%\n")
                            file.write(f"  SEO: {business.get('seo_score')}%\n")
                            file.write(f"  Accessibility: {business.get('accessibility_score')}%\n")
                            file.write(f"  Best Practices: {business.get('best_practices_score')}%\n")
                    
                    if business.get('notes'):
                        file.write(f"\nNOTES: {business.get('notes')}\n")
                    
                    # Get contact attempts
                    contact_attempts = self.get_contact_attempts(business.get('id'))
                    if contact_attempts:
                        file.write("\nCONTACT HISTORY:\n")
                        for attempt in contact_attempts:
                            file.write(f"  {attempt.get('date')}: {attempt.get('method')} - {attempt.get('outcome')}\n")
                            if attempt.get('notes'):
                                file.write(f"    Notes: {attempt.get('notes')}\n")
                    
                    file.write("\n")
            
            return len(businesses)
            
        except Exception as e:
            print(f"Error exporting to text: {e}")
            return 0
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()