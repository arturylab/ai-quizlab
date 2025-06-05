import csv
import random
import string
import os
import json
import io
from flask import send_file


def get_json_path(folder, filename):
    """Return the full path for a JSON file in a given folder."""
    return os.path.join(folder, filename)


def read_json(path):
    """Read and return JSON data from a file, or an empty list if not found."""
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading JSON file {path}: {e}")
    return []


def write_json(path, data):
    """Write data to a JSON file with error handling."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Error writing JSON file {path}: {e}")
        raise


def generate_random_password(length=8):
    """Generate a secure random password with letters and digits."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def create_csv_response(data, headers, filename):
    """Create a CSV response for file download."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(data)
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


def validate_form_data(data, required_fields):
    """Validate form data and return errors if any."""
    errors = []
    for field in required_fields:
        if not data.get(field, '').strip():
            errors.append(f"{field.title()} is required.")
    return errors