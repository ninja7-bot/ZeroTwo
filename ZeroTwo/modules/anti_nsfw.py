from os import remove
from ZeroTwo.utils.errors import capture_err
from ZeroTwo.utils.permissions import adminsOnly

from pyrogram import filters
from pyrogram.types import Message

from ZeroTwo import ZeroTwoTelethonClient, arq
from ZeroTwo.ex_plugins.dbfunctions import (enable_nsfw, disable_nsfw, enable_spam, disable_spam, is_spam_enabled, is_nsfw_enabled)
from ZeroTwo.utils.arqapi import SUDOERS, arq
from ZeroTwo import @adminsOnly, capture_err


async def get_file_id_from_message(message):
    file_id = None
    if message.document:
        if int(message.document.file_size) > 3145728:
            return
        mime_type = message.document.mime_type
        if mime_type != "image/png" and mime_type != "image/jpeg":
            return
        file_id = message.document.file_id

    if message.sticker:
        if message.sticker.is_animated:
            if not message.sticker.thumbs:
                return
            file_id = message.sticker.thumbs[0].file_id
        else:
            file_id = message.sticker.file_id

    if message.photo:
        file_id = message.photo.file_id

    if message.animation:
        if not message.animation.thumbs:
            return
        file_id = message.animation.thumbs[0].file_id

    if message.video:
        if not message.video.thumbs:
            return
        file_id = message.video.thumbs[0].file_id
    return file_id

    
@ZeroTwoTelethonClient.on_message(
    filters.command("anti_nsfw") & ~filters.private, group=3
)
@adminsOnly("can_change_info")
async def nsfw_toggle_func(_, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "Usage: /anti_nsfw [ENABLE|DISABLE]"
        )
    status = message.text.split(None, 1)[1].strip()
    status = status.lower()
    chat_id = message.chat.id
    if status == "enable":
        if is_nsfw_enabled(chat_id):
            return await message.reply("Already enabled.")
        enable_nsfw(chat_id)
        await message.reply_text("Enabled NSFW Detection.")
    elif status == "disable":
        if not is_nsfw_enabled(chat_id):
            return await message.reply("Already disabled.")
        disable_nsfw(chat_id)
        await message.reply_text("Disabled NSFW Detection.")
    else:
        await message.reply_text(
            "Unknown Suffix, Use /anti_nsfw [ENABLE|DISABLE]"
        )


@ZeroTwoTelethonClient.on_message(
    filters.command("anti_spam") & ~filters.private, group=3
)
@adminsOnly("can_change_info")
async def spam_toggle_func(_, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "Usage: /anti_spam [ENABLE|DISABLE]"
        )
    status = message.text.split(None, 1)[1].strip()
    status = status.lower()
    chat_id = message.chat.id
    if status == "enable":
        if is_spam_enabled(chat_id):
            return await message.reply("Already enabled.")
        enable_spam(chat_id)
        await message.reply_text("Enabled Spam Detection.")
    elif status == "disable":
        if not is_spam_enabled(chat_id):
            return await message.reply("Already disabled.")
        disable_spam(chat_id)
        await message.reply_text("Disabled Spam Detection.")
    else:
        await message.reply_text(
            "Unknown Suffix, Use /anti_spam [ENABLE|DISABLE]"
        )


@ZeroTwoTelethonClient.on_message(filters.command("nsfw_scan"), group=3)
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
    file = await ZeroTwoTelethonClient.download_media(file_id)
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


@ZeroTwoTelethonClient.on_message(filters.command("spam_scan"), group=3)
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