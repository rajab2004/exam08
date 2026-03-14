# Yakuniy Imtihon: "OLX.UZ - Marketplace Platformasi" Backend

**Loyiha maqsadi:** Foydalanuvchilar (xaridorlar va sotuvchilar) o'rtasida mahsulot oldi-sotdisini tashkil qiluvchi backend tizimini yaratish. Ushbu loyiha orqali siz Django va DRF yordamida real loyihaga o'xshash platformaning asosiy qismlarini yaratishni o'rganasiz.

**Texnologiyalar:** Django 4.x, Django REST Framework, PostgreSQL, Simple‑JWT (autentifikatsiya), python-telegram-bot,  drf‑spectacular (Swagger), Git.

**Topshiriq muddati:** 2 hafta.

---

## 1. Loyiha haqida

Bu platforma – OLX.UZ ga o‘xshash, lekin soddaroq versiya. Quyidagi imkoniyatlar bo‘lishi kerak:

- **Foydalanuvchilar** Telegram orqali ro‘yxatdan o‘tadi va tizimga kiradi.
- **Sotuvchilar** o‘z do‘kon profilini yaratadi va mahsulot (e’lon) qo‘sha oladi.
- **Kategoriyalar** ierarxik tuzilishda bo‘lib, mahsulotlar ma’lum kategoriyaga tegishli.
- Har bir mahsulot bir nechta rasmga ega bo‘lishi mumkin.
- **Xaridorlar** mahsulotlarni ko‘rish, qidirish, filterlash, sevimlilarga qo‘shish imkoniga ega.
- Xaridor mahsulotni sotib olish niyatini bildirishi (**order**) va kelishilgandan so‘ng buyurtmani yakunlab, sotuvchiga **reyting** qoldirishi mumkin.

Loyiha ikkita asosiy rolni qo‘llab-quvvatlaydi:
- **Customer** (oddiy foydalanuvchi) – mahsulotlarni ko‘rish, sevimlilar, buyurtma berish, sharh qoldirish.
- **Seller** (sotuvchi) – barcha customer imkoniyatlari + mahsulot qo‘shish/tahrirlash/o‘chirish, o‘z buyurtmalarini boshqarish.

Admin/moderator roli talab qilinmaydi.

---

## 2. Ma’lumotlar bazasi modellari

Quyidagi modellarni Django’da yarating. Barcha kerakli maydonlar va munosabatlar ko‘rsatilgan.

### 2.1. User (foydalanuvchi)
`AbstractUser` dan meros olish yoki alohida model yaratish mumkin.

| Field            | Tipi                    | Izoh                                  |
|------------------|-------------------------|---------------------------------------|
| id               | PK                      |                                       |
| telegram_id      | BigIntegerField, unique | Telegram ID orqali login              |
| username         | CharField, unique       | Telegram username                     |
| first_name       | CharField               |                                       |
| last_name        | CharField, blank        |                                       |
| phone_number     | CharField, blank        | Ixtiyoriy                             |
| role             | CharField (choices)     | `customer` (default) yoki `seller`    |
| avatar           | ImageField, blank       | Profil rasmi                          |
| is_active        | BooleanField            | Default=True                          |
| date_joined      | DateTimeField           |                                       |
| last_login       | DateTimeField           |                                       |

**Role tanlovlari:** `(('customer', 'Xaridor'), ('seller', 'Sotuvchi'))`.

### 2.2. SellerProfile (sotuvchi profili)
`User` modeli bilan `OneToOne` bog‘lanish.

| Field            | Tipi                    | Izoh                                  |
|------------------|-------------------------|---------------------------------------|
| id               | PK                      |                                       |
| user             | OneToOne(User)          |                                       |
| shop_name        | CharField, unique       | Do‘kon nomi                           |
| shop_description | TextField, blank        |                                       |
| shop_logo        | ImageField, blank       |                                       |
| region           | CharField               | Viloyat                               |
| district         | CharField               | Tuman                                 |
| address          | CharField, blank        |                                       |
| rating           | FloatField, default=0   | O‘rtacha reyting (avtomatik hisoblanadi) |
| total_sales      | PositiveIntegerField, default=0 | Sotuvlar soni                  |
| created_at       | DateTimeField           |                                       |
| updated_at       | DateTimeField           |                                       |

