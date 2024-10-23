from pyrogram import Client, filters
from info import CHANNELS
from database.ia_filterdb import save_file

# Filter for media types (documents, videos, and audios)
media_filter = filters.document | filters.video | filters.audio

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    """Media Handler to capture documents, videos, and audio from specific channels"""
    
    for file_type in ("document", "video", "audio"):
        media = getattr(message, file_type, None)
        if media is not None:
            break
    else:
        return  # Exit if no media is found
    
    media.file_type = file_type
    media.caption = message.caption
    
    try:
        # Asynchronous call to save the media file
        await save_file(media, message.chat.id, message.id)
    except Exception as e:
        print(e)  # Log the error if saving fails
