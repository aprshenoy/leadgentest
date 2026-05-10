import re
import logging
from dotenv import load_dotenv
import os

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

CATEGORY, LEAD_TYPE, NAME, MOBILE, INCOME, CONFIRM = range(6)

CATEGORIES = {
    "1": ("Loan", {
        "1": "Personal Loan",
        "2": "Gold Loan",
        "3": "Business Loan",
        "4": "Vehicle Loan",
        "5": "Home Loan",
    }),
    "2": ("Credit Card", {
        "1": "Rewards Card",
        "2": "Cashback Card",
        "3": "Travel Card",
        "4": "Lifetime Free Card",
    }),
    "3": ("Insurance", {
        "1": "Life Insurance",
        "2": "Health Insurance",
        "3": "Motor Insurance",
        "4": "Home Insurance",
    }),
    "4": ("Forex", {
        "1": "Currency Exchange",
        "2": "Forex Card",
        "3": "International Transfer",
        "4": "Travel Insurance",
    }),
}

INCOME_OPTIONS = {
    "1": "Below ₹20,000",
    "2": "₹20k–₹50k",
    "3": "Above ₹50k",
}


def build_menu_text(title: str, options: dict) -> str:
    lines = [title, ""]
    for key, label in options.items():
        lines.append(f"{key}) {label}")
    lines.append("")
    lines.append("Please enter your option:")
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    category_options = {k: v[0] for k, v in CATEGORIES.items()}
    text = (
        "Welcome to Leadgen Bot! 👋\n"
        "\n"
        "We help you capture leads across financial products.\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        + build_menu_text("Please select your lead type:", category_options)
    )
    await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    return CATEGORY


async def category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text.strip()
    if choice not in CATEGORIES:
        category_options = {k: v[0] for k, v in CATEGORIES.items()}
        await update.message.reply_text(
            "❌ Invalid option. " + build_menu_text("Please select your lead type:", category_options)
        )
        return CATEGORY

    cat_name, subtypes = CATEGORIES[choice]
    context.user_data["category"] = cat_name
    context.user_data["subtypes"] = subtypes
    await update.message.reply_text(
        build_menu_text(f"Please select {cat_name} type:", subtypes)
    )
    return LEAD_TYPE


async def lead_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text.strip()
    subtypes = context.user_data.get("subtypes", {})
    if choice not in subtypes:
        await update.message.reply_text(
            "❌ Invalid option. " + build_menu_text(
                f"Please select {context.user_data['category']} type:", subtypes
            )
        )
        return LEAD_TYPE

    context.user_data["lead_type"] = subtypes[choice]
    await update.message.reply_text("Enter customer's full name:")
    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not re.fullmatch(r"[A-Za-z ]{3,}", text):
        await update.message.reply_text(
            "❌ Invalid name. Use letters and spaces only, minimum 3 characters.\n\nEnter customer's full name:"
        )
        return NAME

    context.user_data["name"] = text
    await update.message.reply_text("Enter customer's mobile number:")
    return MOBILE


async def mobile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not re.fullmatch(r"[6-9]\d{9}", text):
        await update.message.reply_text(
            "❌ Invalid number. Must be exactly 10 digits and start with 6, 7, 8, or 9.\n\nEnter customer's mobile number:"
        )
        return MOBILE

    context.user_data["mobile"] = text
    await update.message.reply_text(
        build_menu_text("Please select income range:", INCOME_OPTIONS)
    )
    return INCOME


async def income(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text.strip()
    if choice not in INCOME_OPTIONS:
        await update.message.reply_text(
            "❌ Invalid option. " + build_menu_text("Please select income range:", INCOME_OPTIONS)
        )
        return INCOME

    context.user_data["income"] = INCOME_OPTIONS[choice]
    d = context.user_data
    summary = (
        f"📋 New Lead\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Category  : {d['category']}\n"
        f"Lead Type : {d['lead_type']}\n"
        f"Name      : {d['name']}\n"
        f"Mobile    : {d['mobile']}\n"
        f"Income    : {d['income']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Submit this lead?\n\n"
        f"1) Yes\n"
        f"2) No\n\n"
        f"Please enter your option:"
    )
    await update.message.reply_text(summary)
    return CONFIRM


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text.strip()
    if choice == "1":
        await update.message.reply_text("✅ Lead captured successfully!")
    elif choice == "2":
        await update.message.reply_text("❌ Cancelled. Send /start to begin again.")
    else:
        await update.message.reply_text(
            "❌ Invalid option. Please enter 1 for Yes or 2 for No.\n\n"
            "1) Yes\n2) No\n\nPlease enter your option:"
        )
        return CONFIRM

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Cancelled. Send /start to begin again.")
    return ConversationHandler.END


def main() -> None:
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category)],
            LEAD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, lead_type)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            MOBILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, mobile)],
            INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, income)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    logger.info("Bot started. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
