from django.db import models
from django.contrib.auth.models import User


class Table(models.Model):
    number = models.PositiveIntegerField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Stol #{self.number}"

    class Meta:
        ordering = ['number']
        verbose_name = 'Stol'
        verbose_name_plural = 'Stollar'


class Category(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'


class MenuItem(models.Model):
    WEIGHT_TYPE_CHOICES = [
        ('unit', 'Dona'),
        ('kg', 'Kg'),
    ]

    name = models.CharField(max_length=100, verbose_name='Nomi')
    price = models.PositiveIntegerField(verbose_name='Narxi')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Kategoriya')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    weight_type = models.CharField(max_length=10, choices=WEIGHT_TYPE_CHOICES, default='unit', verbose_name='O‘lchov turi')
    price_per_kg = models.PositiveIntegerField(null=True, blank=True, verbose_name='Narxi/kg')
    min_weight = models.DecimalField(max_digits=6, decimal_places=2, default=0.1, verbose_name='Minimal og‘irlik (kg)')
    stock_kg = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='Skladdagi kg')

    def __str__(self):
        return f"{self.name} - {self.price} so'm"

    @property
    def is_weight_based(self):
        return self.weight_type == 'kg'

    @property
    def unit_price(self):
        return self.price_per_kg if self.is_weight_based else self.price

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Menyu taomi'
        verbose_name_plural = 'Menyu taomlari'


class Order(models.Model):
    STATUS_CHOICES = [
        ('active', 'Faol'),
        ('completed', 'Yakunlangan'),
        ('cancelled', 'Bekor qilingan'),
    ]

    table = models.ForeignKey(Table, on_delete=models.CASCADE, verbose_name='Stol')
    waiter = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Ofitsiant')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Holati')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqti')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqti')

    def __str__(self):
        return f"Zakaz #{self.id} - Stol #{self.table.number}"

    @property
    def subtotal(self):
        return sum(item.total for item in self.items.all())

    @property
    def tax(self):
        try:
            setting = Settings.objects.get(key='tax_rate')
            rate = float(setting.value) / 100
        except (Settings.DoesNotExist, ValueError):
            rate = 0.12
        return round(self.subtotal * rate)

    @property
    def total(self):
        return self.subtotal + self.tax

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Zakaz'
        verbose_name_plural = 'Zakazlar'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Zakaz')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, verbose_name='Taom')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Miqdori')
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name='Og‘irlik (kg)')
    price_at_time = models.PositiveIntegerField(verbose_name='Narxi (zakaz vaqtida)')

    def __str__(self):
        if self.is_weight_item:
            return f"{self.menu_item.name} - {self.weight_kg} kg"
        return f"{self.menu_item.name} x{self.quantity}"

    @property
    def is_weight_item(self):
        return self.menu_item.weight_type == 'kg'

    @property
    def total(self):
        if self.is_weight_item:
            return round(self.price_at_time * float(self.weight_kg))
        return self.price_at_time * self.quantity

    class Meta:
        verbose_name = 'Zakaz elementi'
        verbose_name_plural = 'Zakaz elementlari'


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('waiter', 'Ofitsiant'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='waiter', verbose_name='Rol')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefon')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"

    class Meta:
        verbose_name = 'Foydalanuvchi profili'
        verbose_name_plural = 'Foydalanuvchi profillari'


class Settings(models.Model):
    """Tizim sozlamalari"""
    key = models.CharField(max_length=50, unique=True, verbose_name='Kalit')
    value = models.CharField(max_length=255, verbose_name='Qiymat')
    description = models.CharField(max_length=255, blank=True, verbose_name='Tavsif')

    def __str__(self):
        return f"{self.key}: {self.value}"

    class Meta:
        verbose_name = 'Sozlama'
        verbose_name_plural = 'Sozlamalar'
