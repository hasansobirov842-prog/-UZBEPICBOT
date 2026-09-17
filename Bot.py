import os
import sqlite3
import logging
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================================================
# UZB EPIC BOT
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

DB_NAME = "uzb_epic.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# DATABASE
# =========================================================

def db():
    return sqlite3.connect(DB_NAME)


def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product TEXT,
            amount TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    """)

    con.commit()
    con.close()


def save_user(user):
    con = db()
    cur = con.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO users
        (id, username, first_name, joined_at)
        VALUES (?, ?, ?, ?)
    """, (
        user.id,
        user.username or "",
        user.first_name or "",
        datetime.now().isoformat(),
    ))

    cur.execute("""
        UPDATE users
        SET username = ?, first_name = ?
        WHERE id = ?
    """, (
        user.username or "",
        user.first_name or "",
        user.id,
    ))

    con.commit()
    con.close()


def add_order(user_id, product, amount):
    con = db()
    cur = con.cursor()

    cur.execute("""
        INSERT INTO orders
        (user_id, product, amount, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        product,
        amount,
        "pending",
        datetime.now().isoformat(),
    ))

    order_id = cur.lastrowid

    con.commit()
    con.close()

    return order_id


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("⭐ Telegram Stars", callback_data="stars"),
            InlineKeyboardButton("💎 TON", callback_data="ton"),
        ],
        [
            InlineKeyboardButton("🎁 Gifts", callback_data="gifts"),
            InlineKeyboardButton("🛒 Buyurtmalarim", callback_data="orders"),
        ],
        [
            InlineKeyboardButton("👤 Profil", callback_data="profile"),
            InlineKeyboardButton("ℹ️ Yordam", callback_data="help"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def back_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Orqaga", callback_data="home")]
    ])


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    save_user(user)

    text = (
        "✨ <b>UZB EPIC</b>\n\n"
        "Premium Telegram xizmatlari uchun zamonaviy bot.\n\n"
        "⭐ Stars\n"
        "💎 TON\n"
        "🎁 Gifts\n\n"
        "Kerakli bo‘limni tanlang 👇"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================================================
# STARS
# =========================================================

async def stars_menu(query):

    text = (
        "⭐ <b>TELEGRAM STARS</b>\n\n"
        "Kerakli Stars paketini tanlang:"
    )

    keyboard = [
        [InlineKeyboardButton("⭐ 50 Stars", callback_data="buy_stars_50")],
        [InlineKeyboardButton("⭐ 100 Stars", callback_data="buy_stars_100")],
        [InlineKeyboardButton("⭐ 250 Stars", callback_data="buy_stars_250")],
        [InlineKeyboardButton("⭐ 500 Stars", callback_data="buy_stars_500")],
        [InlineKeyboardButton("⭐ 1000 Stars", callback_data="buy_stars_1000")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="home")],
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# TON
# =========================================================

async def ton_menu(query):

    text = (
        "💎 <b>TON</b>\n\n"
        "TON bo‘limi tayyor.\n"
        "Bu yerga keyinchalik o‘zingizning TON mahsulotlaringiz "
        "va narxlaringizni qo‘shishingiz mumkin."
    )

    keyboard = [
        [InlineKeyboardButton("💎 TON olish", callback_data="ton_buy")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="home")],
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# GIFTS
# =========================================================

async def gifts_menu(query):

    text = (
        "🎁 <b>TELEGRAM GIFTS</b>\n\n"
        "Gift bo‘limi.\n\n"
        "Mahsulotlar keyinchalik shu yerga qo‘shiladi."
    )

    keyboard = [
        [InlineKeyboardButton("🎁 Gift buyurtma", callback_data="gift_order")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="home")],
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# BUY STARS
# =========================================================

async def buy_stars(query, amount):

    prices = {
        "50": "Narxni o‘zingiz qo‘yasiz",
        "100": "Narxni o‘zingiz qo‘yasiz",
        "250": "Narxni o‘zingiz qo‘yasiz",
        "500": "Narxni o‘zingiz qo‘yasiz",
        "1000": "Narxni o‘zingiz qo‘yasiz",
    }

    product = f"{amount} Stars"

    text = (
        f"⭐ <b>{amount} Stars</b>\n\n"
        f"💰 {prices[amount]}\n\n"
        "Buyurtma berish uchun tugmani bosing."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🛒 Buyurtma berish",
                callback_data=f"order_stars_{amount}"
            )
        ],
        [
            InlineKeyboardButton(
                "◀️ Orqaga",
                callback_data="stars"
            )
        ],
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# ORDERS
# =========================================================

async def my_orders(query):

    user_id = query.from_user.id

    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT id, product, amount, status
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 10
    """, (user_id,))

    rows = cur.fetchall()
    con.close()

    if not rows:
        text = (
            "🛒 <b>Buyurtmalarim</b>\n\n"
            "Sizda hali buyurtmalar yo‘q."
        )
    else:
        text = "🛒 <b>Buyurtmalarim</b>\n\n"

        for order_id, product, amount, status in rows:
            text += (
                f"🆔 #{order_id}\n"
                f"📦 {product}\n"
                f"💰 {amount}\n"
                f"📌 {status}\n\n"
            )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=back_button(),
    )


# =========================================================
# PROFILE
# =========================================================

async def profile(query):

    user = query.from_user

    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM orders WHERE user_id = ?",
        (user.id,)
    )

    order_count = cur.fetchone()[0]

    con.close()

    username = (
        f"@{user.username}"
        if user.username
        else "Username yo‘q"
    )

    text = (
        "👤 <b>PROFIL</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Username: {username}\n"
        f"🛒 Buyurtmalar: {order_count}\n\n"
        "UZB EPIC ✨"
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=back_button(),
    )


