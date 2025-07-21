#!/usr/bin/env python3
"""
NFL QB Touchdown Predictor - Setup Script

A simple setup script for beginners to get started with the project.

Author: Shelton Bumhe
"""

import os
import sys
import subprocess
import platform

def print_banner():
    """Print the project banner."""
    print("=" * 60)
    print(" NFL QB Touchdown Predictor - Setup")
    print("=" * 60)
    print("A database-driven machine learning project for predicting")
    print("NFL quarterback touchdowns using historical data.")
    print("=" * 60)

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Python 3.8 or higher is required!")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f" Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def install_requirements():
    """Install required packages."""
    print("\n📦 Installing required packages...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print(" Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        return False

def check_data_files():
    """Check if data files exist."""
    print("\n Checking data files...")
    
    required_files = [
        "data/raw/Basic_Stats.csv",
        "data/raw/Game_Logs_Quarterback.csv",
        "data/raw/Career_Stats_Passing.csv"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"{file_path}")
    
    if missing_files:
        print(" Missing data files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        print("\nPlease ensure all CSV files are in the data/raw/ directory.")
        return False
    
    print("All data files found!")
    return True

def run_initial_setup():
    """Run the initial project setup."""
    print("\n🚀 Running initial project setup...")
    
    try:
        # Run the main script to set up database and preprocess data
        result = subprocess.run([
            sys.executable, "main.py", "--workflow"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(" Project setup completed successfully!")
            return True
        else:
            print("Project setup failed!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f" Error during setup: {e}")
        return False

def show_next_steps():
    """Show next steps for the user."""
    print("\n" + "=" * 60)
    print("� Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1.  Launch the app:")
    print("   python main.py --app")
    print("\n2.  Check project status:")
    print("   python main.py --status")
    print("\n3.  Re-run setup (if needed):")
    print("   python main.py --workflow --force-reload")
    print("\n4.  Read the README for more information")
    print("\nThe app will be available at: http://localhost:8501")
    print("=" * 60)

def main():
    """Main setup function."""
    print_banner()
    
    # Step 1: Check Python version
    if not check_python_version():
        return 1
    
    # Step 2: Install requirements
    if not install_requirements():
        return 1
    
    # Step 3: Check data files
    if not check_data_files():
        return 1
    
    # Step 4: Run initial setup
    if not run_initial_setup():
        return 1
    
    # Step 5: Show next steps
    show_next_steps()
    
    return 0

if __name__ == "__main__":
    exit(main()) 
