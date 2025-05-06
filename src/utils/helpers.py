# Helper functions
"""
Helper functions for the UK Business Lead Generator
"""
import re
import time
import datetime
import logging
import os
import sys
import json
import requests
from urllib.parse import urlparse

def validate_uk_location(location):
    """
    Validate if the provided string is a valid UK location
    
    Args:
        location: Location string to validate
        
    Returns:
        Boolean indicating if location appears valid
    """
    # Empty check
    if not location or not location.strip():
        return False
    
    # If it's a UK postcode format
    uk_postcode_pattern = r'^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$'
    if re.match(uk_postcode_pattern, location.upper()):
        return True
    
    # If it's a major UK city or town
    major_uk_locations = [
        'london', 'manchester', 'birmingham', 'liverpool', 'leeds', 
        'glasgow', 'edinburgh', 'cardiff', 'belfast', 'bristol',
        'newcastle', 'sheffield', 'nottingham', 'leicester', 'coventry',
        'bradford', 'brighton', 'southampton', 'plymouth', 'reading',
        'derby', 'wolverhampton', 'hull', 'portsmouth', 'oxford',
        'cambridge', 'york', 'swansea', 'dundee', 'aberdeen'
    ]
    
    if location.lower() in major_uk_locations:
        return True
    
    # If it's at least a reasonable length and contains only valid characters
    if len(location) >= 3 and re.match(r'^[a-zA-Z\s\-\']+$', location):
        return True
        
    return False

def clean_url(url):
    """
    Clean and normalize a URL
    
    Args:
        url: URL string to clean
        
    Returns:
        Cleaned URL string
    """
    if not url:
        return ""
        
    # Ensure URL has a scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Parse URL to clean components
    try:
        parsed = urlparse(url)
        
        # Rebuild URL with normalized components
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        if parsed.query:
            clean_url += f"?{parsed.query}"
            
        # Remove trailing slash
        if clean_url.endswith('/'):
            clean_url = clean_url[:-1]
            
        return clean_url
        
    except Exception as e:
        logging.warning(f"Error cleaning URL {url}: {str(e)}")
        return url

def extract_phone_number(text):
    """
    Extract a phone number from text
    
    Args:
        text: Text possibly containing a phone number
        
    Returns:
        Extracted phone number or None
    """
    if not text:
        return None
        
    # UK phone number patterns
    patterns = [
        r'(?:(?:\+44\s?[0-9]{4}|\(?0[0-9]{4}\)?)\s?[0-9]{3}\s?[0-9]{3})',  # +44 7700 900000
        r'(?:(?:\+44\s?[0-9]{3}|\(?0[0-9]{3}\)?)\s?[0-9]{3}\s?[0-9]{4})',  # +44 121 234 5678
        r'(?:(?:\+44\s?[0-9]{2}|\(?0[0-9]{2}\)?)\s?[0-9]{4}\s?[0-9]{4})',  # +44 20 1234 5678
        r'(?:\+44\s?7[0-9]{3}|(?:^|\s)07[0-9]{3})\s?[0-9]{6}',           # +44 7123 456789
        r'(?:\+44\s?7[0-9]{9})',                                  # +44 7123456789
        r'\b[0-9]{5}\s?[0-9]{5,6}\b'                                 # 01234 567890
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return None

def extract_email(text):
    """
    Extract an email from text
    
    Args:
        text: Text possibly containing an email
        
    Returns:
        Extracted email or None
    """
    if not text:
        return None
        
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    
    if match:
        return match.group(0)
    
    return None

def extract_postcode(text):
    """
    Extract a UK postcode from text
    
    Args:
        text: Text possibly containing a postcode
        
    Returns:
        Extracted postcode or None
    """
    if not text:
        return None
        
    # UK postcode pattern
    uk_postcode = r'[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}'
    match = re.search(uk_postcode, text.upper())
    
    if match:
        postcode = match.group(0)
        
        # Format postcode with proper spacing
        if ' ' not in postcode:
            inward = postcode[-3:]
            outward = postcode[:-3]
            postcode = f"{outward} {inward}"
            
        return postcode
    
    return None

def format_business_type(business_type):
    """
    Format business type consistently
    
    Args:
        business_type: Business type string
        
    Returns:
        Formatted business type string
    """
    if not business_type:
        return "Business"
        
    # Remove common words like "in", "and", etc.
    common_words = ['in', 'and', 'the', 'a', 'an', 'of', 'for']
    
    words = business_type.split()
    filtered_words = [w for w in words if w.lower() not in common_words]
    
    if not filtered_words:
        return "Business"
    
    # Title case each word
    formatted = ' '.join(word.capitalize() for word in filtered_words)
    
    return formatted

def rate_limit_sleep(min_seconds=0.5, max_seconds=2.0):
    """
    Sleep for a random duration to avoid rate limiting
    
    Args:
        min_seconds: Minimum sleep time
        max_seconds: Maximum sleep time
    """
    import random
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    
    Args:
        relative_path: Path relative to the script
        
    Returns:
        Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)

def setup_logging(log_dir=None):
    """
    Set up logging configuration
    
    Args:
        log_dir: Directory to store log files
    """
    if not log_dir:
        log_dir = os.path.join(os.path.expanduser("~"), "UKLeadGen", "logs")
        
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"leadgen_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )