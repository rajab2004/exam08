"""
OLX.UZ Telegram Bot - To'liq versiya v2
========================================
Buyruqlar:
  /start            - Login / ro'yxatdan o'tish
  /help             - Yordam
  /me               - Profil ko'rish
  /menu             - Asosiy menyu
  /upgrade_seller   - Seller bo'lish (dialog)
  /my_products      - Mening mahsulotlarim (seller)
  /add_product      - Mahsulot qo'shish (seller)
  /upload_image     - Mahsulotga rasm yuklash (seller)
  /search           - Mahsulot qidirish
  /my_orders        - Mening buyurtmalarim
  /favorites        - Saralangan mahsulotlar
  /categories       - Kategoriyalar ro'yxati
  /stats            - Seller statistikasi
  /contact_seller   - Sotuvchiga xabar yuborish
  /logout           - Chiqish
  /cancel           - Dialogni bekor qilish
"""

import os
import logging
import requests
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)

# =========================
# ENV + LOGGING
# =========================
load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN        = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT  = 15

# API endpoints
LOGIN_URL      = f"{BACKEND_BASE_URL}/api/v1/auth/telegram-login/"
REFRESH_URL    = f"{BACKEND_BASE_URL}/api/v1/auth/refresh/"
LOGOUT_URL     = f"{BACKEND_BASE_URL}/api/v1/auth/logout/"
ME_URL         = f"{BACKEND_BASE_URL}/api/v1/users/me/"
UPGRADE_URL    = f"{BACKEND_BASE_URL}/api/v1/users/me/upgrade-to-seller/"
PRODUCTS_URL   = f"{BACKEND_BASE_URL}/api/v1/products/"
CATEGORIES_URL = f"{BACKEND_BASE_URL}/api/v1/categories/"
FAVORITES_URL  = f"{BACKEND_BASE_URL}/api/v1/favorites/"
ORDERS_URL     = f"{BACKEND_BASE_URL}/api/v1/orders/"
SELLERS_URL    = f"{BACKEND_BASE_URL}/api/v1/sellers/"
REVIEWS_URL    = f"{BACKEND_BASE_URL}/api/v1/reviews/"

# =========================
# Conversation states
# =========================
# Upgrade seller
SHOP_NAME, REGION, DISTRICT, ADDRESS = range(4)

# Add product
(
    PROD_TITLE, PROD_DESCRIPTION, PROD_CATEGORY_ID,
    PROD_CONDITION, PROD_PRICE, PROD_PRICE_TYPE,
    PROD_REGION, PROD_DISTRICT,
) = range(10, 18)

# Upload image
UPLOAD_PROD_ID, UPLOAD_IMAGE = range(20, 22)

# Search
SEARCH_QUERY = 30

# Contact seller
CONTACT_SELLER_ID, CONTACT_MESSAGE = range(40, 42)


# =========================
# HELPERS
# =========================
def build_login_payload(update: Update) -> dict:
    tg = update.effective_user
    return {
        "telegram_id": tg.id,
        "username":    tg.username or "",
        "first_name":  tg.first_name or "",
        "last_name":   tg.last_name or "",
    }


def save_tokens(context, access: str, refresh: str):
    context.user_data["access"]  = access
    context.user_data["refresh"] = refresh


def clear_tokens(context):
    context.user_data.pop("access",  None)
    context.user_data.pop("refresh", None)


def auth_headers(context) -> dict:
    access = context.user_data.get("access")
    return {"Authorization": f"Bearer {access}"} if access else {}


def is_logged_in(context) -> bool:
    return bool(context.user_data.get("access"))


def api_get(url, context, params=None):
    """(data|None, status_code, error_text)"""
    try:
        r = requests.get(url, headers=auth_headers(context),
                         params=params, timeout=REQUEST_TIMEOUT)
        return (r.json(), r.status_code, None) if r.status_code == 200 else (None, r.status_code, r.text)
    except requests.exceptions.RequestException as e:
        return None, 0, str(e)


def api_post(url, context, payload):
    """(data|None, status_code, error_text)"""
    try:
        r = requests.post(url, json=payload, headers=auth_headers(context), timeout=REQUEST_TIMEOUT)
        return (r.json(), r.status_code, None) if r.status_code in (200, 201) else (None, r.status_code, r.text)
    except requests.exceptions.RequestException as e:
        return None, 0, str(e)


def api_post_files(url, context, files, data=None):
    """Multipart file upload"""
    try:
        r = requests.post(url, headers=auth_headers(context),
                          files=files, data=data or {}, timeout=30)
        return (r.json(), r.status_code, None) if r.status_code in (200, 201) else (None, r.status_code, r.text)
    except requests.exceptions.RequestException as e:
        return None, 0, str(e)