### 2.3. Category (kategoriya)
Ierarxik (parent–child) tuzilish.

| Field            | Tipi                    | Izoh                                  |
|------------------|-------------------------|---------------------------------------|
| id               | PK                      |                                       |
| name             | CharField               | Masalan: "Elektronika"                |
| slug             | SlugField, unique       | URL uchun (avtomatik yaratiladi)      |
| parent           | ForeignKey(self)        | null=True, blank=True                  |
| icon             | ImageField, blank       |                                       |
| description      | TextField, blank        |                                       |
| is_active        | BooleanField, default=True |                                     |
| order_num        | PositiveIntegerField, default=0 | Tartiblash uchun               |
| created_at       | DateTimeField           |                                       |

### 2.4. Product (mahsulot/e’lon)

| Field            | Tipi                    | Izoh                                  |
|------------------|-------------------------|---------------------------------------|
| id               | PK                      |                                       |
| seller           | ForeignKey(User)        | `seller` roli uchun                   |
| category         | ForeignKey(Category)    |                                       |
| title            | CharField(200)          |                                       |
| description      | TextField               |                                       |
| condition        | CharField(choices)      | `yangi`, `ideal`, `yaxshi`, `qoniqarli` |
| price            | DecimalField            |                                       |
| price_type       | CharField(choices)      | `qat'iy`, `kelishiladi`, `bepul`, `ayirboshlash` |
| region           | CharField               |                                       |
| district         | CharField               |                                       |
| view_count       | PositiveIntegerField, default=0 | Ko‘rilganlar soni               |
| favorite_count   | PositiveIntegerField, default=0 | Sevimlilar soni (denormalizatsiya) |
| status           | CharField(choices)      | `moderatsiyada`, `aktiv`, `rad etilgan`, `sotilgan`, `arxivlangan`. Default `moderatsiyada` |
| created_at       | DateTimeField           |                                       |
| updated_at       | DateTimeField           |                                       |
| published_at     | DateTimeField, null     | Aktiv vaqti                           |
| expires_at       | DateTimeField           | 30 kundan keyin                       |

**Status tanlovlari:** `moderatsiyada`, `aktiv`, `rad etilgan`, `sotilgan`, `arxivlangan`.

**Condition tanlovlari:** `yangi`, `ideal`, `yaxshi`, `qoniqarli`.

**Price_type tanlovlari:** `qat'iy`, `kelishiladi`, `bepul`, `ayirboshlash`.

### 2.5. ProductImage (mahsulot rasmlari)

| Field            | Tipi                    | Izoh                                  |
|------------------|-------------------------|---------------------------------------|
| id               | PK                      |                                       |
| product          | ForeignKey(Product)     | related_name='images'                 |
| image            | ImageField              |                                       |
| order            | PositiveIntegerField    | Rasm tartibi                          |
| is_main          | BooleanField, default=False | Bosh rasm (True bo‘lsa boshqalar False) |
| created_at       | DateTimeField           |                                       |

### 2.6. Favorite (sevimlilar)

| Field            | Tipi                    | Izoh                                  |
|------------------|-------------------------|---------------------------------------|
| id               | PK                      |                                       |
| user             | ForeignKey(User)        |                                       |
| product          | ForeignKey(Product)     |                                       |
| created_at       | DateTimeField           |                                       |

**Unique together:** `('user', 'product')`.

### 2.7. Order (buyurtma)

| Field            | Tipi                    | Izoh                                  |
|------------------|-------------------------|---------------------------------------|
| id               | PK                      |                                       |
| product          | ForeignKey(Product)     |                                       |
| buyer            | ForeignKey(User)        | Buyurtma beruvchi                     |
| seller           | ForeignKey(User)        | Mahsulot egasi (denormalizatsiya)     |
| final_price      | DecimalField            | Kelishilgan narx (default product.price) |
| status           | CharField(choices)      | `kutilyapti`, `kelishilgan`, `sotib olingan`, `bekor qilingan` |
| meeting_location | CharField, blank        | Uchrashuv joyi                        |
| meeting_time     | DateTimeField, null     | Uchrashuv vaqti                       |
| notes            | TextField, blank        | Qo‘shimcha izoh                       |
| created_at       | DateTimeField           |                                       |
| updated_at       | DateTimeField           |                                       |

