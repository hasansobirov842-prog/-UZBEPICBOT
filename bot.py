import os
import sqlite3
import logging
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================================================
# SOZLAMALAR
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# GitHub Pages manzilingni shu yerga yozasan
WEBAPP_URL = "https://USERNAME.github.io/REPOSITORY/"

DB_NAME = "uzb_epic.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance REAL DEFAULT 0,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product TEXT,
            amount REAL,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_user(user):
    conn = get_db()

    exists = conn.execute(
        "SELECT id FROM users WHERE id = ?",
        (user.id,)
    ).fetchone()

    if not exists:
        conn.execute(
            """
            INSERT INTO users
            (id, username, first_name, balance, created_at)
            VALUES (?, ?, ?, 0, ?)
            """,
            (
                user.id,
                user.username or "",
                user.first_name or "",
                datetime.now().isoformat()
            )
        )
    else:
        conn.execute(
            """
            UPDATE users
            SET username = ?, first_name = ?
            WHERE id = ?
            """,
            (
                user.username or "",
                user.first_name or "",
                user.id
            )
        )

    conn.commit()
    conn.close()


# =========================================================
# ASOSIY MENYU
# =========================================================

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🚀 UZB EPIC",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ],
        [
            InlineKeyboardButton("⭐ Stars", callback_data="stars"),
            InlineKeyboardButton("🎁 Gifts", callback_data="gifts")
        ],
        [
            InlineKeyboardButton("💎 TON", callback_data="ton"),
            InlineKeyboardButton("📦 Buyurtmalarim", callback_data="orders")
        ],
        [
            InlineKeyboardButton("👤 Profil", callback_data="profile"),
            InlineKeyboardButton("❓ Yordam", callback_data="help")
        ]
    ])


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    add_user(user)

    text = (
        "🔥 <b>UZB EPIC</b>\n\n"
        "Telegram Stars, Gifts va TON uchun "
        "premium mini app.\n\n"
        "🚀 Pastdagi tugma orqali UZB EPIC'ni oching."
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


# =========================================================
# CALLBACK
# =========================================================

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "stars":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ 50 Stars", callback_data="buy_50")],
            [InlineKeyboardButton("⭐ 100 Stars", callback_data="buy_100")],
            [InlineKeyboardButton("⭐ 250 Stars", callback_data="buy_250")],
            [InlineKeyboardButton("⭐ 500 Stars", callback_data="buy_500")],
            [InlineKeyboardButton("⭐ 1000 Stars", callback_data="buy_1000")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
        ])

        await query.edit_message_text(
            "⭐ <b>Stars</b>\n\n"
            "Kerakli paketni tanlang:",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    elif query.data == "gifts":
        await query.edit_message_text(
            "🎁 <b>Gifts</b>\n\n"
            "Bu bo‘lim tez orada ishlaydi.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
            ])
        )

    elif query.data == "ton":
        await query.edit_message_text(
            "💎 <b>TON</b>\n\n"
            "TON bo‘limi tez orada ishga tushadi.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
            ])
        )

    elif query.data == "orders":
        conn = get_db()

        orders = conn.execute(
            """
            SELECT id, product, amount, status
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (user_id,)
        ).fetchall()

        conn.close()

        if not orders:
            text = "📦 <b>Buyurtmalarim</b>\n\nSizda hali buyurtmalar yo‘q."
        else:
            text = "📦 <b>Buyurtmalarim</b>\n\n"

            for order in orders:
                text += (
                    f"#{order['id']} — {order['product']}\n"
                    f"💰 {order['amount']}\n"
                    f"📌 {order['status']}\n\n"
                )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
            ])
        )

    elif query.data == "profile":
        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        conn.close()

        if user:
            text = (
                "👤 <b>Profil</b>\n\n"
                f"🆔 ID: <code>{user['id']}</code>\n"
                f"👤 Ism: {user['first_name'] or '-'}\n"
                f"⭐ Balans: {user['balance']}\n"
            )
        else:
            text = "Profil topilmadi."

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
            ])
        )

    elif query.data == "help":
        await query.edit_message_text(
            "❓ <b>Yordam</b>\n\n"
            "🚀 UZB EPIC — Telegram Mini App.\n\n"
            "Muammo bo‘lsa administratorga murojaat qiling.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
            ])
        )

    elif query.data.startswith("buy_"):
        amount = query.data.replace("buy_", "")

        conn = get_db()

        conn.execute(
            """
            INSERT INTO orders
            (user_id, product, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                f"{amount} Stars",
                0,
                "pending",
                datetime.now().isoformat()
            )
        )

        conn.commit()
        conn.close()

        await query.edit_message_text(
            f"⭐ <b>{amount} Stars</b>\n\n"
            "Buyurtmangiz qabul qilindi.\n"
            "📌 Holat: pending",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
            ])
        )

    elif query.data == "back":
        await query.edit_message_text(
            "🔥 <b>UZB EPIC</b>\n\n"
            "Kerakli bo‘limni tanlang:",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )


# =========================================================
# ADMIN
# =========================================================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    conn = get_db()

    users = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    orders = conn.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    conn.close()

    await update.message.reply_text(
        "👑 <b>ADMIN PANEL</b>\n\n"
        f"👥 Users: <b>{users}</b>\n"
        f"📦 Orders: <b>{orders}</b>",
        parse_mode="HTML"
    )


# =========================================================
# WEB APP DATA
# =========================================================

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.effective_message.web_app_data.data

    logging.info(
        "WebApp data: %s",
        data
    )


# =========================================================
# MAIN
# =========================================================

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi!")

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))

    app.add_handler(
        CallbackQueryHandler(callbacks)
    )

    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.WEB_APP_DATA,
            web_app_data
        )
    )

    print("UZB EPIC BOT ishga tushdi...")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
