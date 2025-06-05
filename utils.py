import csv
import random
import string
import os
import json
import io
from flask import send_file

# ============================================================================
# FILE PATH UTILITIES
# ============================================================================

def get_json_path(folder, filename):
    """
    Return the full path for a JSON file in a given folder.
    
    Args:
        folder (str): Directory path where the file is located
        filename (str): Name of the JSON file
        
    Returns:
        str: Complete file path combining folder and filename
    """
    return os.path.join(folder, filename)

# ============================================================================
# JSON FILE OPERATIONS
# ============================================================================

def read_json(path):
    """
    Read and return JSON data from a file, or an empty list if not found.
    
    Args:
        path (str): Path to the JSON file to read
        
    Returns:
        list or dict: Parsed JSON data, or empty list if file doesn't exist or parsing fails
    """
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading JSON file {path}: {e}")
    return []

def write_json(path, data):
    """
    Write data to a JSON file with error handling and directory creation.
    
    Args:
        path (str): Path where the JSON file will be written
        data (dict or list): Data to be serialized to JSON
        
    Raises:
        IOError: If file writing fails after creating necessary directories
    """
    try:
        # Ensure directory exists before writing file
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Write JSON data with proper encoding and formatting
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Error writing JSON file {path}: {e}")
        raise

# ============================================================================
# PASSWORD GENERATION UTILITIES
# ============================================================================

def generate_random_password(length=8):
    """
    Generate a secure random password with letters and digits.
    
    Args:
        length (int, optional): Length of the password to generate. Defaults to 8.
        
    Returns:
        str: Randomly generated password containing uppercase, lowercase letters and digits
    """
    # Use both letters (upper/lower case) and digits for security
    character_pool = string.ascii_letters + string.digits
    return ''.join(random.choices(character_pool, k=length))

# ============================================================================
# CSV DOWNLOAD UTILITIES
# ============================================================================

def create_csv_response(data, headers, filename):
    """
    Create a CSV response for file download via Flask.
    
    Args:
        data (list): List of rows, where each row is a list of column values
        headers (list): List of column header names
        filename (str): Name for the downloaded file
        
    Returns:
        flask.Response: Flask response object configured for CSV file download
    """
    # Create in-memory CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers and data rows
    writer.writerow(headers)
    writer.writerows(data)
    output.seek(0)
    
    # Convert to bytes and create downloadable response
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

# ============================================================================
# FORM VALIDATION UTILITIES
# ============================================================================

def validate_form_data(data, required_fields):
    """
    Validate form data and return list of validation errors.
    
    Args:
        data (dict): Form data dictionary to validate
        required_fields (list): List of field names that are required
        
    Returns:
        list: List of error messages for missing or empty fields
    """
    errors = []
    
    # Check each required field for presence and non-empty content
    for field in required_fields:
        field_value = data.get(field, '').strip()
        if not field_value:
            # Create user-friendly error message with capitalized field name
            errors.append(f"{field.title()} is required.")
    
    return errors