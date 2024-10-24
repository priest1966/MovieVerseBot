import logging
import re
import base64
from struct import pack
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import (
    DATABASE_URI,
    DATABASE_NAME,
    COLLECTION_NAME,
    USE_CAPTION_FILTER,
    MAX_B_TN,
)
from utils import get_settings, save_group_settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize the MongoDB client and database instance
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

@instance.register
class Media(Document):
    """Media Document Schema"""
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    channel_id = fields.IntField(allow_none=True)
    message_id = fields.IntField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', 'channel_id', 'message_id')
        collection_name = COLLECTION_NAME


async def save_file(media, channel_id=None, message_id=None):
    """Save media file information to the database."""
    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"[_\-\.\+]", " ", str(media.file_name)).strip()

    try:
        media_document = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            channel_id=channel_id,
            message_id=message_id,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
        )
        await media_document.commit()
        logger.info(f'Successfully saved file: {file_name}')
        return True, 1  # Success
    except ValidationError as ve:
        logger.error('Validation error occurred while saving file: %s', ve)
        return False, 2  # Validation Error
    except DuplicateKeyError:
        logger.warning('File already exists: %s', media.file_name)
        return False, 0  # Duplicate Entry


async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0):
    """Return search results based on the query."""
    settings = await get_settings(int(chat_id)) if chat_id else {}
    max_results = 10 if settings.get('max_btn') else int(MAX_B_TN)

    query = query.strip()
    raw_pattern = build_search_pattern(query)
    regex = re.compile(raw_pattern, flags=re.IGNORECASE)

    filter_query = {'file_name': regex}
    if USE_CAPTION_FILTER:
        filter_query['$or'] = [{'file_name': regex}, {'caption': regex}]
    if file_type:
        filter_query['file_type'] = file_type

    try:
        total_results = await Media.count_documents(filter_query)
        next_offset = min(offset + max_results, total_results)

        cursor = Media.find(filter_query).sort('$natural', -1).skip(offset).limit(max_results)
        files = await cursor.to_list(length=max_results)

        return files, next_offset if next_offset < total_results else '', total_results
    except Exception as e:
        logger.error('Error during search: %s', e)
        return [], '', 0


async def get_bad_files(query, file_type=None):
    """Retrieve files marked as bad based on a query."""
    query = query.strip()
    raw_pattern = build_search_pattern(query)
    regex = re.compile(raw_pattern, flags=re.IGNORECASE)

    filter_query = {'file_name': regex}
    if USE_CAPTION_FILTER:
        filter_query['$or'] = [{'file_name': regex}, {'caption': regex}]
    if file_type:
        filter_query['file_type'] = file_type

    try:
        total_results = await Media.count_documents(filter_query)
        cursor = Media.find(filter_query).sort('$natural', -1)
        files = await cursor.to_list(length=total_results)

        return files, total_results
    except Exception as e:
        logger.error('Error fetching bad files: %s', e)
        return [], 0


async def get_file_details(file_id):
    """Retrieve detailed information about a file."""
    filter_query = {'file_id': file_id}
    cursor = Media.find(filter_query)

    try:
        file_details = await cursor.to_list(length=1)
        return file_details
    except Exception as e:
        logger.error('Error fetching file details: %s', e)
        return []


def build_search_pattern(query):
    """Build a regex pattern for searching."""
    if not query:
        return r'.'
    elif ' ' not in query:
        return r'(\b|[\.\+\-_])' + re.escape(query) + r'(\b|[\.\+\-_])'
    else:
        return re.escape(query).replace(' ', r'.*[\s\.\+\-_]')


def encode_file_id(s: bytes) -> str:
    """Encode a file ID into a URL-safe format."""
    encoded = bytearray()
    zero_count = 0

    for byte in s + bytes([22]) + bytes([4]):
        if byte == 0:
            zero_count += 1
        else:
            if zero_count:
                encoded.append(0)
                encoded.append(zero_count)
                zero_count = 0
            encoded.append(byte)

    return base64.urlsafe_b64encode(encoded).decode().rstrip("=")


def encode_file_ref(file_ref: bytes) -> str:
    """Encode a file reference into a URL-safe format."""
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")


def unpack_new_file_id(new_file_id):
    """Unpack the new file ID into file_id and file_ref."""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref
