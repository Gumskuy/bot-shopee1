import json
import csv
import os
from datetime import datetime
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Update
)
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = "8633274639:AAHnVWmIJzNwjZILM7rpsuAaaC9NFmE_42Y"
LOG_FILE = "logs.csv"
ADMIN_USERNAME = "szavvvv"  # tanpa @


# ===== LOAD DATA =====
with open("data.json", "r", encoding="utf-8") as f:
    config = json.load(f)


# ===== LOG FUNCTION =====
def log_activity(user, action):
    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["user_id", "username", "first_name", "action", "timestamp"])

        writer.writerow([
            user.id,
            user.username,
            user.first_name,
            action,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])


# ===== SHOW CATALOG =====
async def show_catalog(update_or_query, edit=False):

    keyboard = []
    for product in config["products"]:
        keyboard.append([
            InlineKeyboardButton(
                product["name"],
                callback_data=f"product_{product['id']}"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if edit:
        try:
            with open(config["banner"], "rb") as photo:
                media = InputMediaPhoto(
                    media=photo,
                    caption=config["welcome_text"]
                )
                await update_or_query.message.edit_media(
                    media=media,
                    reply_markup=reply_markup
                )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    else:
        with open(config["banner"], "rb") as photo:
            await update_or_query.message.reply_photo(
                photo=photo,
                caption=config["welcome_text"],
                reply_markup=reply_markup
            )


# ===== /START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_activity(update.effective_user, "start")
    await show_catalog(update)


# ===== AUTO PRICE LIST DI GROUP =====
async def auto_pricelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.text:
        return

    # Jangan balas pesan dari bot
    if message.from_user.is_bot:
        return

    text = message.text.lower()

    if "pricelist" in text:
        await show_catalog(update)


# ===== BUTTON HANDLER =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    # ===== VIEW PRODUCT =====
    if data.startswith("product_"):
        product_id = data.split("_")[1]

        product = next(
            (p for p in config["products"] if p["id"] == product_id),
            None
        )

        if not product:
            return

        caption = (
            f"🛍 {product['name']}\n\n"
            f"{product['description']}\n\n"
            f"💰 Harga: {product['price']}"
        )

        keyboard = [
            [InlineKeyboardButton("🛒 Beli di Shopee", callback_data=f"buy_{product_id}")],
            [InlineKeyboardButton(
                "💬 Tanya via Telegram",
                url=f"https://t.me/{ADMIN_USERNAME}?text=Halo%20saya%20tertarik%20dengan%20{product['name']}"
            )],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="back")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            with open(product["photo"], "rb") as photo:
                media = InputMediaPhoto(
                    media=photo,
                    caption=caption
                )
                await query.message.edit_media(
                    media=media,
                    reply_markup=reply_markup
                )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise

    # ===== BUY BUTTON (LOGGED) =====
    elif data.startswith("buy_"):
        product_id = data.split("_")[1]

        log_activity(user, f"klik_beli_{product_id}")

        product = next(
            (p for p in config["products"] if p["id"] == product_id),
            None
        )

        if product:
            await query.message.reply_text(product["link"])

    # ===== BACK BUTTON =====
    elif data == "back":
        await show_catalog(query, edit=True)


# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # handler grup
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), auto_pricelist))

    print("Bot berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()