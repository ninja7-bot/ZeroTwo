from os import remove

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import (ChatAdminRequired, ChatWriteForbidden,
                             UserAdminInvalid)

from ZeroTwo.utils.permissions import adminsOnly

from ZeroTwo import arq, ZeroTwoTelethonClient as zbot
from ZeroTwo.ex_plugins.dbfunctions import (disable_nsfw, disable_spam, enable_nsfw,
                          enable_spam, is_nsfw_enabled,
                          is_spam_enabled)
from ZeroTwo.modules.helper_funcs.chat_status import user_admin, user_not_admin

__mod_name__ = "Anti_NSFW"

__HELP__ = """
/antinsfw [on|off] - Enable or disable NSFW Detection.
/anti_spam [on|off] - Enable or disable Spam Detection.
/nsfwscan - Classify a media.
/spamscan - Get Spam predictions of replied message.
"""

async def delete_get_info(message: Message):
    try:
        await message.delete()
    except (ChatAdminRequired, UserAdminInvalid):
        try:
            return await message.reply_text(
                "I don't have enough permission to delete "
                + "this message which is Flagged as Spam."
            )
        except ChatWriteForbidden:
            return await zbot.leave_chat(message.chat.id)

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


async def delete_nsfw_notify(
    message: Message,
    result,
):
    info = await delete_get_info(message)
    if not info:
        return
    msg = f"""
🚨 **NSFW ALERT**  🚔
{info}
**Prediction:**
    **Safe:** `{result.neutral} %`
    **Porn:** `{result.porn} %`
    **Adult:** `{result.sexy} %`
    **Hentai:** `{result.hentai} %`
    **Drawings:** `{result.drawings} %`
"""
    await zbot.send_message(message.chat.id, text=msg)


async def delete_spam_notify(
    message: Message,
    spam_probability: float,
):
    info = await delete_get_info(message)
    if not info:
        return
    msg = f"""
🚨 **SPAM ALERT**  🚔
{info}
**Spam Probability:** {spam_probability} %
__Message has been deleted__
"""
    await zbot.send_message(message.chat.id, text=msg)
      
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
    file = await zbot.download_media(file_id)
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
    
@user_not_admin
async def message_watcher(_, message: Message):
    user_id = None
    chat_id = None

    if message.chat.type in ["group", "supergroup"]:
        chat_id = message.chat.id

    if not chat_id or not user_id:
        return

    file_id = get_file_id(message)
    file_unique_id = get_file_unique_id(message)
    if file_id and file_unique_id:
        file = await zbot.download_media(file_id)
        try:
            resp = await arq.nsfw_scan(file=file)
        except Exception:
            try:
                return os.remove(file)
            except Exception:
                return
        os.remove(file)
        if resp.ok:
            if resp.result.is_nsfw:
                if is_nsfw_enabled(chat_id):
                    return await delete_nsfw_notify(
                        message, resp.result
                    )

    text = message.text or message.caption
    if not text:
        return
    resp = await arq.nlp(text)
    if not resp.ok:
        return
    result = resp.result[0]
    if not result.is_spam:
        return
    if not is_spam_enabled(chat_id):
        return
    await delete_spam_notify(message, result.spam_probability)
