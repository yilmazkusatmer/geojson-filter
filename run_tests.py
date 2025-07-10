#!/usr/bin/env python3
"""
Test Runner for YIKU-GeoFilter

Executes all unit tests and generates coverage reports.
Usage: python run_tests.py
"""

import subprocess
import sys
import os


def run_tests():
    """Run all tests with coverage reporting"""
    print("🧪 Running YIKU-GeoFilter Unit Tests...")
    print("=" * 50)
    
    # Ensure we're in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Run pytest with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "--verbose",
            "--cov=backend",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-fail-under=90"
        ], capture_output=False, text=True)
        
        print("\n" + "=" * 50)
        
        if result.returncode == 0:
            print("✅ ALL TESTS PASSED!")
            print("📊 Coverage report generated in: htmlcov/index.html")
        else:
            print("❌ SOME TESTS FAILED!")
            sys.exit(1)
            
    except FileNotFoundError:
        print("❌ pytest not found. Install dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    run_tests() 