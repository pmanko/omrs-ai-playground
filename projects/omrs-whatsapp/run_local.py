#!/usr/bin/env python3
"""Run the WhatsApp-OpenMRS-MedGemma service locally for development."""

import os
import sys
import subprocess

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_redis():
    """Check if Redis is running locally."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        print("✓ Redis is running on localhost:6379")
        return True
    except:
        print("✗ Redis is not running. Please start Redis first:")
        print("  - macOS: brew services start redis")
        print("  - Ubuntu: sudo systemctl start redis")
        print("  - Docker: docker run -d -p 6379:6379 redis:alpine")
        return False

def check_env():
    """Check if .env file exists."""
    if not os.path.exists('.env'):
        print("✗ .env file not found. Creating from .env.example...")
        subprocess.run(['cp', '.env.example', '.env'])
        print("  Please edit .env with your credentials before running.")
        return False
    print("✓ .env file found")
    return True

def main():
    """Run the service locally."""
    print("WhatsApp-OpenMRS-MedGemma Local Development Runner\n")
    
    # Check prerequisites
    if not check_env():
        sys.exit(1)
    
    if not check_redis():
        sys.exit(1)
    
    print("\nStarting service on http://localhost:8000")
    print("Press Ctrl+C to stop\n")
    
    # Run the service
    subprocess.run([
        sys.executable, '-m', 'src.main'
    ])

if __name__ == "__main__":
    main()