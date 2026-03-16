# utils/helpers.py
import os
import logging
from PIL import Image
import base64
from io import BytesIO

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, upload_folder='uploads'):
    """Save uploaded file and return path"""
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    filename = f"temp_{os.urandom(8).hex()}.jpg"
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    return file_path

def cleanup_file(file_path):
    """Remove temporary files"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ Cleaned up: {file_path}")
    except Exception as e:
        logging.error(f"Error cleaning up file {file_path}: {e}")

def image_to_base64(img):
    """Convert PIL image to base64 string"""
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def validate_patient_data(patient_data):
    """Validate patient information"""
    errors = []
    
    if not patient_data.get('name') or len(patient_data['name'].strip()) < 2:
        errors.append("Patient name is required and should be at least 2 characters")
    
    if not patient_data.get('age') or not patient_data['age'].isdigit():
        errors.append("Valid age is required")
    elif int(patient_data['age']) < 1 or int(patient_data['age']) > 120:
        errors.append("Age must be between 1 and 120")
    
    return errors