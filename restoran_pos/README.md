# Restoran POS Tizimi

Django da yozilgan restoran boshqaruv tizimi.

## Xususiyatlar

- **Ofitsiant paneli**: Stollarni ko'rish, zakaz qilish, chek chop etish
- **Admin paneli**: Menyu boshqaruvi, stollar sozlamalari, xodimlar boshqaruvi, hisobotlar
- **QQS hisoblash**: Avtomatik 12% QQS
- **Ko'p stollarni qo'llab-quvvatlash**

## O'rnatish

1. Virtual muhit yaratish:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

2. Kutubxonalarni o'rnatish:
```bash
pip install -r requirements.txt
```

3. Ma'lumotlar bazasini yaratish:
```bash
python manage.py migrate
```

4. Superuser yaratish:
```bash
python manage.py createsuperuser
```

5. Ma'lumotlarni yuklash (stollar va kategoriyalar):
```bash
python manage.py shell
```

```python
from pos.models import Table, Category

# Stollar yaratish
for i in range(1, 21):
    Table.objects.get_or_create(number=i)

# Kategoriyalar yaratish
categories = [
    ('salad', 'Salatlar'),
    ('soup', "Sho'rvalar"),
    ('main', 'Asosiy'),
    ('drink', 'Ichimliklar'),
    ('dessert', 'Desertlar'),
]

for slug, name in categories:
    Category.objects.get_or_create(slug=slug, defaults={'name': name})
```

6. Serverni ishga tushirish:
```bash
python manage.py runserver
```

## Standart loginlar

- **Admin**: superuser orqali yaratilgan login
- **Ofitsiant**: admin paneldan qo'shiladi

## URL manzillar

- `/login/` - Kirish sahifasi
- `/` - Ofitsiant boshqaruv paneli
- `/admin-panel/` - Admin boshqaruv paneli
- `/admin/` - Django admin paneli


## ⚙️ QQS Stavkasini O'zgartirish

### Usul 1: Django Admin Paneli (Tavsiya etiladi)
1. Brauzerda `http://127.0.0.1:8000/admin/` ga kiring
2. `Sozlamalar` (Settings) bo'limiga kiring
3. `tax_rate` yozuvini toping
4. Qiymatini o'zgartiring (faqat son, masalan: 15, 10, 0)
5. Saqlash tugmasini bosing

### Usul 2: Admin Hisobot Sahifasi
Admin panelidagi `📊 Hisobot` sahifasida joriy QQS stavkasi ko'rsatiladi.

**Eslatma:** Yangi stavka faqat yangi zakazlarga qo'llaniladi. Avvalgi zakazlar o'zgarishsiz qoladi.
