from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, MenuItem, Order, OrderItem, SavedReceipt, Settings, Table, UserProfile


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

    def test_save_order_creates_receipt_without_clearing_history(self):
        order = self.create_order(status='active', quantity=2)
        self.client.force_login(self.waiter)

        response = self.client.get(reverse('save_order', args=[order.id]))

        self.assertRedirects(response, reverse('waiter_dashboard'))
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')
        self.assertTrue(Order.objects.filter(id=order.id, status='completed').exists())

        receipt = SavedReceipt.objects.get(order=order)
        self.assertEqual(receipt.receipt_data['order_id'], order.id)
        self.assertEqual(receipt.receipt_data['table_number'], self.table.number)
        self.assertEqual(receipt.receipt_data['total'], 22000)

        remaining = receipt.expires_at - timezone.now()
        self.assertGreater(remaining, timedelta(days=2, hours=23))
        self.assertLessEqual(remaining, timedelta(days=3, minutes=1))

        self.client.force_login(self.admin)
        reports_response = self.client.get(reverse('admin_reports'))
        self.assertEqual(reports_response.context['all_count'], 1)
        self.assertEqual(reports_response.context['all_total'], 22000)

        receipts_response = self.client.get(reverse('saved_receipts'))
        self.assertIn(receipt, list(receipts_response.context['receipts']))

    def test_saved_receipts_backfills_completed_order_without_clearing_history(self):
        order = self.create_order(status='completed', quantity=2)
        self.client.force_login(self.admin)

        response = self.client.get(reverse('saved_receipts'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Order.objects.filter(id=order.id, status='completed').exists())

        receipt = SavedReceipt.objects.get(order=order)
        self.assertIn(receipt, list(response.context['receipts']))
        self.assertEqual(receipt.receipt_data['total'], 22000)

    def test_clear_history_keeps_missing_saved_receipt_for_three_days(self):
        order = self.create_order(status='completed', quantity=2)
        self.client.force_login(self.admin)

        response = self.client.post(reverse('clear_history'))

        self.assertRedirects(response, reverse('admin_reports'))
        self.assertFalse(Order.objects.filter(id=order.id).exists())

        receipt = SavedReceipt.objects.get()
        self.assertIsNone(receipt.order_id)
        self.assertEqual(receipt.receipt_data['order_id'], order.id)
        self.assertEqual(receipt.receipt_data['table_number'], self.table.number)
        self.assertEqual(receipt.receipt_data['total'], 22000)

        remaining = receipt.expires_at - timezone.now()
        self.assertGreater(remaining, timedelta(days=2, hours=23))
        self.assertLessEqual(remaining, timedelta(days=3, minutes=1))

    def test_expired_saved_receipts_are_deleted_automatically(self):
        receipt = SavedReceipt.objects.create(
            receipt_data={'table_number': self.table.number},
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse('receipt_detail', args=[receipt.id]))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(SavedReceipt.objects.filter(id=receipt.id).exists())


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