# =========================================================
# HELP
# =========================================================

async def help_menu(query):

    text = (
        "ℹ️ <b>YORDAM</b>\n\n"
        "⭐ Stars — Telegram Stars\n"
        "💎 TON — TON bo‘limi\n"
        "🎁 Gifts — Telegram Gifts\n"
        "🛒 Buyurtmalarim — buyurtmalar tarixi\n"
        "👤 Profil — akkaunt ma’lumotlari\n\n"
        "Muammo bo‘lsa administratorga murojaat qiling."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "👨‍💻 Admin",
                url="https://t.me/"
            )
        ],
        [
            InlineKeyboardButton(
                "◀️ Orqaga",
                callback_data="home"
            )
        ],
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# ADMIN PANEL
# =========================================================

async def admin_panel(query):

    if query.from_user.id != ADMIN_ID:
        await query.answer(
            "⛔ Siz admin emassiz.",
            show_alert=True
        )
        return

    con = db()
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders")
    orders = cur.fetchone()[0]

    con.close()

    text = (
        "👑 <b>ADMIN PANEL</b>\n\n"
        f"👥 Foydalanuvchilar: {users}\n"
        f"🛒 Buyurtmalar: {orders}\n"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📊 Statistika",
                callback_data="admin_stats"
            )
        ],
        [
            InlineKeyboardButton(
                "◀️ Orqaga",
                callback_data="home"
            )
        ],
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# CALLBACKS
# =========================================================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "home":

        text = (
            "✨ <b>UZB EPIC</b>\n\n"
            "Premium Telegram xizmatlari uchun bot.\n\n"
            "Kerakli bo‘limni tanlang 👇"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

    elif data == "stars":
        await stars_menu(query)

    elif data == "ton":
        await ton_menu(query)

    elif data == "gifts":
        await gifts_menu(query)

    elif data == "orders":
        await my_orders(query)

    elif data == "profile":
        await profile(query)

    elif data == "help":
        await help_menu(query)

    elif data == "admin":
        await admin_panel(query)

    elif data == "admin_stats":

        if query.from_user.id != ADMIN_ID:
            return

        con = db()
        cur = con.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM orders")
        orders = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM orders WHERE status = 'pending'"
        )
        pending = cur.fetchone()[0]

        con.close()

        text = (
            "📊 <b>STATISTIKA</b>\n\n"
            f"👥 Users: {users}\n"
            f"🛒 Orders: {orders}\n"
            f"⏳ Pending: {pending}"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=back_button(),
        )

    elif data.startswith("buy_stars_"):

        amount = data.replace("buy_stars_", "")
        await buy_stars(query, amount)

    elif data.startswith("order_stars_"):

        amount = data.replace("order_stars_", "")

        order_id = add_order(
            query.from_user.id,
            f"{amount} Stars",
            "Narx belgilanmagan",
        )

        text = (
            "✅ <b>BUYURTMA QABUL QILINDI</b>\n\n"
            f"📦 Mahsulot: {amount} Stars\n"
            f"🆔 Buyurtma: #{order_id}\n\n"
            "Admin buyurtmani ko‘rib chiqadi."
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=back_button(),
        )

        if ADMIN_ID:

            try:
                await context.bot.send_message(
                    ADMIN_ID,
                    (
                        "🔔 <b>YANGI BUYURTMA</b>\n\n"
                        f"👤 User ID: <code>{query.from_user.id}</code>\n"
                        f"📦 {amount} Stars\n"
                        f"🆔 Order: #{order_id}"
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.error(e)

    elif data == "ton_buy":

        order_id = add_order(
            query.from_user.id,
            "TON",
            "Narx belgilanmagan",
        )

        await query.edit_message_text(
            (
                "💎 <b>TON BUYURTMA</b>\n\n"
                f"🆔 Buyurtma: #{order_id}\n\n"
                "TON mahsulotlari va narxlarini "
                "keyinchalik o‘zingiz qo‘shishingiz mumkin."
            ),
            parse_mode="HTML",
            reply_markup=back_button(),
        )

    elif data == "gift_order":

        order_id = add_order(
            query.from_user.id,
            "Telegram Gift",
            "Narx belgilanmagan",
        )

        await query.edit_message_text(
            (
                "🎁 <b>GIFT BUYURTMA</b>\n\n"
                f"🆔 Buyurtma: #{order_id}\n\n"
                "Buyurtma qabul qilindi."
            ),
            parse_mode="HTML",
            reply_markup=back_button(),
        )


# =========================================================
# ADMIN COMMAND
# =========================================================

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Ruxsat yo‘q.")
        return

    con = db()
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders")
    orders = cur.fetchone()[0]

    con.close()

    await update.message.reply_text(
        (
            "👑 <b>UZB EPIC ADMIN</b>\n\n"
            f"👥 Users: {users}\n"
            f"🛒 Orders: {orders}"
        ),
        parse_mode="HTML",
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. GitHub Secrets ichida BOT_TOKEN yarating."
        )

    if not ADMIN_ID:
        raise RuntimeError(
            "ADMIN_ID topilmadi. GitHub Secrets ichida ADMIN_ID yarating."
        )

    init_db()

    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("admin", admin_command)
    )

    app.add_handler(
        CallbackQueryHandler(callback_handler)
    )

    print("UZB EPIC BOT ISHLADI!")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
