"""
Launcher script for Stock OHLC Analysis Admin Dashboard
Checks and installs required packages, then runs the dashboard.
"""

import subprocess
import sys
import os

REQUIRED_PACKAGES = {
    'yfinance': 'yfinance>=0.2.28',
    'pandas': 'pandas>=2.0.0',
    'streamlit': 'streamlit>=1.28.0'
}

def check_package_installed(package_name):
    """Check if a package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def install_package(package_spec):
    """Install a package using pip."""
    print(f"Installing {package_spec}...", end=" ", flush=True)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_spec],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓")
            return True
        else:
            print("✗")
            print(f"  Error: {result.stderr}")
            return False
    except Exception as e:
        print("✗")
        print(f"  Error: {e}")
        return False

def check_and_install_packages():
    """Check all required packages and install missing ones."""
    print("=" * 60)
    print("Stock OHLC Dashboard - Package Checker")
    print("=" * 60)
    print()
    
    missing_packages = []
    
    # Check each required package
    for package_name, package_spec in REQUIRED_PACKAGES.items():
        print(f"Checking {package_name}...", end=" ")
        if check_package_installed(package_name):
            print("✓ Installed")
        else:
            print("✗ Missing")
            missing_packages.append(package_spec)
    
    print()
    
    # Install missing packages
    if missing_packages:
        print(f"Installing {len(missing_packages)} missing package(s)...")
        print()
        
        for package_spec in missing_packages:
            if not install_package(package_spec):
                print(f"\n❌ Failed to install {package_spec}")
                print("Please install manually using: pip install -r requirements.txt")
                return False
        
        print()
        print("All packages installed successfully!")
    else:
        print("All required packages are already installed!")
    
    print("=" * 60)
    print()
    return True

def run_dashboard():
    """Run the main dashboard application."""
    print("Starting Stock OHLC Analysis Admin Dashboard...")
    print()
    print("The dashboard will open in your default web browser.")
    print("If it doesn't open automatically, go to: http://localhost:8501")
    print()
    print("Press Ctrl+C to stop the server.")
    print()
    
    try:
        # Run Streamlit app
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard.py"])
        return True
    except KeyboardInterrupt:
        print("\n\nDashboard closed by user.")
        return True
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")
        return False

def main():
    """Main launcher function."""
    # Check if dashboard.py exists
    if not os.path.exists("dashboard.py"):
        print("❌ Error: dashboard.py not found!")
        print("Please make sure you're running this script from the project directory.")
        sys.exit(1)
    
    # Check and install packages
    if not check_and_install_packages():
        print("\n❌ Package installation failed. Please fix the errors above.")
        sys.exit(1)
    
    # Run the dashboard
    run_dashboard()

if __name__ == "__main__":
    main()