**Status tanlovlari:** `kutilyapti`, `kelishilgan`, `sotib olingan`, `bekor qilingan`.

### 2.8. Review (fikr va reyting)

| Field            | Tipi                    | Izoh                                  |
|------------------|-------------------------|---------------------------------------|
| id               | PK                      |                                       |
| order            | OneToOneField(Order)    | Har bir buyurtma uchun bitta fikr     |
| reviewer         | ForeignKey(User)        | Fikr qoldiruvchi (buyer)               |
| seller           | ForeignKey(User)        | Sotuvchi (denormalizatsiya)           |
| rating           | PositiveSmallIntegerField | 1–5 gacha                            |
| comment          | TextField               |                                       |
| created_at       | DateTimeField           |                                       |

---

## 3. Biznes mantiq (Business Logic)

Loyihada quyidagi qoidalar va amallar bajarilishi kerak:

### 3.1. Foydalanuvchi va autentifikatsiya
- Foydalanuvchi tizimga **Telegram** orqali kiradi. Frontend (yoki Telegram bot) `telegram_id`, `username`, `first_name`, `last_name` va ixtiyoriy `photo_url` ni backendga yuboradi.
- Backend:
  - Agar `telegram_id` bo‘yicha foydalanuvchi topilsa, unga JWT token yaratib beradi.
  - Agar topilmasa, yangi foydalanuvchi yaratadi (role = `customer`) va token qaytaradi.
- Token orqali barcha so‘rovlar autentifikatsiya qilinadi.

### 3.2. Rolga asoslangan ruxsatlar
- **Customer**:
  - Barcha mahsulotlarni ko‘rish, qidirish, filterlash.
  - Mahsulotni sevimlilarga qo‘shish/olib tashlash.
  - O‘z sevimlilarini ko‘rish.
  - Mahsulotga buyurtma berish (`order` yaratish).
  - O‘z buyurtmalarini ko‘rish.
  - Faqat o‘zi yaratgan buyurtma uchun (status `sotib olingan` bo‘lsa) fikr qoldirish.
- **Seller**:
  - Customer ning barcha imkoniyatlari.
  - O‘z do‘kon profilini yaratish va tahrirlash (faqat bir marta yaratish mumkin).
  - Mahsulot qo‘shish, tahrirlash, o‘chirish (faqat o‘z mahsulotlari).
  - O‘z mahsulotlariga kelgan buyurtmalarni ko‘rish va statusini o‘zgartirish (`kelishilgan`, `sotib olingan`, `bekor qilingan`).
  - Sotuvlar soni va reytingi avtomatik yangilanadi.

### 3.3. Mahsulot (e’lon) bilan ishlash
- **Yangi e’lon**: Seller tomonidan yaratiladi. Status `moderatsiyada` bo‘ladi (moderatsiya real emas, shunchaki placeholder). Keyinroq `aktiv`ga o‘tkazish uchun alohida endpoint (masalan, `publish/`).
- **E’lonni tahrirlash**: Faqat o‘z e’loni. Agar e’lon `aktiv` bo‘lsa, tahrirlangandan keyin yana `moderatsiyada` bo‘lishi kerak.
- **E’lonni o‘chirish**: Faqat o‘z e’loni. O‘chirilganda bog‘liq rasmlar ham o‘chadi.
- **E’lonni arxivlash**: `status` ni `arxivlangan` qilish.
- **E’lonni sotilgan deb belgilash**: `status` → `sotilgan`. Sotuvchining `total_sales` +1.
- **Ko‘rishlar soni**: Har safar mahsulot detallari ko‘rilganda `view_count` +1 (bir kunda bir foydalanuvchidan faqat bir marta hisoblash ixtiyoriy).

