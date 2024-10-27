from info import ADMINS
from Script import script
from time import time, sleep
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden
from pyrogram.errors.exceptions.bad_request_400 import ChatAdminRequired, UserAdminInvalid


def send_and_delete_message(client, chat_id, text, delay=20):
    """Helper function to send a message and delete it after a delay."""
    sent_message = client.send_message(chat_id, text)
    sleep(delay)
    sent_message.delete()


def kick_member(client, chat_id, user_id, kick_duration=45):
    """Helper function to kick a member with error handling."""
    try:
        client.kick_chat_member(chat_id, user_id, int(time() + kick_duration))
        sleep(1)
        return True
    except (ChatAdminRequired, UserAdminInvalid):
        return "admin_required"
    except FloodWait as e:
        sleep(e.x)
        return False


@Client.on_message(filters.incoming & ~filters.private & filters.command('inkick'))
def inkick(client, message):
    user = client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status == "creator":
        if len(message.command) > 1:
            input_str = message.command[1:]
            sent_message = message.reply_text(script.START_KICK)
            sleep(20)
            sent_message.delete()
            message.delete()
            
            count = 0
            for member in client.iter_chat_members(message.chat.id):
                if member.user.status in input_str and member.status not in ('administrator', 'creator'):
                    result = kick_member(client, message.chat.id, member.user.id)
                    if result == "admin_required":
                        sent_message.edit(script.ADMIN_REQUIRED)
                        client.leave_chat(message.chat.id)
                        break
                    count += 1 if result else 0
            try:
                sent_message.edit(script.KICKED.format(count))
            except ChatWriteForbidden:
                pass
        else:
            message.reply_text(script.INPUT_REQUIRED)
    else:
        send_and_delete_message(client, message.chat.id, script.CREATOR_REQUIRED, delay=5)


@Client.on_message(filters.incoming & ~filters.private & filters.command('dkick'))
def dkick(client, message):
    user = client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status == "creator":
        sent_message = message.reply_text(script.START_KICK)
        sleep(20)
        sent_message.delete()
        message.delete()
        
        count = 0
        for member in client.iter_chat_members(message.chat.id):
            if member.user.is_deleted and member.status not in ('administrator', 'creator'):
                result = kick_member(client, message.chat.id, member.user.id)
                if result == "admin_required":
                    sent_message.edit(script.ADMIN_REQUIRED)
                    client.leave_chat(message.chat.id)
                    break
                count += 1 if result else 0
        try:
            sent_message.edit(script.DKICK.format(count))
        except ChatWriteForbidden:
            pass
    else:
        send_and_delete_message(client, message.chat.id, script.CREATOR_REQUIRED, delay=5)


@Client.on_message(filters.incoming & ~filters.private & filters.command('instatus'))
def instatus(client, message):
    user = client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status in ('administrator', 'creator') or user.user.id in ADMINS:
        sent_message = message.reply_text(script.FETCHING_INFO)
        
        recently = within_week = within_month = long_time_ago = deleted_acc = uncached = bot = 0
        for member in client.iter_chat_members(message.chat.id):
            user = member.user
            if user.is_deleted:
                deleted_acc += 1
            elif user.is_bot:
                bot += 1
            elif user.status == "recently":
                recently += 1
            elif user.status == "within_week":
                within_week += 1
            elif user.status == "within_month":
                within_month += 1
            elif user.status == "long_time_ago":
                long_time_ago += 1
            else:
                uncached += 1
        sent_message.edit(script.STATUS.format(
            message.chat.title, recently, within_week, within_month, long_time_ago, deleted_acc, bot, uncached
        ))
    else:
        send_and_delete_message(client, message.chat.id, script.CREATOR_REQUIRED, delay=5)
