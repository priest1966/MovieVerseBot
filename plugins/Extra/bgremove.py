import os
import aiohttp
import aiofiles
from aiohttp import ContentTypeError
from pyrogram import Client, filters

def check_filename(file_name):
    """Check if a file already exists and generate a unique filename if it does."""
    if os.path.exists(file_name):
        no = 1
        base, ext = os.path.splitext(file_name)
        while True:
            new_name = f"{base}_{no}{ext}"
            if os.path.exists(new_name):
                no += 1
            else:
                return new_name
    return file_name

async def RemoveBG(input_file_name):
    """Remove the background from the image using the remove.bg API."""
    headers = {"X-API-Key": "5NBZGefoEj5VSmBbubeESTpa"}
    
    async with aiofiles.open(input_file_name, "rb") as file:
        files = {"image_file": await file.read()}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.remove.bg/v1.0/removebg", headers=headers, data=files
            ) as response:
                content_type = response.headers.get("content-type")
                
                if "image" not in content_type:
                    return False, await response.json()

                output_name = check_filename("lucy.png")
                async with aiofiles.open(output_name, "wb") as output_file:
                    await output_file.write(await response.read())
                    
                return True, output_name

@Client.on_message(filters.command("rmbg"))
async def rmbg(bot, message):
    """Handle the /rmbg command to remove the background from an image."""
    rmbg_message = await message.reply("Processing...") 
    replied = message.reply_to_message
    
    if not replied or not replied.photo:
        return await rmbg_message.edit("Reply to a photo to remove its background.")

    photo_path = await bot.download_media(replied)
    
    success, output_file = await RemoveBG(photo_path)
    os.remove(photo_path)  # Clean up the downloaded photo

    if not success:
        error_info = output_file["errors"][0]
        detail = error_info.get("detail", "")
        return await rmbg_message.edit(f"ERROR: {error_info['title']},\n{detail}")

    await message.reply_photo(photo=output_file, caption="Here is your image without background.")
    await message.reply_document(document=output_file)
    await rmbg_message.delete()
    os.remove(output_file)  # Clean up the output file
