import os
import logging
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty, MessageTooLong, PeerIdInvalid, ChatAdminRequired
from info import ADMINS, LOG_CHANNEL, SUPPORT_CHAT, MELCOW_NEW_USERS, MELCOW_VID
from database.users_chats_db import db
from database.ia_filterdb import Media
from utils import get_size, temp, get_settings
from Script import script
import asyncio

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

"""----------------------------------------- https://t.me/movieversepremium --------------------------------------"""

@Client.on_message(filters.new_chat_members & filters.group)
async def save_group(bot, message):
    r_j_check = [u.id for u in message.new_chat_members]
    if temp.ME in r_j_check:
        # When the bot itself is added to a new group
        if not await db.get_chat(message.chat.id):
            total = await bot.get_chat_members_count(message.chat.id)
            r_j = message.from_user.mention if message.from_user else "Anonymous"
            await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, r_j))
            await db.add_chat(message.chat.id, message.chat.title)

        if message.chat.id in temp.BANNED_CHATS:
            buttons = [[InlineKeyboardButton('Support', url=SUPPORT_CHAT)]]
            reply_markup = InlineKeyboardMarkup(buttons)
            k = await message.reply(
                text="<b>This chat is banned from using me.</b>",
                reply_markup=reply_markup,
            )

            try:
                await k.pin()
            except Exception as e:
                logger.error(f"Error pinning message: {e}")

            await bot.leave_chat(message.chat.id)
            return

        buttons = [[
            InlineKeyboardButton('Support', url=SUPPORT_CHAT),
            InlineKeyboardButton('Updates', url='https://t.me/movieversepremium')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(
            f"<b>Thank you for adding me to {message.chat.title}.\n"
            "Don't forget to make me an admin.\n"
            "For any help, click the buttons below.</b>",
            reply_markup=reply_markup)
    else:
        settings = await get_settings(message.chat.id)
        if settings.get("welcome"):
            for u in message.new_chat_members:
                # Send welcome message
                if temp.MELCOW.get('welcome') is not None:
                    try:
                        await temp.MELCOW['welcome'].delete()
                    except:
                        pass
                temp.MELCOW['welcome'] = await message.reply_photo(
                    photo=MELCOW_VID,
                    caption=script.MELCOW_ENG.format(u.mention, message.chat.title),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton('• Join My Updates •', url='https://t.me/movieversepremium')]]
                    ),
                    parse_mode=enums.ParseMode.HTML
                )

        if settings.get("auto_delete"):
            await asyncio.sleep(120)
            try:
                await temp.MELCOW['welcome'].delete()
            except Exception as e:
                logger.error(f"Error deleting welcome message: {e}")


@Client.on_message(filters.command('leave') & filters.user(ADMINS))
async def leave_a_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply("Give me a chat id")
    chat = message.command[1]
    try:
        chat = int(chat)
    except ValueError:
        return await message.reply("Invalid chat id")

    try:
        await bot.send_message(
            chat_id=chat,
            text="<b>I am leaving the chat as per admin request. To add me back, contact support.</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Support', url=SUPPORT_CHAT)]])
        )
        await bot.leave_chat(chat)
        await message.reply(f"Left the chat `{chat}` successfully")
    except Exception as e:
        logger.error(f"Error leaving chat: {e}")
        await message.reply(f"Error - {e}")


@Client.on_message(filters.command('disable') & filters.user(ADMINS))
async def disable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply("Give me a chat id")
    
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "No reason provided"
    
    try:
        chat_id = int(chat)
    except ValueError:
        return await message.reply("Give me a valid chat ID")
    
    chat_info = await db.get_chat(chat_id)
    if not chat_info:
        return await message.reply("Chat not found in database")
    
    if chat_info['is_disabled']:
        return await message.reply(f"This chat is already disabled.\nReason: {chat_info['reason']}")
    
    await db.disable_chat(chat_id, reason)
    temp.BANNED_CHATS.append(chat_id)
    await message.reply("Chat successfully disabled")

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=f"<b>This chat has been disabled by admin.</b>\nReason: <code>{reason}</code>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Support', url=SUPPORT_CHAT)]])
        )
        await bot.leave_chat(chat_id)
    except Exception as e:
        logger.error(f"Error disabling chat: {e}")
        await message.reply(f"Error - {e}")


@Client.on_message(filters.command('enable') & filters.user(ADMINS))
async def re_enable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply("Give me a chat id")
    
    chat = message.command[1]
    try:
        chat_id = int(chat)
    except ValueError:
        return await message.reply("Give me a valid chat ID")

    chat_info = await db.get_chat(chat_id)
    if not chat_info:
        return await message.reply("Chat not found in the database")

    if not chat_info.get('is_disabled'):
        return await message.reply("This chat is not disabled")

    await db.re_enable_chat(chat_id)
    temp.BANNED_CHATS.remove(chat_id)
    await message.reply("Chat successfully re-enabled")


@Client.on_message(filters.command('ban') & filters.user(ADMINS))
async def ban_user(bot, message):
    if len(message.command) == 1:
        return await message.reply("Give me a user id or username")

    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        user = message.text.split(None, 2)[1]
    else:
        user = message.command[1]
        reason = "No reason provided"

    try:
        user_info = await bot.get_users(user)
    except PeerIdInvalid:
        return await message.reply("Invalid user id or username")

    ban_status = await db.get_ban_status(user_info.id)
    if ban_status['is_banned']:
        return await message.reply(f"{user_info.mention} is already banned.\nReason: {ban_status['ban_reason']}")

    try:
        await bot.kick_chat_member(message.chat.id, user_info.id)
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        return await message.reply(f"Failed to ban user: {e}")

    await db.ban_user(user_info.id, reason)
    temp.BANNED_USERS.append(user_info.id)
    await message.reply(f"Successfully banned {user_info.mention}.\nReason: {reason}")


@Client.on_message(filters.command('unban') & filters.user(ADMINS))
async def unban_user(bot, message):
    if len(message.command) == 1:
        return await message.reply("Give me a user id or username")

    user = message.command[1]
    try:
        user_info = await bot.get_users(user)
    except PeerIdInvalid:
        return await message.reply("Invalid user id or username")

    ban_status = await db.get_ban_status(user_info.id)
    if not ban_status['is_banned']:
        return await message.reply(f"{user_info.mention} is not banned")

    await db.remove_ban(user_info.id)
    temp.BANNED_USERS.remove(user_info.id)
    await message.reply(f"Successfully unbanned {user_info.mention}")


@Client.on_message(filters.command('stats') & filters.user(ADMINS))
async def get_stats(bot, message):
    r = await message.reply("Fetching stats...")
    total_users = await db.total_users_count()
    total_chats = await db.total_chat_count()
    total_files = await Media.count_documents()
    db_size = await db.get_db_size()
    free_space = 536870912 - db_size  # Example free space calculation
    db_size = get_size(db_size)
    free_space = get_size(free_space)

    await r.edit(f"**Total Users:** {total_users}\n**Total Chats:** {total_chats}\n**Total Files:** {total_files}\n\n**Database Size:** {db_size}\n**Free Space:** {free_space}")
