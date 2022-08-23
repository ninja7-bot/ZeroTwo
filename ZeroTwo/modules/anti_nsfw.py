import os
from os import remove

from pyrogram import filters
from pyrogram.types import Message

from ZeroTwo.modules.helper_funcs.telethn.chatstatus import (
    can_delete_messages)

from ZeroTwo.utils.permissions import adminsOnly

from ZeroTwo import arq, ZeroTwoTelethonClient as zbot
from ZeroTwo.ex_plugins.dbfunctions import (disable_nsfw, disable_spam, enable_nsfw,
                          enable_spam, is_nsfw_enabled,
                          is_spam_enabled)
from ZeroTwo.modules.helper_funcs.chat_status import user_not_admin
from telegram.ext import CallbackContext

from ZeroTwo.FastTelethon import download_file
import mimetypes

__mod_name__ = "Anti-NSFW"

__HELP__ = """
/antinsfw [on|off] - Enable or disable NSFW Detection.
/anti_spam [on|off] - Enable or disable Spam Detection.
/nsfwscan - Classify a media.
/spamscan - Get Spam predictions of replied message.
"""

def get_file_id(message):
    if message.document:
        if int(message.document.file_size) > 3145728:
            return
        mime_type = message.document.mime_type
        if mime_type != "image/png" and mime_type != "image/jpeg":
            return
        return message.document.file_id

    if message.sticker:
        if message.sticker.is_animated:
            if not message.sticker.thumbs:
                return
            return message.sticker.thumbs[0].file_id
        return message.sticker.file_id

    if message.photo:
        return message.photo.file_id

    if message.animation:
        if not message.animation.thumbs:
            return
        return message.animation.thumbs[0].file_id

    if message.video:
        if not message.video.thumbs:
            return
        return message.video.thumbs[0].file_id

def get_file_unique_id(message):
    m = message
    m = m.sticker or m.video or m.document or m.animation or m.photo
    if not m:
        return
    return m.file_unique_id

    
@adminsOnly("can_change_info")
@zbot.on_message(
    filters.command("antinsfw") & ~filters.private, group=3
)
async def nsfw_toggle_func(_, message: Message):
    chat_id = message.chat.id
    
    if len(message.command) != 2:
        if is_nsfw_enabled(chat_id):
            return await message.reply("Already enabled.")
        enable_nsfw(chat_id)

    status = message.text.split(None, 1)[1].strip()
    status = status.lower()   
    if status == "enable" or "on":
        await message.reply_text("Enabled NSFW Detection.")
    elif status == "disable" or "off":
        if not is_nsfw_enabled(chat_id):
            return await message.reply("Already disabled.")
        disable_nsfw(chat_id)
        await message.reply_text("Disabled NSFW Detection.")
    else:
        await message.reply_text(
            "Unknown Suffix, Use /antinsfw [on|off]"
        )

@adminsOnly("can_change_info")
@zbot.on_message(
    filters.command("anti_spam") & ~filters.private, group=3
)
async def spam_toggle_func(_, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "Usage: /anti_spam [on|off]"
        )
    status = message.text.split(None, 1)[1].strip()
    status = status.lower()
    chat_id = message.chat.id
    if status == "enable" or "on":
        if is_spam_enabled(chat_id):
            return await message.reply("Already enabled.")
        enable_spam(chat_id)
        await message.reply_text("Enabled Spam Detection.")
    elif status == "disable" or "off":
        if not is_spam_enabled(chat_id):
            return await message.reply("Already disabled.")
        disable_spam(chat_id)
        await message.reply_text("Disabled Spam Detection.")
    else:
        await message.reply_text(
            "Unknown Suffix, Use /anti_spam [on|off]"
        )



@zbot.on_message(
    (
        filters.document
        | filters.photo
        | filters.sticker
        | filters.animation
        | filters.video
        | filters.text
    )
)
async def nsfw_watcher(_, message: Message):
    if not await is_nsfw_enabled(message.chat.id):
        return
    if not message.from_user:
        return

    file_id = get_file_id(message)
    file_unique_id = get_file_unique_id(message)
    if file_id and file_unique_id:
        file = zbot.download_media(file_id)  
        try:
            resp = await arq.nsfw_scan(file=file)
        except Exception:
            try:
                return os.remove(file)
            except Exception:
                return
        os.remove(file)
        result = resp.result
        nsfw = result.is_nsfw
        if not nsfw:
            return
        try:
            if can_delete_messages:
                await message.delete()
            else:
                await message.reply_text("Delete Permissions not granted.")
        except Exception:
            return
        await message.reply_text(
            f""" 
**NSFW Image Detected & Deleted Successfully!**
**User:** {message.from_user.mention} [`{message.from_user.id}`]
**Safe:** `{result.neutral} %`
**Porn:** `{result.porn} %`
**Adult:** `{result.sexy} %`
**Hentai:** `{result.hentai} %`
**Drawings:** `{result.drawings} %`

Avoid sending NSFW messages.
""")
    

async def spam_detect(_, message):
    if not is_spam_enabled(message.chat.id):
        return
    text = message.text or message.caption
    if not text:
        return
    resp = await arq.nlp(text)
    result = resp.result[0]
    if not result.is_spam:
        return
    try:
        if can_delete_messages:
            await message.delete()
        else:
            await message.reply_text("Delete Permissions not granted/")
    except Exception:
        return
    await message.reply_text(
        f"""
**Spam Message was detected and deleted!**
**Spam Probability:** {result.spam_probability} %
__Message has been deleted__
""")



@zbot.on_message(filters.command("nsfwscan"), group=3)
async def nsfw_scan_command(_, message: Message):
    err = "Reply to an image/document/sticker/animation to scan it."
    if not message.reply_to_message:
        await message.reply_text(err)
        return
    reply = message.reply_to_message
    if (
        not reply.document
        and not reply.photo
        and not reply.sticker
        and not reply.animation
        and not reply.video
    ):
        await message.reply_text(err)
        return
    m = await message.reply_text("Scanning")
    file_id = get_file_id(reply)
    if not file_id:
        return await m.edit("Something went wrong.")
    file= await download_file(client=zbot,location=message, out="..NSFW/")       
    try:
        results = await arq.nsfw_scan(file=file)
    except Exception as e:
        return await m.edit(str(e))
    remove(file)
    if not results.ok:
        return await m.edit(results.result)
    results = results.result
    await m.edit(
        f"""
**Neutral:** `{results.neutral} %`
**Porn:** `{results.porn} %`
**Hentai:** `{results.hentai} %`
**Sexy:** `{results.sexy} %`
**Drawings:** `{results.drawings} %`
**NSFW:** `{results.is_nsfw}`
"""
    )


@zbot.on_message(filters.command("spamscan"), group=3)
async def scanNLP(_, message: Message):
    if not message.reply_to_message:
        return await message.reply("Reply to a message to scan it.")
    r = message.reply_to_message
    text = r.text or r.caption
    if not text:
        return await message.reply("Can't scan that")
    data = await arq.nlp(text)
    data = data.result[0]
    msg = f"""
**Is Spam:** {data.is_spam}
**Spam Probability:** {data.spam_probability} %
**Spam:** {data.spam}
**Ham:** {data.ham}
**Profanity:** {data.profanity}
"""
    await message.reply(msg, quote=True)
    
