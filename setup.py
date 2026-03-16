seup.py


# setup_simple.py
import os
import subprocess
import sys

def create_structure():
    print("=== Pneumonia Detection App Setup ===")
    
    # Create folders
    folders = [
        'static/css', 'static/js', 'static/images', 'static/reports',
        'templates', 'uploads', 'models', 'utils', 'config', 'tests', 'logs'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"Created folder: {folder}")
    
    # Create empty files
    files_to_create = [
        'utils/__init__.py', 'config/__init__.py', 'tests/__init__.py',
        'static/reports/.gitkeep', 'uploads/.gitkeep', 'models/.gitkeep', 'logs/.gitkeep'
    ]
    
    for file in files_to_create:
        with open(file, 'w') as f:
            pass
        print(f"Created file: {file}")
    
    # Create requirements.txt
    requirements = """Flask==2.3.3
tensorflow==2.13.0
Pillow==10.0.0
reportlab==4.0.4
numpy==1.24.3"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    print("Created: requirements.txt")
    
    # Create .gitignore
    gitignore = """__pycache__/
*.pyc
uploads/*
static/reports/*.pdf
*.h5"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore)
    print("Created: .gitignore")
    
    print("\n=== Installing Dependencies ===")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
    except:
        print("Please run: pip install -r requirements.txt")
    
    print("\n=== SETUP COMPLETE ===")
    print("Run: python app.py")

if __name__ == "__main__":
    create_structure()