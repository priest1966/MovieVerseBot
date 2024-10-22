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



@Client.on_message(filters.command(["setname"]))
async def who_is(bot, message):
    source_message = message.reply_to_message
    if source_message and source_message.text:
        title = source_message.text
        try:
            await bot.set_chat_title(message.chat.id, title=title)
        except Exception as e:
            await message.reply_text(f"Error: {str(e)}")

@Client.on_message(filters.command(["setbio"]))
async def set_chat_description(bot, message):
    source_message = message.reply_to_message
    if source_message and source_message.text:
        description = source_message.text
        try:
            await bot.set_chat_description(message.chat.id, description=description)
        except Exception as e:
            await message.reply_text(f"Error: {str(e)}")

@Client.on_message(filters.command(["poll"]))
async def who_is(bot, message):
    content = message.reply_to_message.text
    chat_id = message.chat.id
    await bot.send_poll(chat_id, f"{content}", ["Yes", "No", "Maybe"])

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

RULE_TXT = """Group Rules

◈ <b>Sᴇᴀʀᴄʜ Mᴏᴠɪᴇ Wɪᴛʜ Cᴏʀʀᴇᴄᴛ Sᴘᴇʟʟɪɴɢ:</b>
• ᴀᴠᴀᴛᴀʀ  
• ᴀᴠᴀᴛᴀʀ 𝟸𝟶𝟶𝟿
• ᴀᴠᴀᴛᴀʀ ʜɪɴᴅɪ
• ᴀᴠᴀᴛᴀʀ ʜɪɴᴅɪ ᴅᴜʙʙᴇᴅ

◈ <b>Sᴇᴀʀᴄʜ Wᴇʙ Sᴇʀɪᴇs Iɴ ᴛʜɪs Fᴏʀᴍᴀᴛ:</b>
• ᴠɪᴋɪɴɢs
• ᴠɪᴋɪɴɢs S𝟶𝟷
• ᴠɪᴋɪɴɢs S𝟶𝟷E𝟶𝟷
• ᴠɪᴋɪɴɢs S𝟶𝟷 ʜɪɴᴅɪ
• ᴠɪᴋɪɴɢs S𝟶𝟷 ʜɪɴᴅɪ ᴅᴜʙʙᴇᴅ 


<b>1. Only movie topics and related topics are allowed in the group. Non-movie realated conversations are strictly prohibited In the group.
(Please use this group to request a movie according to the rules. Other conversations are not allowed.)

2. Be polite to all members and admins of the group.

3. Porn movies and B Grade Moveis are not posted. Warn or Ban if asked.
(WE do not share pornographic content. Do not ask them.)

4. Unnecessary messages and links that are against the group will be deleted and punished by the admins for no reason.

5. If you do not know the exact spelling of the movie, request it only after looking it up in Google or using the imdb.

6. Mention the request only if no reply is recived within 12 hours after requesting. In the meanwhile Warn will give it if it keeps re-mentioning.

7. Movie song, trailers, reviews, collection reports, mobile applications, games, etc, are not shared with the group, None of the content posted on this page is our own.

8. Or if you think we are using your content, contact the admin and the content will be removed. Once the reply message is asked again the mute will be muted.

9. No spamming, self-promotion, or advertising is allowed in the group.



Note : We not fulfill movie request in Assamese, Bengali, Bodo, Dogri, Gujarati, Kannada, Kashmiri, Konkani, Maithili, Malayalam, Manipuri, Marathi, Nepali, Odia, Punjabi, Sanskrit, Santali, Sindhi, Tamil, Telugu, and Urdu language. So don't request.

➙ ᴅᴏɴ'ᴛ ʀᴇǫᴜᴇꜱᴛ ᴀɴʏ ᴛʜɪɴɢꜱ ᴏᴛʜᴇʀ ᴛʜᴀɴ ᴍᴏᴠɪᴇꜱ, ꜱᴇʀɪᴇꜱ, ᴀɴɪᴍᴀᴛɪᴏɴ, ᴄᴀʀᴛᴏᴏɴ, ᴀɴɪᴍᴇ, ᴋ-ᴅʀᴀᴍᴀ ᴍᴀɴʏ ᴍᴏʀᴇ.</b>

<b>Nᴏᴛᴇ :</b> ᴀʟʟ ᴍᴇꜱꜱᴀɢᴇꜱ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇᴅ ᴀꜰᴛᴇʀ 𝟷𝟶 ᴍɪɴᴜᴛᴇꜱ ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ."""