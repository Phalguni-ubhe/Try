import subprocess
import sys
import os
from pathlib import Path

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {str(e)}")
        sys.exit(1)

def main():
    print("Setting up Student API project...")
    
    # Create virtual environment
    print("\n1. Creating virtual environment...")
    run_command("python -m venv venv")
    
    # Determine the correct activate script based on OS
    if os.name == 'nt':  # Windows
        activate_script = ".\\venv\\Scripts\\activate"
    else:  # Unix/Linux/MacOS
        activate_script = "source ./venv/bin/activate"
      # Install required packages from requirements.txt
    print("\n2. Installing required packages from requirements.txt...")
    cmd = f"{activate_script} && python -m pip install -r requirements.txt"
    run_command(cmd)
    
    # Create Django project if it doesn't exist
    if not Path('manage.py').exists():
        print("\n4. Creating Django project...")
        run_command(f"{activate_script} && django-admin startproject student_api .")
    
    # Run migrations
    print("\n5. Running initial migrations...")
    run_command(f"{activate_script} && python manage.py migrate")
    
    print("\nSetup completed successfully!")
    print("\nTo start development:")
    print("1. Activate the virtual environment:")
    if os.name == 'nt':
        print("   .\\venv\\Scripts\\activate")
    else:
        print("   source ./venv/bin/activate")
    print("2. Run the development server:")
    print("   python manage.py runserver")

if __name__ == "__main__":
    main()
