import os
from os import remove

from pyrogram import filters
from pyrogram.types import Message

from telegram.ext import CallbackContext
from telethon.utils import resolve_bot_file_id as res

from ZeroTwo.modules.helper_funcs.telethn.chatstatus import can_delete_messages
from ZeroTwo.utils.permissions import adminsOnly
from ZeroTwo.modules.log_channel import loggable
from ZeroTwo.modules.warns import warn
from ZeroTwo.modules.helper_funcs.string_handling import extract_time
from ZeroTwo import LOGGER, arq, ZeroTwoTelethonClient as zbot
from ZeroTwo.ex_plugins.dbfunctions import (disable_nsfw, disable_spam, enable_nsfw, enable_spam, is_nsfw_enabled, is_spam_enabled)
from ZeroTwo.ex_plugins.dbfunctions import (set_nsfw_strength, get_nsfw_setting)
from ZeroTwo.modules.helper_funcs.chat_status import user_not_admin
from ZeroTwo.FastTelethon import download_file


__mod_name__ = "Anti-NSFW"

__HELP__ = """
/antinsfw [on|off] - Enable or disable NSFW Detection.
/anti_spam [on|off] - Enable or disable Spam Detection.
/scan - To scan a message for NSFW or Spam.
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
        if message.sticker.is_video:
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

async def download(message):
    media = message.media
    if hasattr(media, "document"):
        msg = media.document
        mime_type = file.mime_type
        filename = message.file.name
        if not filename:
            if "video" in mime_type:
                filename = (
                    "video_" +
                    datetime.now().isoformat(
                        "_",
                        "seconds") +
                    ".mp4")
            elif "gif" in mime_type:
                filename = (
                    "gif_" +
                    datetime.now().isoformat(
                            "_",
                            "seconds") +
                        ".gif")
        file = await download_file(client=zbot, location=msg, out="NSFW/")
        return file
    else:
        file_id=get_file_id(message)
        file = await zbot.download_media(file_id)
        return file
    
@loggable
@adminsOnly("can_change_info")
@zbot.on_message(filters.command("nsfwmode") & ~filters.edited & ~filters.group)
async def blacklist_mode(_, message: Message):
    args = message.command
    chat_id = message.chat.id
    chat_name=message.chat.title
    if len(args)>1:
        if args[1].lower() in ["del", "delete"]:
            settypensfw = "delete blacklisted message"
            await set_nsfw_strength(chat_id, 1, "0")
        elif args[1].lower() == "warn":
            settypensfw = "warn the sender"
            await set_nsfw_strength(chat_id, 2, "0")
        elif args[1].lower() == "mute":
            settypensfw = "mute the sender"
            await set_nsfw_strength(chat_id, 3, "0")
        elif args[1].lower() == "kick":
            settypensfw = "kick the sender"
            await set_nsfw_strength(chat_id, 4, "0")
        elif args[1].lower() == "ban":
            settypensfw = "ban the sender"
            await set_nsfw_strength(chat_id, 5, "0")
        elif args[1].lower() == "tban":
            if len(args) == 1:
                teks = """It looks like you tried to set time value for blacklist but you didn't specified time; Try, `/blacklistmode tban <timevalue>`.
    Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                message.reply_text(teks)
                return ""
            restime = extract_time(message, args[1])
            if not restime:
                teks = """Invalid time value!
    Example of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                message.reply_text(teks)
                return ""
            time=args[2]
            settypensfw = f"temporarily ban for {time}"
            await set_nsfw_strength(chat_id, 6, str(args[2]))
        elif args[1].lower() == "tmute":
            if len(args) == 1:
                teks = """It looks like you tried to set time value for blacklist but you didn't specified  time; try, `/blacklistmode tmute <timevalue>`.
    Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                message.reply_text(teks)
                return ""
            restime = extract_time(message, args[2])
            if not restime:
                teks = """Invalid time value!
    Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                message.reply_text(teks)
                return ""
            time=args[2]
            settypensfw = f"temporarily mute for {time}"
            set_nsfw_strength(chat_id, 7, str(args[2]))
        else:
            message.reply_text(
                "I only understand: del/warn/ban/kick/mute/tban/tmute!",
            )
            return ""
        text = f"Changed blacklist mode: `{settypensfw}`!"
        message.reply_text(text)
        user_mention = message.reply_to_message.from_user.mention
        return (
            f"**{chat_name}:**\n"
            f"**Admin:** {user_mention}\n"
            f"Changed the NSFW mode. will `{settypensfw}`."
        )
    getmode, getvalue = await get_nsfw_setting(chat_id)
    if getmode == 1:
        settypensfw = "delete"
    elif getmode == 2:
        settypensfw = "warn"
    elif getmode == 3:
        settypensfw = "mute"
    elif getmode == 4:
        settypensfw = "kick"
    elif getmode == 5:
        settypensfw = "ban"
    elif getmode == 6:
        settypensfw = f"temporarily ban for {getvalue}"
    elif getmode == 7:
        settypensfw = f"temporarily mute for {getvalue}"
    else:
        text = f"Current Blacklist Settings: {settypensfw}"
        message.reply_text(text)
    return ""  

    
@adminsOnly("can_change_info")
@zbot.on_message(
    filters.command("antinsfw") & ~filters.private, group=3
)
async def nsfw_toggle_func(_, message: Message):
    chat_id = message.chat.id
    
    if len(message.command) != 2:
        status = is_nsfw_enabled(chat_id)
        await message.reply(text=f"Usage: /anti_spam [on|off]\n\nCurrent Setting: `{status}`")

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
    chat_id = message.chat.id
    if not await is_nsfw_enabled(message.chat.id):
        return
    if not message.from_user:
        return
    getmode, value = await get_nsfw_setting(chat_id)

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
        result = resp.result
        nsfw = result.is_nsfw
        if not nsfw:
            return
        try:
            try:
                if getmode == 1:
                    try:
                        message.delete()
                    except BadRequest:
                        pass
                elif getmode == 2:
                    try:
                        message.delete()
                    except BadRequest:
                        pass
                    warn(
                        message.user,
                        message.chat,
                        ("NSFW Media"),
                        message,
                    )
                    return
                elif getmode == 3:
                    message.delete()
                    bot.restrict_chat_member(
                        messgae.chat.id,
                        message.user.id,
                        permissions=ChatPermissions(can_send_messages=False),
                    )
                elif getmode == 4:
                    message.delete()
                    res = chat.unban_member(update.effective_user.id)
                    return
                elif getmode == 5:
                    message.delete()
                    chat.kick_member(user.id)
                    return
                elif getmode == 6:
                    message.delete()
                    bantime = extract_time(message, value)
                    chat.kick_member(user.id, until_date=bantime)
                    return
                elif getmode == 7:
                    message.delete()
                    mutetime = extract_time(message, value)
                    bot.restrict_chat_member(
                        message.chat.id,
                        message.user.id,
                        datetime.now() + timedelta(mutetime),
                        permissions=ChatPermissions(can_send_messages=False),
                    )
                    return
            except BadRequest as excp:
                if excp.message != "Message to delete not found":
                    LOGGER.exception("Error while deleting NSFW message.")   
        except Exception:
            return await message.reply_text("Delete Permissions not granted.")
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



@zbot.on_message(filters.command("scan"), group=3)
async def scan_command(_, message: Message):
    if not message.reply_to_message:
        return await message.reply("Reply to some media or text to scan it.")
    r = message.reply_to_message
    text = r.text or r.caption
    if text:
        m = await message.reply_text("Scanning")
        data = await arq.nlp(text)
        data = data.result[0]
        msg = f"""
**Is Spam:** `{data.is_spam}`
**Spam Probability:** `{data.spam_probability} %`
**Spam:** `{data.spam}`
**Ham:** `{data.ham}`
**Profanity:** `{data.profanity}`
    """
        await m.edit(msg, quote=True)
    if not text:
        reply = message.reply_to_message
        m = await message.reply_text("Scanning")
        file_id = get_file_id(reply)
        if not file_id:
            return await m.edit("Something went wrong.")
        file = await download(reply)
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
