from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from pos.models import Category, MenuItem, Settings, Table, UserProfile


class Command(BaseCommand):
    help = 'Create default tables, menu categories, menu items, settings, and users.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help='Reset passwords for default users to the documented defaults.',
        )

    def handle(self, *args, **options):
        self.create_tables()
        self.create_categories()
        self.create_menu_items()
        self.create_settings()
        self.create_default_users(reset_passwords=options['reset_passwords'])
        self.stdout.write(self.style.SUCCESS('Default data is ready.'))

    def create_tables(self):
        for number in range(1, 21):
            Table.objects.get_or_create(number=number)

    def create_categories(self):
        categories = [
            ('salad', 'Salatlar'),
            ('soup', "Sho'rvalar"),
            ('main', 'Asosiy'),
            ('drink', 'Ichimliklar'),
            ('dessert', 'Desertlar'),
        ]
        for slug, name in categories:
            Category.objects.get_or_create(slug=slug, defaults={'name': name})

    def create_menu_items(self):
        items = [
            ('Olivye salati', 25000, 'salad'),
            ('Sezar salati', 35000, 'salad'),
            ('Mastava', 20000, 'soup'),
            ("Sho'rva", 22000, 'soup'),
            ('Osh', 45000, 'main'),
            ('Manti (4 dona)', 40000, 'main'),
            ('Shashlik (1 kg)', 120000, 'main'),
            ("Lag'mon", 35000, 'main'),
            ('Coca-Cola 1L', 12000, 'drink'),
            ("Choy (ko'k)", 5000, 'drink'),
            ('Sharbat', 15000, 'drink'),
            ('Medovik', 18000, 'dessert'),
            ('Napaleon', 20000, 'dessert'),
            ('Chuchvara', 30000, 'soup'),
            ("Baranina sho'rva", 28000, 'soup'),
        ]

        for name, price, category_slug in items:
            category = Category.objects.get(slug=category_slug)
            MenuItem.objects.get_or_create(
                name=name,
                defaults={'price': price, 'category': category},
            )

    def create_settings(self):
        Settings.objects.get_or_create(
            key='tax_rate',
            defaults={'value': '12', 'description': 'QQS stavkasi (%)'},
        )

    def create_default_users(self, reset_passwords=False):
        users = [
            {
                'username': 'admin',
                'first_name': 'Admin',
                'password': 'admin123',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'waiter1',
                'first_name': 'Ali',
                'password': '1234',
                'role': 'waiter',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'waiter2',
                'first_name': 'Vali',
                'password': '1234',
                'role': 'waiter',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        for data in users:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'is_staff': data['is_staff'],
                    'is_superuser': data['is_superuser'],
                },
            )
            user.first_name = data['first_name']
            user.is_staff = data['is_staff']
            user.is_superuser = data['is_superuser']
            if created or reset_passwords:
                user.set_password(data['password'])
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = data['role']
            profile.save()
