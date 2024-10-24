from pyrogram import Client, filters
from info import CHANNELS
from database.ia_filterdb import save_file

# Define a combined media filter for documents, videos, and audios
media_filter = filters.document | filters.video | filters.audio

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    """Media Handler to save media files from specified channels."""
    # Attempt to get the first available media type
    media = None
    file_type = None

    for ft in ("document", "video", "audio"):
        media = getattr(message, ft, None)
        if media is not None:
            file_type = ft
            break

    if media is None:
        return  # Exit if no media is found

    media.file_type = file_type
    media.caption = message.caption

    # Try saving the media to the database
    try:
        await save_file(media, message.chat.id, message.id)
    except Exception as e:
        logger.error(f"Error saving file: {e}")  # Use logging for better traceability
