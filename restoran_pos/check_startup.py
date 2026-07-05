#!/usr/bin/env python
"""
Django startup verification script
"""
import os
import sys
import django

# Add the restoran_pos directory to Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restoran.settings')

print("=" * 50)
print("Django Startup Verification")
print("=" * 50)
print(f"Python version: {sys.version}")
print(f"Django version: {django.get_version()}")
print(f"BASE_DIR: {BASE_DIR}")
print(f"Python path: {sys.path[:3]}")

try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)

try:
    from restoran.wsgi import application
    print("✓ WSGI application imported successfully")
except Exception as e:
    print(f"✗ WSGI import failed: {e}")
    sys.exit(1)

try:
    from django.core.management import execute_from_command_line
    from django.core.wsgi import get_wsgi_application
    app = get_wsgi_application()
    print("✓ WSGI get_wsgi_application() successful")
except Exception as e:
    print(f"✗ WSGI application creation failed: {e}")
    sys.exit(1)

print("=" * 50)
print("All checks passed!")
print("=" * 50)