### 3.4. Kategoriyalar
- Kategoriyalarni yaratish/tahrirlash/o‘chirish faqat admin uchun (yoki Django admin panel orqali). Talabalar oddiy CRUD qilsa bo‘ladi, lekin role tekshiruvi talab qilinmaydi.
- Kategoriya ierarxiyasi: parent–child. Mahsulot istalgan kategoriyaga qo‘shilishi mumkin.

### 3.5. Sevimlilar (Favorite)
- Foydalanuvchi faqat o‘z sevimlilarini qo‘shishi/olib tashlashi/ko‘rishi mumkin.
- `favorite_count` mahsulotda denormalizatsiya qilinadi: sevimlilarga qo‘shilganda +1, olib tashlanganda -1.

### 3.6. Buyurtma (Order)
- **Buyurtma yaratish**: Xaridor mahsulotni tanlab, `order` yaratadi. Status `kutilyapti`. `final_price` = product.price (keyin kelishib o‘zgartirish mumkin).
- **Buyurtmani ko‘rish**: Sotuvchi va xaridor o‘z buyurtmalarini ko‘ra oladi.
- **Statusni o‘zgartirish**:
  - Sotuvchi `kutilyapti` → `kelishilgan` (narx va uchrashuv vaqtini kiritishi mumkin) yoki `bekor qilingan`.
  - Xaridor `kelishilgan` → `sotib olingan` (yoki `bekor qilingan`).
  - `sotib olingan` bo‘lganda:
    - Mahsulot statusi `sotilgan` ga o‘zgaradi.
    - Sotuvchining `total_sales` +1.
    - Xaridor endi ushbu buyurtma uchun `review` qoldirishi mumkin.

### 3.7. Fikr va reyting (Review)
- Faqat `sotib olingan` statusli buyurtma uchun fikr qoldirish mumkin.
- Bir buyurtma uchun faqat bitta fikr (OneToOne).
- Fikr qoldirilganda sotuvchining `rating` maydoni barcha fikrlar o‘rtachasiga yangilanadi.
- Fikrni faqat xaridor qoldiradi va tahrirlay olmaydi (agar bonus kerak bo‘lsa, tahrirlashga ruxsat berish mumkin).

### 3.8. Qidiruv va filterlash
- `products/` endpointida quyidagi filterlar bo‘lishi kerak:
  - `category` (slug yoki id)
  - `region`
  - `min_price`, `max_price`
  - `search` (title va description bo‘yicha matnli qidiruv, `icontains`)
  - `ordering` (`created_at`, `price`, `-view_count` va h.k.)
- Faqat `status='aktiv'` bo‘lgan mahsulotlar chiqishi kerak (moderatsiyadagilar chiqmasin).

---

## 4. API Endpointlar

Quyidagi endpointlarni REST prinsiplari asosida yarating. Barcha endpointlar (registratsiyadan tashqari) JWT token orqali himoyalangan.

### 4.1. Autentifikatsiya

| Method | URL | Tavsif | Kirish ma’lumotlari | Javob |
|--------|-----|--------|----------------------|-------|
| POST | `/api/v1/auth/telegram-login/` | Telegram orqali login/registratsiya bittada | `{telegram_id, username, first_name, last_name, photo_url?}` | `{access, refresh, user}` |
| POST | `/api/v1/auth/refresh/` | Tokenni yangilash | `{refresh}` | `{access}` |
| POST | `/api/v1/auth/logout/` | Chiqish (tokenni blacklist) | - | `{message}` |

### 4.2. Foydalanuvchi profili

| Method | URL | Tavsif | Ruxsat |
|--------|-----|--------|--------|
| GET | `/api/v1/users/me/` | O‘z profilini ko‘rish | Authenticated |
| PATCH | `/api/v1/users/me/` | Profilni tahrirlash (telefon, ism) | Authenticated |
| POST | `/api/v1/users/me/upgrade-to-seller/` | Sotuvchi bo‘lish (SellerProfile yaratish) | Customer (keyin role seller) |
| GET | `/api/v1/sellers/{seller_id}/` | Sotuvchi haqida ma’lumot (public) | Public |
| GET | `/api/v1/sellers/{seller_id}/products/` | Sotuvchining barcha aktiv mahsulotlari | Public |

### 4.3. Kategoriyalar

| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/api/v1/categories/` | Barcha kategoriyalar (parent–child) |
| GET | `/api/v1/categories/{slug}/` | Bitta kategoriya |
| GET | `/api/v1/categories/{slug}/products/` | Shu kategoriyadagi aktiv mahsulotlar |

### 4.4. Mahsulotlar (Products)

| Method | URL | Tavsif | Ruxsat |
|--------|-----|--------|--------|
| GET | `/api/v1/products/` | Barcha aktiv mahsulotlar (filter, search, pagination) | Public |
| GET | `/api/v1/products/{id}/` | Bitta mahsulot (view_count +1) | Public |
| POST | `/api/v1/products/` | Yangi e’lon qo‘shish | Seller |
| PUT/PATCH | `/api/v1/products/{id}/` | E’lonni tahrirlash | Faqat o‘z e’loni (seller) |
| DELETE | `/api/v1/products/{id}/` | E’lonni o‘chirish | Faqat o‘z e’loni (seller) |
| POST | `/api/v1/products/{id}/publish/` | E’lonni chop etish (moderatsiyadan aktivga) | Faqat o‘z e’loni (seller) |
| POST | `/api/v1/products/{id}/archive/` | Arxivlash | Faqat o‘z e’loni (seller) |
| POST | `/api/v1/products/{id}/sold/` | Sotilgan deb belgilash | Faqat o‘z e’loni (seller) |

### 4.5. Sevimlilar (Favorites)

| Method | URL | Tavsif | Ruxsat |
|--------|-----|--------|--------|
| GET | `/api/v1/favorites/` | O‘z sevimlilari ro‘yxati | Authenticated |
| POST | `/api/v1/favorites/` | Sevimlilarga qo‘shish | `{product_id}` | Authenticated |
| DELETE | `/api/v1/favorites/{id}/` | Sevimlilardan olib tashlash | Authenticated |

### 4.6. Buyurtmalar (Orders)

| Method | URL | Tavsif | Ruxsat |
|--------|-----|--------|--------|
| GET | `/api/v1/orders/` | O‘z buyurtmalari (filter: ?role=buyer|seller) | Authenticated |
| POST | `/api/v1/orders/` | Yangi buyurtma yaratish | `{product_id, notes?}` | Customer |
| GET | `/api/v1/orders/{id}/` | Bitta buyurtma | Faqat buyer yoki seller |
| PATCH | `/api/v1/orders/{id}/` | Statusni yangilash | `{status, meeting_location?, meeting_time?}` | Buyer yoki seller (statusga qarab) |

### 4.7. Fikrlar (Reviews)

| Method | URL | Tavsif | Ruxsat |
|--------|-----|--------|--------|
| GET | `/api/v1/reviews/` | Barcha fikrlar (filter: ?seller_id) | Public |
| POST | `/api/v1/reviews/` | Fikr qoldirish | `{order_id, rating, comment}` | Buyer (order ‘sotib olingan’ bo‘lishi kerak) |

---

## 5. Qo‘shimcha talabalar (texnik)

- **Clean code**: PEP8, ma’noli o‘zgaruvchi nomlari, funksiya/docstring izohlari.
- **Error handling**: HTTP status kodlari to‘g‘ri qaytarilsin (400, 401, 403, 404, 500).
- **Environment variables**: `.env` fayl orqali sozlamalar (DB, secret key va h.k.).
- **Git**: Feature branch lar, aniq commit xabarlari.
- **Dokumentatsiya**: Swagger (drf-spectacular) orqali avtomatik API hujjatlari.
- **PostgreSQL** ishlatilsin.

---

## 7. Topshiriqni topshirish

1. GitHub’da repository yarating va barcha kodni yuklang.
2. `README.md` faylida:
   - Loyiha nomi va qisqacha tavsifi
   - O‘rnatish va ishga tushirish bosqichlari
   - .env fayl namuna (`.env.example`)
   - API hujjatlariga havola (Swagger)
3. serverga deploy qilingan ip address yoki domain.
4. Postman collection (ixtiyoriy, lekin tavsiya etiladi).

**Muddat:** 2 hafta.

---

**Omad!** Agar savollar bo‘lsa, o‘qituvchingizga murojaat qiling.
