# OLX.UZ Clone - Loyihani ishga tushirish

## 📋 Talablar
- Python 3.10+
- PostgreSQL 14+
- pip

---

## 🚀 0-dan ishga tushirish (ketma-ket buyruqlar)

### 1. PostgreSQL bazasini yaratish

```bash
sudo -u postgres psql
```

PostgreSQL'da:
```sql
CREATE DATABASE olx_db;
CREATE USER olx_user WITH PASSWORD 'olx_password';
GRANT ALL PRIVILEGES ON DATABASE olx_db TO olx_user;
\q
```

### 2. Loyihani klonlash yoki arxivdan chiqarish

```bash
cd ~
unzip olx_uz-main.zip
cd olx_uz-main
```

### 3. Virtual muhit yaratish va faollashtirish

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
# yoki: venv\Scripts\activate  # Windows
```

### 4. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 5. .env faylini sozlash

```bash
cp .env.example .env
nano .env   # yoki: gedit .env
```

`.env` faylni to'ldiring:
```
SECRET_KEY=django-insecure-your-random-secret-key-here
DEBUG=1
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=olx_db
DB_USER=olx_user
DB_PASSWORD=olx_password
DB_HOST=127.0.0.1
DB_PORT=5432

TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
BACKEND_BASE_URL=http://127.0.0.1:8000

JWT_ACCESS_MINUTES=60
JWT_REFRESH_DAYS=7
```

### 6. Migratsiyalarni qo'llash

```bash
python manage.py migrate
```

### 7. Superuser (admin) yaratish

```bash
python manage.py createsuperuser
```

Ma'lumotlar so'raladi:
- Username: `admin`
- Email: (bo'sh qoldirish mumkin)
- Password: `admin1234` (yoki xohlagan parolingiz)

**Admin paneli:** http://127.0.0.1:8000/admin/
**Login:** admin / admin1234

### 8. Statik fayllarni yig'ish (ixtiyoriy, production uchun)

```bash
python manage.py collectstatic
```

### 9. Django serverni ishga tushirish

```bash
python manage.py runserver
```

Server ishlaydi: http://127.0.0.1:8000

### 10. Telegram botni ishga tushirish (yangi terminal oynada)

```bash
cd ~/olx_uz-main
source venv/bin/activate
python bot/main.py
```

---

## 🌐 API hujjatlari

- **Swagger UI:** http://127.0.0.1:8000/api/docs/
- **OpenAPI Schema:** http://127.0.0.1:8000/api/schema/

---

## 🤖 Bot buyruqlari

| Buyruq | Tavsif |
|--------|--------|
| `/start` | Login / ro'yxatdan o'tish |
| `/me` | Profilni ko'rish |
| `/menu` | Asosiy menyu |
| `/upgrade_seller` | Seller bo'lish |
| `/my_products` | Mening mahsulotlarim |
| `/add_product` | Mahsulot qo'shish |
| `/my_orders` | Buyurtmalarim |
| `/favorites` | Saralangan mahsulotlar |
| `/categories` | Kategoriyalar |
| `/logout` | Chiqish |
| `/cancel` | Dialogni bekor qilish |

---

## 🗂 API Endpoints

### Auth
- `POST /api/v1/auth/telegram-login/` - Telegram orqali login
- `POST /api/v1/auth/refresh/` - Token yangilash
- `POST /api/v1/auth/logout/` - Chiqish

### Users
- `GET/PUT/PATCH /api/v1/users/me/` - Profil
- `POST /api/v1/users/me/upgrade-to-seller/` - Seller bo'lish

### Marketplace
- `GET /api/v1/categories/` - Kategoriyalar
- `GET/POST /api/v1/products/` - Mahsulotlar
- `GET /api/v1/products/{id}/` - Mahsulot detail
- `POST /api/v1/products/{id}/publish/` - Mahsulotni tasdiqlash (admin)
- `POST /api/v1/products/{id}/images/` - Rasm qo'shish
- `GET/POST /api/v1/favorites/` - Saralangan
- `GET/POST /api/v1/orders/` - Buyurtmalar
- `PATCH /api/v1/orders/{id}/` - Buyurtma statusini yangilash
- `GET/POST /api/v1/reviews/` - Izohlar
- `GET /api/v1/sellers/` - Sotuvchilar

---

## ⚠️ Muhim eslatmalar

1. Mahsulot qo'shilgandan keyin admin panelida tasdiqlash kerak
   - http://127.0.0.1:8000/admin/ → Products → Tanlangan mahsulotni tanlash → "Tanlangan mahsulotlarni tasdiqlash"

2. Telegram botni ishlatish uchun avval Django server ishlab turishi kerak

3. Production'da `DEBUG=0` qiling va `SECRET_KEY`ni o'zgartiring
