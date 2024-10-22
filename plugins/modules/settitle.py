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

# Define your START_MESSAGE and PROTECT_CONTENT somewhere in your code
START_MESSAGE = "Welcome {}, here are the rules for the group {}."
PROTECT_CONTENT = True  # Set this flag based on your needs

@Client.on_message(filters.command("rules") & filters.group)
async def r_message(client, message):
    # Set the protect value based on the PROTECT_CONTENT flag
    protect = "/pbatch" if PROTECT_CONTENT else "batch"
    mention = message.from_user.mention

    # Define the button and reply markup
    buttons = [[
        InlineKeyboardButton('Join Group', url='https://t.me/movieverse_discussion_2')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)

    # Send the message with the rules and join button
    await message.reply_text(
        START_MESSAGE.format(mention, message.chat.title),
        protect_content=True,  # Protects the content of the message if required
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML
    )
