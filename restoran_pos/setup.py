#!/usr/bin/env python
"""
Setup script to initialize the restaurant POS system with default data.
Run this after migrations: python setup.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restoran.settings')
django.setup()

from pos.models import Table, Category, MenuItem, Settings
from django.contrib.auth.models import User
from pos.models import UserProfile


def create_tables():
    """Create default tables (1-20)"""
    print("Creating tables...")
    for i in range(1, 21):
        Table.objects.get_or_create(number=i)
    print(f"Created {Table.objects.count()} tables")


def create_categories():
    """Create default menu categories"""
    print("Creating categories...")
    categories = [
        ('salad', 'Salatlar'),
        ('soup', "Sho'rvalar"),
        ('main', 'Asosiy'),
        ('drink', 'Ichimliklar'),
        ('dessert', 'Desertlar'),
    ]
    for slug, name in categories:
        Category.objects.get_or_create(slug=slug, defaults={'name': name})
    print(f"Created {Category.objects.count()} categories")


def create_menu_items():
    """Create default menu items"""
    print("Creating menu items...")
    items = [
        (1, 'Olivye salati', 25000, 'salad'),
        (2, 'Sezar salati', 35000, 'salad'),
        (3, 'Mastava', 20000, 'soup'),
        (4, "Sho'rva", 22000, 'soup'),
        (5, 'Osh', 45000, 'main'),
        (6, 'Manti (4 dona)', 40000, 'main'),
        (7, 'Shashlik (1 kg)', 120000, 'main'),
        (8, "Lag'mon", 35000, 'main'),
        (9, 'Coca-Cola 1L', 12000, 'drink'),
        (10, "Choy (ko'k)", 5000, 'drink'),
        (11, 'Sharbat', 15000, 'drink'),
        (12, 'Medovik', 18000, 'dessert'),
        (13, 'Napaleon', 20000, 'dessert'),
        (14, 'Chuchvara', 30000, 'soup'),
        (15, "Baranina sho'rva", 28000, 'soup'),
    ]

    for id, name, price, cat_slug in items:
        category = Category.objects.get(slug=cat_slug)
        MenuItem.objects.get_or_create(
            id=id,
            defaults={'name': name, 'price': price, 'category': category}
        )
    print(f"Created {MenuItem.objects.count()} menu items")


def create_settings():
    '''Create default settings'''
    print("Creating settings...")
    Settings.objects.get_or_create(
        key='tax_rate',
        defaults={'value': '12', 'description': 'QQS stavkasi (%)'}
    )
    print("Default settings created")


def create_default_users():
    """Create default admin and waiter users"""
    print("Creating default users...")

    # Admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={'first_name': 'Admin', 'is_staff': True, 'is_superuser': True}
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        UserProfile.objects.get_or_create(user=admin_user, defaults={'role': 'admin'})
        print("Created admin user (admin/admin123)")

    # Waiter users
    waiters = [
        ('waiter1', 'Ali', '1234'),
        ('waiter2', 'Vali', '1234'),
    ]

    for username, name, password in waiters:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'first_name': name}
        )
        if created:
            user.set_password(password)
            user.save()
            UserProfile.objects.get_or_create(user=user, defaults={'role': 'waiter'})
            print(f"Created waiter user {username} ({name}/{password})")


if __name__ == '__main__':
    print("=" * 50)
    print("Restoran POS - Setup Script")
    print("=" * 50)

    create_tables()
    create_categories()
    create_menu_items()
    create_default_users()

    print("=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print("\nDefault logins:")
    print("  Admin:    admin / admin123")
    print("  Waiter 1: waiter1 / 1234")
    print("  Waiter 2: waiter2 / 1234")
