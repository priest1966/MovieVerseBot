from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import re


mongo_url_pattern = re.compile(r'mongodb(?:\+srv)?:\/\/[^\s]+')


@Client.on_message(filters.command("mongo"))
async def mongo_command(client, message: Message):
    if len(message.command) < 2:
        await message.reply("Please enter your MongoDB URL after the command. Example: /mongo your_mongodb_url")
        return

    mongo_url = message.command[1]
    if re.match(mongo_url_pattern, mongo_url):
        try:
            # Attempt to connect to the MongoDB instance
            client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
            client.server_info()  # Will cause an exception if connection fails
            await message.reply("MongoDB Url is valid and connection successful")
        except Exception as e:
            await message.reply(f"Failed to connect to MongoDB: {e}")
    else:
        await message.reply("Invalid MongoDB URL format")
