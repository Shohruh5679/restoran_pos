from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Category, MenuItem, Order, OrderItem, Settings, Table, UserProfile


class PosViewTests(TestCase):
    def setUp(self):
        self.table = Table.objects.create(number=1)
        self.category = Category.objects.create(name='Asosiy', slug='main')
        self.menu_item = MenuItem.objects.create(
            name='Osh',
            price=10000,
            category=self.category,
        )
        Settings.objects.create(key='tax_rate', value='10')

        self.waiter = User.objects.create_user(
            username='waiter',
            password='testpass123',
            first_name='Ali',
        )
        UserProfile.objects.create(user=self.waiter, role='waiter')

        self.admin = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True,
            is_superuser=True,
        )
        UserProfile.objects.create(user=self.admin, role='admin')

    def create_order(self, status='active', quantity=1):
        order = Order.objects.create(
            table=self.table,
            waiter=self.waiter,
            status=status,
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.menu_item,
            quantity=quantity,
            price_at_time=self.menu_item.price,
        )
        return order

    def test_change_qty_deletes_empty_order(self):
        order = self.create_order()
        order_item = order.items.get()
        self.client.force_login(self.waiter)

        response = self.client.post(
            reverse('change_qty', args=[order_item.id]),
            {'delta': -1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {'success': True, 'order_total': 0, 'deleted': True},
        )
        self.assertFalse(Order.objects.filter(id=order.id).exists())

    def test_admin_can_cancel_active_order(self):
        order = self.create_order()
        self.client.force_login(self.admin)

        response = self.client.post(reverse('clear_order', args=[order.id]))

        self.assertRedirects(response, reverse('admin_orders'))
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')

    def test_user_edit_without_password_keeps_existing_password(self):
        target = User.objects.create_user(
            username='worker',
            password='oldpass123',
            first_name='Old Name',
        )
        UserProfile.objects.create(user=target, role='waiter')
        old_password_hash = target.password
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('user_edit', args=[target.id]),
            {
                'username': 'worker',
                'first_name': 'New Name',
                'password': '',
                'role': 'admin',
            },
        )

        self.assertRedirects(response, reverse('admin_users'))
        target.refresh_from_db()
        self.assertEqual(target.password, old_password_hash)
        self.assertTrue(target.check_password('oldpass123'))
        self.assertEqual(target.userprofile.role, 'admin')

    def test_admin_reports_include_quantity_and_tax(self):
        self.create_order(status='completed', quantity=3)
        self.client.force_login(self.admin)

        response = self.client.get(reverse('admin_reports'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['today_total'], 33000)
        self.assertEqual(response.context['all_total'], 33000)


class SeedDefaultDataTests(TestCase):
    def test_seed_default_data_creates_documented_logins(self):
        call_command('seed_default_data', reset_passwords=True)

        admin = User.objects.get(username='choy')
        waiter1 = User.objects.get(username='waiter1')
        waiter2 = User.objects.get(username='waiter2')

        self.assertTrue(admin.check_password('123'))
        self.assertTrue(waiter1.check_password('1234'))
        self.assertTrue(waiter2.check_password('1234'))
        self.assertEqual(admin.userprofile.role, 'admin')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(waiter1.userprofile.role, 'waiter')
        self.assertEqual(Table.objects.count(), 20)
        self.assertTrue(Settings.objects.filter(key='tax_rate').exists())
