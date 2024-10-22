import os
from pyrogram import Client, filters, enums
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from info import IMDB_TEMPLATE, BOT_TOKEN
from utils import extract_user, get_file_id, get_poster, last_online
import time
from datetime import datetime
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
import io 
from pyrogram.types import Message
from pyrogram import enums


@Client.on_message(filters.command(["setname"]))
async def who_is(bot, message):
    sourse_message = message.reply_to_message
    title = sourse_message.text 
    await bot.set_chat_title(message.chat.id, title=title)


@Client.on_message(filters.command(["setbio"]))
async def set_chat_description(bot, message):
    sourse_message = message.reply_to_message
    description = sourse_message.text 
    await bot.set_chat_description(message.chat.id, description=description)


@Client.on_message(filters.command(["poll"]))
async def who_is(bot, message):
    
    content = message.reply_to_message.text
    chat_id = message.chat.id
    await bot.send_poll(chat_id, f"{content}", ["Yes", "No", "Maybe"])
    



from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from script import RULE_TXT  # Make sure to import RULE_TXT from your script

START_MESSAGE = "Welcome {}, here are the rules for the group {}."
PROTECT_CONTENT = True  # Set this flag based on your needs

@Client.on_message(filters.command("rules") & filters.group)
async def r_message(client, message):
    protect = "/pbatch" if PROTECT_CONTENT else "batch"
    mention = message.from_user.mention

    # Define buttons
    buttons = [
        [
            InlineKeyboardButton('Rules', callback_data='show_rules')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    try:
        await message.reply_text(
            START_MESSAGE.format(mention, message.chat.title),
            protect_content=PROTECT_CONTENT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        print(f"Error sending rules message: {e}")

@Client.on_callback_query(filters.regex('show_rules'))
async def show_rules(client, callback_query):
    await callback_query.answer()  # Acknowledge the callback
    await callback_query.message.reply_text(RULE_TXT, parse_mode=enums.ParseMode.HTML)
