from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from info import AUTH_GROUPS  # Import AUTH_GROUPS from info.py
import time

settings = {
    "welcome_enabled": False,
    "goodbye_enabled": False,
    "welcome_message": "Welcome to the group!",
    "goodbye_message": "Goodbye, {fullname}!",
    "clean_welcome": False,
    "old_welcome_message_id": None,
}

def format_message(text, user, chat):
    text = text.replace("{first}", user.first_name or "")
    text = text.replace("{last}", user.last_name or "")
    text = text.replace("{fullname}", f"{user.first_name or ''} {user.last_name or ''}".strip())
    text = text.replace("{username}", f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})")
    text = text.replace("{mention}", f"[{user.first_name}](tg://user?id={user.id})")
    text = text.replace("{id}", str(user.id))
    text = text.replace("{chatname}", chat.title if chat else "")
    
    if "{rules}" in text:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Rules", url="https://example.com/rules")]])
    else:
        keyboard = None
    
    disable_notification = "{nonotif}" in text
    protect_content = "{protect}" in text
    disable_web_page_preview = "{preview}" not in text and "{preview:top}" not in text
    
    text = text.replace("{rules}", "").replace("{nonotif}", "").replace("{protect}", "")
    text = text.replace("{preview}", "").replace("{preview:top}", "")

    return text, keyboard, disable_notification, protect_content, disable_web_page_preview


@Client.on_message(filters.group & filters.command(["setwelcome", "setgoodbye", "resetwelcome", "resetgoodbye",
                                                    "welcome", "goodbye", "cleanwelcome"]))
def handle_welcome_goodbye(client, message):
    global settings

    if message.chat.id not in AUTH_GROUPS:
        return  # Ignore messages outside AUTH_GROUPS

    command = message.command[0].lower()

    if command in ["welcome", "goodbye", "cleanwelcome"]:
        action = message.command[1].lower() if len(message.command) > 1 else None
        if action in ["yes", "on"]:
            settings[f"{command}_enabled"] = True
            message.reply_text(f"{command.capitalize()} messages enabled.")
        elif action in ["no", "off"]:
            settings[f"{command}_enabled"] = False
            message.reply_text(f"{command.capitalize()} messages disabled.")
        else:
            message.reply_text("Please specify 'yes', 'no', 'on', or 'off'.")
        return

    elif command == "setwelcome":
        settings["welcome_message"] = message.text.split(" ", 1)[1] if len(message.command) > 1 else "Welcome to the group!"
        message.reply_text("New welcome message set!")

    elif command == "setgoodbye":
        settings["goodbye_message"] = message.text.split(" ", 1)[1] if len(message.command) > 1 else "Goodbye!"
        message.reply_text("New goodbye message set!")

    elif command == "resetwelcome":
        settings["welcome_message"] = "Welcome to the group!"
        message.reply_text("Welcome message reset to default.")

    elif command == "resetgoodbye":
        settings["goodbye_message"] = "Goodbye, {fullname}!"
        message.reply_text("Goodbye message reset to default.")


@Client.on_message(filters.group & filters.new_chat_members)
def welcome_message(client, message):
    global settings

    if message.chat.id not in AUTH_GROUPS or not settings["welcome_enabled"]:
        return  # Ignore if not in AUTH_GROUPS or welcome is disabled

    user = message.from_user
    chat = message.chat
    welcome_text, keyboard, disable_notification, protect_content, disable_web_page_preview = format_message(settings["welcome_message"], user, chat)

    sent_message = message.reply_text(
        welcome_text,
        reply_markup=keyboard,
        disable_notification=disable_notification,
        protect_content=protect_content,
        disable_web_page_preview=disable_web_page_preview
    )

    if settings["clean_welcome"]:
        if settings["old_welcome_message_id"]:
            try:
                client.delete_messages(message.chat.id, settings["old_welcome_message_id"])
            except:
                pass
        settings["old_welcome_message_id"] = sent_message.message_id
        time.sleep(300)
        client.delete_messages(message.chat.id, sent_message.message_id)


@Client.on_message(filters.group & filters.left_chat_member)
def goodbye_message(client, message):
    global settings

    if message.chat.id not in AUTH_GROUPS or not settings["goodbye_enabled"]:
        return  # Ignore if not in AUTH_GROUPS or goodbye is disabled

    user = message.left_chat_member
    chat = message.chat
    goodbye_text, keyboard, disable_notification, protect_content, disable_web_page_preview = format_message(settings["goodbye_message"], user, chat)

    message.reply_text(
        goodbye_text,
        reply_markup=keyboard,
        disable_notification=disable_notification,
        protect_content=protect_content,
        disable_web_page_preview=disable_web_page_preview
    )
