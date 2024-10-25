import logging
import asyncio
import re
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import (
    ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
)
from info import ADMINS, INDEX_REQ_CHANNEL as LOG_CHANNEL
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import temp

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()

import time

@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    try:
        # Unpack data, where the start message ID is passed as part of the query data
        _, action, chat, lst_msg_id, from_user, start_msg_id = query.data.split("#")
        start_msg_id = int(start_msg_id)

        if action == 'reject':
            await query.message.delete()
            await bot.send_message(
                int(from_user),
                f'Your submission for indexing {chat} has been declined by our moderators.',
                reply_to_message_id=int(lst_msg_id)
            )
            return

        if lock.locked():
            return await query.answer('Wait until the previous process completes.', show_alert=True)

        msg = query.message
        await query.answer('Processing...', show_alert=True)

        # Notify user if they are not an admin
        if int(from_user) not in ADMINS:
            await bot.send_message(
                int(from_user),
                f'Your submission for indexing {chat} has been accepted by our moderators and will be added soon.',
                reply_to_message_id=int(lst_msg_id)
            )

        await msg.edit(
            f"Starting Indexing from message ID {start_msg_id}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Cancel', callback_data='index_cancel')]])
        )

        # Variables for progress calculation
        start_time = time.time()
        processed_count = 0
        total_messages = 0

        # Loop through all messages starting from `start_msg_id`
        async for message in bot.iter_history(chat, offset_id=start_msg_id - 1):
            if temp.CANCEL:
                await msg.edit("Indexing cancelled.")
                temp.CANCEL = False
                return

            await index_files_to_db(message.message_id, chat, msg, bot)
            processed_count += 1
            total_messages = message.message_id - start_msg_id + 1  # Calculate total messages from start to current

            # Update progress every 10 messages
            if processed_count % 10 == 0:
                # Calculate elapsed time and estimated completion
                elapsed_time = time.time() - start_time
                msg_per_sec = processed_count / elapsed_time
                msg_per_min = msg_per_sec * 60
                msg_per_day = msg_per_min * 60 * 24
                eta = (total_messages - processed_count) / msg_per_sec if msg_per_sec > 0 else 0

                await msg.edit(
                    f"Indexing Progress:\n"
                    f"Current Message ID: {message.message_id}\n"
                    f"Progress: {processed_count}/{total_messages} messages\n"
                    f"Speed: {msg_per_min:.2f} msg/min, {msg_per_day:.2f} msg/day\n"
                    f"ETA: {int(eta)} seconds"
                )

        await msg.edit(f"Indexing completed from message ID {start_msg_id} to the latest message.")

    except Exception as e:
        logger.error(f"Error in index_files: {e}")
        await query.message.reply(f"An error occurred: {e}")


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    try:
        if ' ' in message.text:
            _, skip = message.text.split(" ")
            try:
                skip = int(skip)
            except ValueError:
                return await message.reply("Skip number should be an integer.")
            await message.reply(f"Successfully set SKIP number to {skip}")
            temp.CURRENT = skip
        else:
            await message.reply("Provide a skip number.")
    except Exception as e:
        logger.error(f"Error in set_skip_number: {e}")
        await message.reply(f"An error occurred: {e}")

async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0

    async with lock:
        try:
            current = temp.CURRENT
            temp.CANCEL = False

            async for message in bot.iter_messages(chat, lst_msg_id, temp.CURRENT):
                if temp.CANCEL:
                    await msg.edit(f"Cancelled!\n\nSaved <code>{total_files}</code> files to the database!\nDuplicate Files: <code>{duplicate}</code>\nDeleted Messages: <code>{deleted}</code>\nNon-Media Messages: <code>{no_media + unsupported}</code> (Unsupported: `{unsupported}`)\nErrors: <code>{errors}</code>")
                    break

                current += 1
                if current % 200 == 0:
                    # Adding 10-second delay after every 100 files
                    await asyncio.sleep(10)

                if current % 200 == 0:
                    await asyncio.sleep(20)
                if current % 20 == 0:
                    can = [[InlineKeyboardButton('Cancel', callback_data='index_cancel')]]
                    reply = InlineKeyboardMarkup(can)
                    await msg.edit_text(
                        f"Total messages fetched: <code>{current}</code>\nTotal messages saved: <code>{total_files}</code>\nDuplicate Files: <code>{duplicate}</code>\nDeleted Messages: <code>{deleted}</code>\nNon-Media: <code>{no_media + unsupported}</code> (Unsupported: `{unsupported}`)\nErrors: <code>{errors}</code>",
                        reply_markup=reply
                    )

                if message.empty:
                    deleted += 1
                    continue
                elif not message.media:
                    no_media += 1
                    continue
                elif message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
                    unsupported += 1
                    continue

                media = getattr(message, message.media.value, None)
                if not media:
                    unsupported += 1
                    continue

                media.file_type = message.media.value
                media.caption = message.caption if message.caption else ''

                try:
                    aynav, vnay = await save_file(media)

                    if aynav:
                        total_files += 1
                    elif vnay == 0:
                        duplicate += 1
                    elif vnay == 2:
                        errors += 1

                except FloodWait as e:
                    logger.warning(f"FloodWait: Sleeping for {e.x} seconds.")
                    await asyncio.sleep(e.x)

        except Exception as e:
            logger.error(f"Error in index_files_to_db: {e}")
            await msg.reply(f"Error while indexing: {e}")
        
        await msg.edit_text(
            f"Completed!\n\nSaved <code>{total_files}</code> files to the database!\nDuplicate Files: <code>{duplicate}</code>\nDeleted Messages: <code>{deleted}</code>\nNon-Media Messages: <code>{no_media + unsupported}</code> (Unsupported: `{unsupported}`)\nErrors: <code>{errors}</code>"
        )
