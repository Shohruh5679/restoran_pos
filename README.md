# Restoran POS

Django asosida yozilgan restoran uchun POS boshqaruv tizimi.

## Imkoniyatlar

- Ofitsiant paneli: stollarni ko'rish, zakaz yaratish, chek chiqarish
- Admin panel: zakazlar, menyu, stollar, xodimlar va hisobotlarni boshqarish
- QQS hisoblash: standart 12%, admin orqali o'zgartirish mumkin
- Railway deploy uchun tayyor konfiguratsiya

## Demo Loginlar

Admin:

```text
login: choy
parol: 123
```

Ofitsiant:

```text
login: waiter1
parol: 1234

login: waiter2
parol: 1234
```

## URL Manzillar

```text
/login/        - Kirish sahifasi
/              - Ofitsiant paneli
/admin-panel/  - Admin panel
/admin/        - Django admin panel
```

## Local Ishga Tushirish

1. Virtual muhit yarating:

```bash
python -m venv .venv
```

2. Virtual muhitni yoqing:

Windows:

```bash
.venv\Scripts\activate
```

Linux/Mac:

```bash
source .venv/bin/activate
```

3. Kutubxonalarni o'rnating:

```bash
pip install -r requirements.txt
```

4. Migratsiyalarni bajaring:

```bash
python restoran_pos/manage.py migrate
```

5. Default ma'lumotlarni yarating:

```bash
python restoran_pos/manage.py seed_default_data --reset-passwords
```

6. Serverni ishga tushiring:

```bash
python restoran_pos/manage.py runserver
```

## Railway Deploy

Loyihada Railway uchun kerakli fayllar bor:

- `railway.json`
- `Procfile`
- `runtime.txt`
- `requirements.txt`

Deploy vaqtida avtomatik bajariladi:

```bash
python restoran_pos/manage.py migrate --noinput
python restoran_pos/manage.py seed_default_data --reset-passwords
gunicorn --chdir restoran_pos restoran.wsgi --log-file -
```

## Test

```bash
python restoran_pos/manage.py test pos
```