def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("👤 Profil"),       KeyboardButton("🔍 Qidirish")],
        [KeyboardButton("❤️ Saralangan"),   KeyboardButton("📦 Buyurtmalar")],
        [KeyboardButton("🏪 Kategoriyalar"), KeyboardButton("⚙️ Sozlamalar")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def seller_menu_keyboard():
    keyboard = [
        [KeyboardButton("👤 Profil"),         KeyboardButton("🔍 Qidirish")],
        [KeyboardButton("🛍 Mahsulotlarim"),  KeyboardButton("📸 Rasm yuklash")],
        [KeyboardButton("📦 Buyurtmalar"),    KeyboardButton("📊 Statistika")],
        [KeyboardButton("🏪 Kategoriyalar"),  KeyboardButton("⚙️ Sozlamalar")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_smart_keyboard(context):
    """Foydalanuvchi roliga qarab to'g'ri klaviatura"""
    role = context.user_data.get("role", "customer")
    return seller_menu_keyboard() if role == "seller" else main_menu_keyboard()


def format_price(price) -> str:
    try:
        return f"{float(price):,.0f} so'm"
    except Exception:
        return str(price)


STATUS_EMOJI = {
    "moderatsiyada": "🔄",
    "aktiv":         "✅",
    "rad etilgan":   "❌",
    "sotilgan":      "💚",
    "arxivlangan":   "📁",
}

ORDER_EMOJI = {
    "kutilyapti":      "⏳",
    "kelishilgan":     "🤝",
    "sotib olingan":   "✅",
    "bekor qilingan":  "❌",
}


# =========================
# /start  /help  /menu
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payload = build_login_payload(update)
    try:
        r = requests.post(LOGIN_URL, json=payload, timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            await update.message.reply_text(
                f"❌ Backend xatolik berdi!\nStatus: {r.status_code}\n{r.text[:200]}")
            return

        data    = r.json()
        access  = data.get("access")
        refresh = data.get("refresh")
        user    = data.get("user", {})

        if not access or not refresh:
            await update.message.reply_text("❌ Backend token qaytarmadi.")
            return

        save_tokens(context, access, refresh)
        context.user_data["role"] = user.get("role", "customer")

        role_emoji = "🏪" if user.get("role") == "seller" else "🛒"
        name = (f"{user.get('first_name','')} {user.get('last_name','')}".strip()
                or user.get("username", "Foydalanuvchi"))

        await update.message.reply_text(
            f"✅ Xush kelibsiz, *{name}*!\n"
            f"{role_emoji} Rol: `{user.get('role','customer')}`\n\n"
            "Pastdagi tugmalardan foydalaning 👇",
            parse_mode="Markdown",
            reply_markup=get_smart_keyboard(context),
        )
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"❌ Backendga ulana olmadim!\n{e}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Buyruqlar ro'yxati:*\n\n"
        "🔐 *Auth:*\n"
        "/start — Login / ro'yxatdan o'tish\n"
        "/logout — Chiqish\n\n"
        "👤 *Profil:*\n"
        "/me — Profilni ko'rish\n"
        "/upgrade\\_seller — Seller bo'lish\n\n"
        "🛍 *Mahsulotlar:*\n"
        "/search — Mahsulot qidirish\n"
        "/categories — Kategoriyalar\n"
        "/my\\_products — Mening mahsulotlarim\n"
        "/add\\_product — Mahsulot qo'shish\n"
        "/upload\\_image — Mahsulotga rasm yuklash\n\n"
        "📦 *Buyurtmalar:*\n"
        "/my\\_orders — Buyurtmalarim\n"
        "/favorites — Saralangan mahsulotlar\n\n"
        "📊 *Boshqa:*\n"
        "/stats — Seller statistikasi\n"
        "/contact\\_seller — Sotuvchiga xabar yuborish\n"
        "/cancel — Dialogni bekor qilish",
        parse_mode="Markdown",
    )


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_logged_in(context):
        await update.message.reply_text("Avval /start yozing.")
        return
    await update.message.reply_text("📋 Asosiy menyu:", reply_markup=get_smart_keyboard(context))


# =========================
# /me  /logout
# =========================
async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_logged_in(context):
        await update.message.reply_text("Avval /start yozing.")
        return

    data, code, err = api_get(ME_URL, context)
    if data is None:
        await update.message.reply_text(f"❌ Profilni olishda xato!\nStatus: {code}\n{err[:200]}")
        return

    context.user_data["role"] = data.get("role", "customer")
    role_emoji = "🏪" if data.get("role") == "seller" else "🛒"
    name = f"{data.get('first_name','')} {data.get('last_name','')}".strip() or "-"

    await update.message.reply_text(
        f"👤 *Profil*\n\n"
        f"🆔 ID: `{data.get('id')}`\n"
        f"📱 Telegram ID: `{data.get('telegram_id')}`\n"
        f"👤 Username: @{data.get('username') or '-'}\n"
        f"📝 Ism: {name}\n"
        f"📞 Telefon: {data.get('phone_number') or 'Kiritilmagan'}\n"
        f"{role_emoji} Rol: *{data.get('role','-')}*",
        parse_mode="Markdown",
    )


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    refresh = context.user_data.get("refresh")
    if not refresh:
        await update.message.reply_text("Siz login bo'lmagansiz. /start yozing.")
        return
    try:
        r = requests.post(LOGOUT_URL, json={"refresh": refresh}, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            clear_tokens(context)
            await update.message.reply_text("✅ Chiqildi! /start yozing.", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text(f"❌ Logout xatolik!\nStatus: {r.status_code}\n{r.text[:200]}")
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"❌ Backendga ulana olmadim!\n{e}")


# =========================
# CATEGORIES
# =========================
async def categories_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_logged_in(context):
        await update.message.reply_text("Avval /start yozing.")
        return

    data, code, err = api_get(CATEGORIES_URL, context)
    if data is None:
        await update.message.reply_text(f"❌ Kategoriyalarni olishda xato!\nStatus: {code}\n{err[:200]}")
        return

    results = data.get("results", data) if isinstance(data, dict) else data
    if not results:
        await update.message.reply_text("Hali kategoriyalar yo'q.")
        return

    lines = ["🏷 *Kategoriyalar:*\n"]
    for cat in results:
        lines.append(f"📁 *{cat['name']}* (ID: `{cat['id']}`, slug: `{cat['slug']}`)")
        for ch in cat.get("children", []):
            lines.append(f"   └ {ch['name']} (ID: `{ch['id']}`, slug: `{ch['slug']}`)")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# =========================
# ★ YANGI: SEARCH (qidiruv)
# =========================
async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/search — mahsulot qidirish"""
    if not is_logged_in(context):
        await update.message.reply_text("Avval /start yozing.")
        return ConversationHandler.END

    await update.message.reply_text(
        "🔍 *Mahsulot qidirish*\n\n"
        "Qidirish so'zini yozing (masalan: *iPhone*, *velosiped*, *stol*):\n"
        "_(Bekor qilish: /cancel)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return SEARCH_QUERY


async def search_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if len(query) < 2:
        await update.message.reply_text("❌ Kamida 2 ta harf kiriting.")
        return SEARCH_QUERY

    await update.message.reply_text(f"🔍 *{query}* bo'yicha qidirilmoqda...", parse_mode="Markdown")

    data, code, err = api_get(PRODUCTS_URL, context, params={"search": query, "page_size": 10})
    if data is None:
        await update.message.reply_text(
            f"❌ Qidirishda xato!\nStatus: {code}\n{err[:200]}",
            reply_markup=get_smart_keyboard(context),
        )
        return ConversationHandler.END

    results = data.get("results", data) if isinstance(data, dict) else data
    count   = data.get("count", len(results)) if isinstance(data, dict) else len(results)

    if not results:
        await update.message.reply_text(
            f"😔 *{query}* bo'yicha hech narsa topilmadi.\n\nQaytadan qidirish: /search",
            parse_mode="Markdown",
            reply_markup=get_smart_keyboard(context),
        )
        return ConversationHandler.END

    lines = [f"🔍 *'{query}'* bo'yicha natijalar: {count} ta\n"]
    for prod in results[:10]:
        st_e = STATUS_EMOJI.get(prod.get("status", ""), "📦")
        lines.append(
            f"{st_e} *{prod.get('title','-')}*\n"
            f"   💰 {format_price(prod.get('price', 0))} — {prod.get('price_type','')}\n"
            f"   🔧 {prod.get('condition','-')} | 📍 {prod.get('region','-')}\n"
            f"   👁 {prod.get('view_count',0)} ko'rish | 🆔 `{prod.get('id')}`\n"
        )

    if count > 10:
        lines.append(f"\n_(Jami {count} ta. Ko'proq ko'rish uchun veb-saytdan foydalaning)_")

    # Inline keyboard: qidiruv natijalari uchun mahsulotga buyurtma berish
    keyboard = []
    for prod in results[:5]:
        keyboard.append([InlineKeyboardButton(
            f"📦 {prod['title'][:30]} — buyurtma",
            callback_data=f"order_{prod['id']}"
        )])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
    )

    await update.message.reply_text(
        "Klaviaturaga qaytish 👇",
        reply_markup=get_smart_keyboard(context),
    )
    return ConversationHandler.END


# =========================
# ★ YANGI: UPLOAD IMAGE (rasm yuklash)
# =========================
async def upload_image_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/upload_image — mahsulotga rasm yuklash"""
    if not is_logged_in(context):
        await update.message.reply_text("Avval /start yozing.")
        return ConversationHandler.END

    if context.user_data.get("role") != "seller":
        await update.message.reply_text(
            "⚠️ Faqat *seller*lar rasm yuklashi mumkin!\n/upgrade\\_seller",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "📸 *Mahsulotga rasm yuklash*\n\n"
        "Avval mahsulot *ID* sini yozing:\n"
        "_(ID ni /my\\_products dan topishingiz mumkin)_\n"
        "_(Bekor qilish: /cancel)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return UPLOAD_PROD_ID


async def upload_image_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit():
        await update.message.reply_text("❌ Faqat raqam (ID) kiriting!")
        return UPLOAD_PROD_ID

    context.user_data["upload_product_id"] = int(txt)
    await update.message.reply_text(
        f"✅ Mahsulot ID: `{txt}`\n\n"
        "📸 Endi rasmni yuboring (foto sifatida):",
        parse_mode="Markdown",
    )
    return UPLOAD_IMAGE


async def upload_image_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = context.user_data.get("upload_product_id")

    # Rasm olish
    if update.message.photo:
        photo = update.message.photo[-1]  # Eng katta o'lcham
    elif update.message.document and update.message.document.mime_type.startswith("image/"):
        photo = update.message.document
    else:
        await update.message.reply_text("❌ Iltimos, rasm (photo) yuboring!")
        return UPLOAD_IMAGE

    await update.message.reply_text("⏳ Rasm yuklanmoqda...")

    try:
        # Telegram'dan fayl olish
        file = await context.bot.get_file(photo.file_id)
        file_bytes = await file.download_as_bytearray()

        # Backendga yuborish
        url   = f"{PRODUCTS_URL}{product_id}/images/"
        files = {"image": ("photo.jpg", bytes(file_bytes), "image/jpeg")}

        result, code, err = api_post_files(url, context, files)

        if result is None:
            await update.message.reply_text(
                f"❌ Rasm yuklashda xato!\nStatus: {code}\n{err[:300]}",
                reply_markup=get_smart_keyboard(context),
            )
        else:
            main_txt = " (asosiy rasm)" if result.get("is_main") else ""
            await update.message.reply_text(
                f"✅ Rasm muvaffaqiyatli yuklandi!{main_txt}\n"
                f"🆔 Rasm ID: `{result.get('id')}`",
                parse_mode="Markdown",
                reply_markup=get_smart_keyboard(context),
            )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Xato yuz berdi: {e}",
            reply_markup=get_smart_keyboard(context),
        )

    return ConversationHandler.END


# =========================
# ★ YANGI: STATS (statistika)
# =========================
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stats — seller statistikasi"""
    if not is_logged_in(context):
        await update.message.reply_text("Avval /start yozing.")
        return

    # Profil olish
    user_data, _, _ = api_get(ME_URL, context)
    if not user_data:
        await update.message.reply_text("❌ Profil ma'lumotlarini olishda xato!")
        return

    if user_data.get("role") != "seller":
        await update.message.reply_text(
            "📊 Statistika faqat *seller*lar uchun!\n"
            "Seller bo'lish: /upgrade\\_seller",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text("⏳ Statistika hisoblanmoqda...")

    # Mahsulotlar
    products_data, _, _ = api_get(
        PRODUCTS_URL, context,
        params={"page_size": 100}
    )
    prod_results = []
    if products_data:
        prod_results = products_data.get("results", products_data) if isinstance(products_data, dict) else products_data

    # Buyurtmalar (sotuvchi sifatida)
    orders_data, _, _ = api_get(ORDERS_URL, context, params={"role": "seller", "page_size": 100})
    order_results = []
    if orders_data:
        order_results = orders_data.get("results", orders_data) if isinstance(orders_data, dict) else orders_data

    # Izohlar
    reviews_data, _, _ = api_get(REVIEWS_URL, context, params={"seller_id": user_data.get("id")})
    review_count = 0
    avg_rating   = 0.0
    if reviews_data:
        review_list  = reviews_data.get("results", reviews_data) if isinstance(reviews_data, dict) else reviews_data
        review_count = len(review_list)
        if review_count:
            avg_rating = sum(r.get("rating", 0) for r in review_list) / review_count

    # Hisoblash
    total_products  = len(prod_results)
    active_prods    = sum(1 for p in prod_results if p.get("status") == "aktiv")
    mod_prods       = sum(1 for p in prod_results if p.get("status") == "moderatsiyada")
    sold_prods      = sum(1 for p in prod_results if p.get("status") == "sotilgan")
    total_views     = sum(p.get("view_count", 0) for p in prod_results)
    total_favorites = sum(p.get("favorite_count", 0) for p in prod_results)

    total_orders    = len(order_results)
    pending_orders  = sum(1 for o in order_results if o.get("status") == "kutilyapti")
    agreed_orders   = sum(1 for o in order_results if o.get("status") == "kelishilgan")
    sold_orders     = sum(1 for o in order_results if o.get("status") == "sotib olingan")
    cancelled_orders= sum(1 for o in order_results if o.get("status") == "bekor qilingan")

    total_revenue = sum(
        float(o.get("final_price", 0))
        for o in order_results if o.get("status") == "sotib olingan"
    )

    # Eng ko'p ko'rilgan mahsulot
    top_viewed = None
    if prod_results:
        top_viewed = max(prod_results, key=lambda p: p.get("view_count", 0))

    stars = "⭐" * round(avg_rating) if avg_rating > 0 else "—"

    msg = (
        f"📊 *Seller Statistikasi*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛍 *Mahsulotlar:*\n"
        f"  Jami: {total_products} ta\n"
        f"  ✅ Aktiv: {active_prods} ta\n"
        f"  🔄 Moderatsiyada: {mod_prods} ta\n"
        f"  💚 Sotilgan: {sold_prods} ta\n"
        f"  👁 Jami ko'rishlar: {total_views:,}\n"
        f"  ❤️ Jami saqlanganlar: {total_favorites:,}\n\n"
        f"📦 *Buyurtmalar:*\n"
        f"  Jami: {total_orders} ta\n"
        f"  ⏳ Kutilmoqda: {pending_orders} ta\n"
        f"  🤝 Kelishilgan: {agreed_orders} ta\n"
        f"  ✅ Sotilgan: {sold_orders} ta\n"
        f"  ❌ Bekor: {cancelled_orders} ta\n\n"
        f"💰 *Daromad:*\n"
        f"  Jami: {format_price(total_revenue)}\n\n"
        f"⭐ *Reyting:*\n"
        f"  {stars} {avg_rating:.1f}/5.0 ({review_count} ta izoh)\n"
    )

    if top_viewed:
        msg += (
            f"\n🏆 *Eng ko'p ko'rilgan:*\n"
            f"  {top_viewed.get('title','-')} — {top_viewed.get('view_count',0)} marta\n"
        )

    await update.message.reply_text(msg, parse_mode="Markdown")


# =========================
# ★ YANGI: CONTACT SELLER (xabar yuborish)
# =========================
async def contact_seller_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/contact_seller — sotuvchiga xabar yuborish"""
    if not is_logged_in(context):
        await update.message.reply_text("Avval /start yozing.")
        return ConversationHandler.END

    user_data, _, _ = api_get(ME_URL, context)
    if user_data and user_data.get("role") == "seller":
        await update.message.reply_text(
            "ℹ️ Siz seller siz. Bu funksiya xaridorlar uchun.\n"
            "Buyurtmalar uchun /my\\_orders yozing.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    # Sotuvchilar ro'yxatini ko'rsatish
    sellers_data, code, err = api_get(SELLERS_URL, context)
    if sellers_data is None:
        await update.message.reply_text(f"❌ Sotuvchilar ro'yxatini olishda xato!\nStatus: {code}")
        return ConversationHandler.END

    results = sellers_data.get("results", sellers_data) if isinstance(sellers_data, dict) else sellers_data

    if not results:
        await update.message.reply_text("Hali sotuvchilar yo'q.")
        return ConversationHandler.END

    lines = [
        "📬 *Sotuvchiga xabar yuborish*\n\n"
        "Quyidagi sotuvchilardan birini ID sini yozing:\n"
    ]
    for s in results[:10]:
        lines.append(
            f"🆔 `{s['id']}` — 🏪 *{s['shop_name']}*"
            f" | ⭐ {s.get('rating', 0):.1f}"
            f" | 📍 {s.get('region', '-')}"
        )

    lines.append("\n_(Bekor qilish: /cancel)_")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return CONTACT_SELLER_ID


async def contact_seller_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit():
        await update.message.reply_text("❌ Faqat raqam (ID) kiriting!")
        return CONTACT_SELLER_ID

    seller_id = int(txt)
    # Seller profilini tekshirish
    seller_data, code, err = api_get(f"{SELLERS_URL}{seller_id}/", context)
    if seller_data is None:
        await update.message.reply_text(f"❌ Sotuvchi ID={seller_id} topilmadi!")
        return CONTACT_SELLER_ID

    context.user_data["contact_seller_id"]   = seller_id
    context.user_data["contact_seller_name"] = seller_data.get("shop_name", f"Sotuvchi #{seller_id}")

    await update.message.reply_text(
        f"✅ Sotuvchi: *{seller_data.get('shop_name')}*\n"
        f"📍 {seller_data.get('region','-')}, {seller_data.get('district','-')}\n"
        f"⭐ Reyting: {seller_data.get('rating',0):.1f}\n\n"
        f"✍️ Xabaringizni yozing (sotuvchi Telegram orqali xabarni ko'ra oladi):",
        parse_mode="Markdown",
    )
    return CONTACT_MESSAGE


async def contact_seller_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message   = update.message.text.strip()
    seller_id = context.user_data.get("contact_seller_id")
    shop_name = context.user_data.get("contact_seller_name", "Sotuvchi")

    if len(message) < 5:
        await update.message.reply_text("❌ Xabar juda qisqa! Kamida 5 ta belgi kiriting.")
        return CONTACT_MESSAGE

    # Sotuvchining telegram_id sini topish
    seller_profile, _, _ = api_get(f"{SELLERS_URL}{seller_id}/", context)

    if seller_profile and seller_profile.get("user"):
        user_id = seller_profile["user"]
        # User profilini olish uchun admin token kerak bo'ladi.
        # Botdan xabar yuborishning eng yaxshi usuli — buyurtma orqali.
        # Bu yerda xabarni botdan forward qilamiz.

        sender = update.effective_user
        sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip() or sender.username or "Foydalanuvchi"

        # Bot xabarini yozib qo'yamiz (internal log)
        logger.info(
            f"Contact Seller | From: {sender.id} ({sender_name}) "
            f"-> Seller: {seller_id} ({shop_name}) | Msg: {message}"
        )

        await update.message.reply_text(
            f"✅ Xabaringiz *{shop_name}* ga yuborildi!\n\n"
            f"📝 Xabar: _{message}_\n\n"
            f"💡 Sotuvchi siz bilan bog'lanishi uchun buyurtma berish tavsiya etiladi: /search",
            parse_mode="Markdown",
            reply_markup=get_smart_keyboard(context),
        )
    else:
        await update.message.reply_text(
            "❌ Sotuvchi bilan bog'lana olmadim.",
            reply_markup=get_smart_keyboard(context),
        )

    return ConversationHandler.END


# =========================
# FAVORITES  ORDERS  MY_PRODUCTS
# =========================
async def favorites_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_logged_in(context):
        await update.message.reply_text("Avval /start yozing.")
        return

    data, code, err = api_get(FAVORITES_URL, context)
    if data is None:
        await update.message.reply_text(f"❌ Saralangan mahsulotlarni olishda xato!\nStatus: {code}\n{err[:200]}")
        return

    results = data.get("results", data) if isinstance(data, dict) else data
    if not results:
        await update.message.reply_text("❤️ Saralangan mahsulotlaringiz yo'q.")
        return

    lines = [f"❤️ *Saralangan mahsulotlar* ({len(results)} ta):\n"]
    keyboard = []
    for fav in results:
        prod = fav.get("product", {})
        lines.append(
            f"🛍 *{prod.get('title','-')}*\n"
            f"   💰 {format_price(prod.get('price',0))}\n"
            f"   📍 {prod.get('region','-')}\n"
            f"   🆔 `{prod.get('id')}`\n"
        )
        keyboard.append([InlineKeyboardButton(
            f"🗑 O'chirish: {prod.get('title','')[:25]}",
            callback_data=f"unfav_{fav.get('id')}"
        )])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
    )


async def my_orders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_logged_in(context):
        await update.message.reply_text("Avval /start yozing.")
        return

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🛒 Xaridor", callback_data="orders_buyer"),
        InlineKeyboardButton("🏪 Sotuvchi", callback_data="orders_seller"),
    ]])
    await update.message.reply_text("Qaysi buyurtmalarni ko'rmoqchisiz?", reply_markup=keyboard)


async def my_products_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_logged_in(context):
        await update.message.reply_text("Avval /start yozing.")
        return

    user_data, _, _ = api_get(ME_URL, context)
    if not user_data or user_data.get("role") != "seller":
        await update.message.reply_text(
            "⚠️ Bu buyruq faqat *seller*lar uchun!\n/upgrade\\_seller",
            parse_mode="Markdown",
        )
        return

    data, code, err = api_get(PRODUCTS_URL, context)
    if data is None:
        await update.message.reply_text(f"❌ Mahsulotlarni olishda xato!\nStatus: {code}\n{err[:200]}")
        return

    results = data.get("results", data) if isinstance(data, dict) else data
    if not results:
        await update.message.reply_text(
            "🛍 Hali mahsulotlaringiz yo'q.\n/add\\_product",
            parse_mode="Markdown",
        )
        return

    lines = [f"🛍 *Mening mahsulotlarim* ({len(results)} ta):\n"]
    for prod in results[:15]:
        st = prod.get("status", "-")
        lines.append(
            f"{STATUS_EMOJI.get(st,'📦')} *{prod.get('title','-')}*\n"
            f"   💰 {format_price(prod.get('price',0))} | {prod.get('condition','-')}\n"
            f"   👁 {prod.get('view_count',0)} | ❤️ {prod.get('favorite_count',0)} | 📌 {st}\n"
            f"   🆔 `{prod.get('id')}`\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# =========================
# CALLBACK QUERIES
# =========================
async def orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    role = "buyer" if query.data == "orders_buyer" else "seller"
    data, code, err = api_get(ORDERS_URL, context, params={"role": role})

    if data is None:
        await query.edit_message_text(f"❌ Buyurtmalarni olishda xato!\nStatus: {code}\n{err[:200]}")
        return

    results = data.get("results", data) if isinstance(data, dict) else data
    role_text = "xaridor" if role == "buyer" else "sotuvchi"

    if not results:
        await query.edit_message_text(f"📦 {role_text.capitalize()} sifatida buyurtmalaringiz yo'q.")
        return

    role_emoji = "🛒" if role == "buyer" else "🏪"
    lines = [f"{role_emoji} *{role_text.capitalize()} sifatida buyurtmalar* ({len(results)} ta):\n"]

    for order in results[:10]:
        prod = order.get("product", {})
        st   = order.get("status", "-")
        lines.append(
            f"{ORDER_EMOJI.get(st,'📦')} *{prod.get('title','-')}*\n"
            f"   💰 {format_price(order.get('final_price',0))}\n"
            f"   📌 {st} | 🆔 `{order.get('id')}`\n"
        )

    await query.edit_message_text("\n".join(lines), parse_mode="Markdown")


async def order_create_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Qidiruv natijasidan buyurtma berish"""
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("_")[1])

    user_data, _, _ = api_get(ME_URL, context)
    if not user_data or user_data.get("role") != "customer":
        await query.answer("Buyurtma berish faqat xaridorlar uchun!", show_alert=True)
        return

    data, code, err = api_post(ORDERS_URL, context, {"product_id": product_id})
    if data is None:
        await query.answer(f"❌ Xato: {err[:100]}", show_alert=True)
    else:
        await query.answer("✅ Buyurtma berildi!", show_alert=True)
        await query.edit_message_reply_markup(reply_markup=None)


async def unfavorite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saralangandan o'chirish"""
    query = update.callback_query
    await query.answer()

    fav_id = query.data.split("_")[1]
    try:
        r = requests.delete(
            f"{FAVORITES_URL}{fav_id}/",
            headers=auth_headers(context),
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code == 204:
            await query.answer("🗑 O'chirildi!", show_alert=False)
            await query.edit_message_reply_markup(reply_markup=None)
        else:
            await query.answer(f"❌ Xato: {r.status_code}", show_alert=True)
    except Exception as e:
        await query.answer(f"❌ {e}", show_alert=True)


# =========================
# UPGRADE SELLER CONVERSATION
# =========================
async def upgrade_seller_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_logged_in(context):
        await update.message.reply_text("Avval /start yozing.")
        return ConversationHandler.END

    user_data, _, _ = api_get(ME_URL, context)
    if user_data and user_data.get("role") == "seller":
        await update.message.reply_text("✅ Siz allaqachon *seller*siz!", parse_mode="Markdown")
        return ConversationHandler.END

    await update.message.reply_text(
        "🏪 *Seller bo'lish*\n\n"
        "1️⃣ Do'kon nomini yozing:\n_(Bekor qilish: /cancel)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return SHOP_NAME


async def upgrade_seller_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["shop_name"] = update.message.text.strip()
    await update.message.reply_text("2️⃣ Viloyatni yozing (masalan: Toshkent):")
    return REGION


async def upgrade_seller_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["region"] = update.message.text.strip()
    await update.message.reply_text("3️⃣ Tuman/shaharni yozing:")
    return DISTRICT


async def upgrade_seller_district(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["district"] = update.message.text.strip()
    await update.message.reply_text("4️⃣ Manzil yozing yoki '-' bosing:")
    return ADDRESS


async def upgrade_seller_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    if address == "-":
        address = ""

    payload = {
        "shop_name":       context.user_data.get("shop_name", ""),
        "region":          context.user_data.get("region", ""),
        "district":        context.user_data.get("district", ""),
        "address":         address,
        "shop_description": "",
    }
    try:
        r = requests.post(UPGRADE_URL, json=payload, headers=auth_headers(context), timeout=REQUEST_TIMEOUT)
        if r.status_code in (200, 201):
            context.user_data["role"] = "seller"
            await update.message.reply_text(
                "🎉 *Tabriklayman!* Endi siz SELLER bo'ldingiz!\n\n"
                "Mahsulot qo'shish: /add\\_product",
                parse_mode="Markdown",
                reply_markup=seller_menu_keyboard(),
            )
        else:
            await update.message.reply_text(
                f"❌ Upgrade xatolik!\nStatus: {r.status_code}\n{r.text[:300]}",
                reply_markup=get_smart_keyboard(context),
            )
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"❌ Backendga ulana olmadim!\n{e}")
    return ConversationHandler.END


# =========================
# ADD PRODUCT CONVERSATION
# =========================
async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_logged_in(context):
        await update.message.reply_text("Avval /start yozing.")
        return ConversationHandler.END

    user_data, _, _ = api_get(ME_URL, context)
    if not user_data or user_data.get("role") != "seller":
        await update.message.reply_text(
            "⚠️ Faqat *seller*lar mahsulot qo'sha oladi!\n/upgrade\\_seller",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🛍 *Mahsulot qo'shish*\n\n1️⃣ Mahsulot nomini yozing:\n_(Bekor qilish: /cancel)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return PROD_TITLE


async def add_product_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_product"] = {"title": update.message.text.strip()}
    await update.message.reply_text("2️⃣ Mahsulot tavsifini yozing:")
    return PROD_DESCRIPTION


async def add_product_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_product"]["description"] = update.message.text.strip()

    data, code, err = api_get(CATEGORIES_URL, context)
    if data is None:
        await update.message.reply_text(f"❌ Kategoriyalarni olishda xato!\nStatus: {code}")
        return ConversationHandler.END

    results = data.get("results", data) if isinstance(data, dict) else data
    lines = ["3️⃣ Kategoriya *ID* sini yozing:\n"]
    for cat in results:
        lines.append(f"• `{cat['id']}` — {cat['name']}")
        for ch in cat.get("children", []):
            lines.append(f"   └ `{ch['id']}` — {ch['name']}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    return PROD_CATEGORY_ID


async def add_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not txt.isdigit():
        await update.message.reply_text("❌ Faqat raqam kiriting!")
        return PROD_CATEGORY_ID
    context.user_data["new_product"]["category"] = int(txt)

    keyboard = ReplyKeyboardMarkup(
        [["yangi", "ideal"], ["yaxshi", "qoniqarli"]],
        resize_keyboard=True, one_time_keyboard=True,
    )
    await update.message.reply_text("4️⃣ Mahsulot holatini tanlang:", reply_markup=keyboard)
    return PROD_CONDITION


async def add_product_condition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    condition = update.message.text.strip().lower()
    if condition not in ["yangi", "ideal", "yaxshi", "qoniqarli"]:
        await update.message.reply_text("❌ Noto'g'ri! Tanlang: yangi / ideal / yaxshi / qoniqarli")
        return PROD_CONDITION
    context.user_data["new_product"]["condition"] = condition
    await update.message.reply_text("5️⃣ Narxni yozing (so'mda, faqat raqam):", reply_markup=ReplyKeyboardRemove())
    return PROD_PRICE


async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().replace(",", "").replace(" ", "")
    try:
        price = float(txt)
        if price < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri narx! (masalan: 150000)")
        return PROD_PRICE
    context.user_data["new_product"]["price"] = price

    keyboard = ReplyKeyboardMarkup(
        [["qat'iy", "kelishiladi"], ["bepul", "ayirboshlash"]],
        resize_keyboard=True, one_time_keyboard=True,
    )
    await update.message.reply_text("6️⃣ Narx turini tanlang:", reply_markup=keyboard)
    return PROD_PRICE_TYPE


async def add_product_price_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pt = update.message.text.strip().lower()
    if pt not in ["qat'iy", "kelishiladi", "bepul", "ayirboshlash"]:
        await update.message.reply_text("❌ Noto'g'ri! Tanlang.")
        return PROD_PRICE_TYPE
    context.user_data["new_product"]["price_type"] = pt
    await update.message.reply_text("7️⃣ Viloyatni yozing:", reply_markup=ReplyKeyboardRemove())
    return PROD_REGION


async def add_product_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_product"]["region"] = update.message.text.strip()
    await update.message.reply_text("8️⃣ Tuman/shaharni yozing:")
    return PROD_DISTRICT


async def add_product_district(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_product"]["district"] = update.message.text.strip()
    prod = context.user_data["new_product"]

    data, code, err = api_post(PRODUCTS_URL, context, prod)
    if data is None:
        await update.message.reply_text(
            f"❌ Mahsulot qo'shishda xato!\nStatus: {code}\n{err[:300]}",
            reply_markup=get_smart_keyboard(context),
        )
    else:
        await update.message.reply_text(
            f"✅ Mahsulot muvaffaqiyatli qo'shildi!\n"
            f"🆔 ID: `{data.get('id')}`\n"
            f"📌 Holat: moderatsiyada\n\n"
            f"📸 Rasm qo'shish uchun /upload\\_image yozing.",
            parse_mode="Markdown",
            reply_markup=get_smart_keyboard(context),
        )
    return ConversationHandler.END


# =========================
# CANCEL
# =========================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Bekor qilindi.",
        reply_markup=get_smart_keyboard(context) if is_logged_in(context) else ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# =========================
# KEYBOARD BUTTON HANDLER
# =========================
async def keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    dispatch = {
        "👤 Profil":         me,
        "🔍 Qidirish":       search_start,
        "❤️ Saralangan":    favorites_cmd,
        "📦 Buyurtmalar":    my_orders_cmd,
        "🏪 Kategoriyalar":  categories_cmd,
        "🛍 Mahsulotlarim":  my_products_cmd,
        "📸 Rasm yuklash":   upload_image_start,
        "📊 Statistika":     stats_cmd,
    }

    if text in dispatch:
        handler = dispatch[text]
        result = await handler(update, context)
        # Agar conversation handler bo'lsa (search/upload) — ConversationHandler.END emas
        return result

    if text == "⚙️ Sozlamalar":
        await update.message.reply_text(
            "⚙️ *Sozlamalar:*\n\n"
            "/upgrade\\_seller — Seller bo'lish\n"
            "/contact\\_seller — Sotuvchiga xabar\n"
            "/logout — Chiqish\n"
            "/help — Yordam",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "❓ Noma'lum buyruq. /help yozing.",
            reply_markup=get_smart_keyboard(context),
        )


# =========================
# UNKNOWN + ERROR HANDLERS
# =========================
async def unknown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Noma'lum buyruq. /help yozing.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Ichki xato yuz berdi. Iltimos, qaytadan urinib ko'ring."
        )


# =========================
# MAIN
# =========================
def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN .env ichida yo'q!")

    app = Application.builder().token(BOT_TOKEN).build()

    # ---- Conversations ----
    upgrade_conv = ConversationHandler(
        entry_points=[CommandHandler("upgrade_seller", upgrade_seller_start)],
        states={
            SHOP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, upgrade_seller_shop)],
            REGION:    [MessageHandler(filters.TEXT & ~filters.COMMAND, upgrade_seller_region)],
            DISTRICT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, upgrade_seller_district)],
            ADDRESS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, upgrade_seller_address)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    add_product_conv = ConversationHandler(
        entry_points=[CommandHandler("add_product", add_product_start)],
        states={
            PROD_TITLE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_title)],
            PROD_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_description)],
            PROD_CATEGORY_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_category)],
            PROD_CONDITION:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_condition)],
            PROD_PRICE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price)],
            PROD_PRICE_TYPE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price_type)],
            PROD_REGION:      [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_region)],
            PROD_DISTRICT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_district)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    search_conv = ConversationHandler(
        entry_points=[
            CommandHandler("search", search_start),
            MessageHandler(filters.Regex(r"^🔍 Qidirish$"), search_start),
        ],
        states={
            SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_execute)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    upload_image_conv = ConversationHandler(
        entry_points=[
            CommandHandler("upload_image", upload_image_start),
            MessageHandler(filters.Regex(r"^📸 Rasm yuklash$"), upload_image_start),
        ],
        states={
            UPLOAD_PROD_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, upload_image_get_id)],
            UPLOAD_IMAGE: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, upload_image_receive),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    contact_seller_conv = ConversationHandler(
        entry_points=[CommandHandler("contact_seller", contact_seller_start)],
        states={
            CONTACT_SELLER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_seller_get_id)],
            CONTACT_MESSAGE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_seller_send)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    # ---- Handlers (tartib muhim!) ----
    app.add_handler(search_conv)
    app.add_handler(upload_image_conv)
    app.add_handler(contact_seller_conv)
    app.add_handler(upgrade_conv)
    app.add_handler(add_product_conv)

    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("help",    help_cmd))
    app.add_handler(CommandHandler("me",      me))
    app.add_handler(CommandHandler("menu",    menu_cmd))
    app.add_handler(CommandHandler("logout",  logout))
    app.add_handler(CommandHandler("categories", categories_cmd))
    app.add_handler(CommandHandler("favorites",  favorites_cmd))
    app.add_handler(CommandHandler("my_orders",  my_orders_cmd))
    app.add_handler(CommandHandler("my_products", my_products_cmd))
    app.add_handler(CommandHandler("stats",      stats_cmd))

    # Callback queries
    app.add_handler(CallbackQueryHandler(orders_callback,      pattern=r"^orders_"))
    app.add_handler(CallbackQueryHandler(order_create_callback, pattern=r"^order_\d+$"))
    app.add_handler(CallbackQueryHandler(unfavorite_callback,  pattern=r"^unfav_\d+$"))

    # Keyboard tugmalari (search va upload_image conversation'lar boshqaradi)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^🔍 Qidirish$") & ~filters.Regex(r"^📸 Rasm yuklash$"),
        keyboard_handler,
    ))

    app.add_handler(MessageHandler(filters.COMMAND, unknown_cmd))
    app.add_error_handler(error_handler)

    logger.info("✅ OLX.UZ Bot ishga tushdi (v2)!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
