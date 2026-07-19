from django.contrib import admin
from .models import Category, MenuItem, Order, OrderItem, SavedReceipt, Settings, Table, UserProfile


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'is_active']
    list_filter = ['is_active']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'waiter', 'status', 'subtotal', 'total', 'created_at']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']
    list_filter = ['role']



@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'description']
    list_editable = ['value']
    search_fields = ['key', 'description']


@admin.register(SavedReceipt)
class SavedReceiptAdmin(admin.ModelAdmin):
    list_display = ['id', 'table_number', 'created_at', 'expires_at']
    list_filter = ['created_at', 'expires_at']
    readonly_fields = ['receipt_data', 'created_at', 'expires_at']

    def table_number(self, obj):
        return obj.receipt_data.get('table_number', '-') if isinstance(obj.receipt_data, dict) else '-'

    table_number.short_description = 'Stol'
