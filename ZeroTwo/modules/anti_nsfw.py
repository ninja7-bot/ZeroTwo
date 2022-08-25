import os
from os import remove
import time

from pyrogram import filters
from pyrogram.types import Message

from ZeroTwo.modules.helper_funcs.telethn.chatstatus import (
    can_delete_messages)

from ZeroTwo.utils.permissions import adminsOnly

from telegram import ParseMode, ChatPermissions
from telegram.error import BadRequest
from telegram.utils.helpers import mention_html
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async

from ZeroTwo import arq, ZeroTwoTelethonClient as zbot
from ZeroTwo.ex_plugins.dbfunctions import (disable_nsfw, disable_spam, enable_nsfw,
                          enable_spam, is_nsfw_enabled,
                          is_spam_enabled, get_admin_chat)
from ZeroTwo.modules.helper_funcs.chat_status import user_not_admin
from ZeroTwo.modules.helper_funcs.alternate import send_message, typing_action
from ZeroTwo.modules.log_channel import loggable
from ZeroTwo.modules.warns import warn
from ZeroTwo.modules.helper_funcs.string_handling import extract_time
from ZeroTwo.modules.connection import connected
from ZeroTwo.modules.admin_log import send_log
from ZeroTwo.modules.sql.approve_sql import is_approved
import ZeroTwo.modules.sql.nsfw_sql as sql
from ZeroTwo import dispatcher, LOGGER

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

@run_async
def nsfw_mode(update, context):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    chat = update.effective_chat
    chat_id = update.effective_chat.id
    chat_name = update.effective_message.chat.title
    if args:
        if args[0].lower() in ["default"]:
            settypensfw = "default"
            sql.set_nsfw_strength(chat_id, 0, "0")
        elif args[0].lower() in ["ban"]:
            settypensfw = "ban the sender"
            sql.set_nsfw_strength(chat_id, 1, "0")
        elif args[0].lower() == "warn":
            settypensfw = "warn the sender"
            sql.set_nsfw_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypensfw = "mute the sender"
            sql.set_nsfw_strength(chat_id, 3, "0")
        elif args[0].lower() == "kick":
            settypensfw = "kick the sender"
            sql.set_nsfw_strength(chat_id, 4, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """It looks like you tried to set time value for nsfw but you didn't specified time; Try, `/nsfwmode tban <timevalue>`.
    Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = """Invalid time value!
    Example of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            settypensfw = "temporarily ban for {}".format(args[1])
            sql.set_nsfw_strength(chat_id, 5, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = """It looks like you tried to set time value for nsfw but you didn't specified  time; try, `/nsfwmode tmute <timevalue>`.
    Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = """Invalid time value!
    Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            settypensfw = "temporarily mute for {}".format(args[1])
            sql.set_nsfw_strength(chat_id, 6, str(args[1]))
        else:
            send_message(
                update.effective_message,
                "I only understand: default/warn/ban/kick/mute/tban/tmute!",
            )
            return ""       
    getmode, getvalue = get_nsfw_setting(chat_id)
    if getmode == 0:
        settypensfw = "default"
    elif getmode == 1:
        settypensfw = "ban"
    elif getmode == 2:
        settypensfw = "warn"
    elif getmode == 3:
        settypensfw = "mute"
    elif getmode == 4:
        settypensfw = "kick"
    elif getmode == 5:
        settypensfw = "temporarily ban for {}".format(getvalue)
    elif getmode == 6:
        settypensfw = "temporarily mute for {}".format(getvalue)
    text = "Current NSFW Mode: *{}*.".format(settypensfw)
    send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
    return ""

NSFWMODE_HANDLER = CommandHandler(
    "nsfwmode", nsfw_mode, pass_args=True, run_async=True
)

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


ALERT = """ 
**NSFW Image Detected & Deleted Successfully!**
**User:** {message.from_user.mention} [`{message.from_user.id}`]
**Safe:** `{result.neutral} %`
**Porn:** `{result.porn} %`
**Adult:** `{result.sexy} %`
**Hentai:** `{result.hentai} %`
**Drawings:** `{result.drawings} %`

Action has been taken against the user.
"""


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
async def nsfw_watcher(_,message: Message):
    if not await is_nsfw_enabled(message.chat.id):
        return
    if not message.from_user:
        return
    bot = zbot
    user = message.from_user
    chat_id = message.chat.id
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
        result = resp.result[0]
        nsfw = result.is_nsfw
        admin_chat = get_admin_chat(chat_id)
        if admin_chat:
            admin_chat_id = bot.get_chat(admin_chat)
            send_log(chat_id, admin_chat_id, result=message)
        else:
            return
        if not nsfw:
            return
        getmode, value = sql.get_nsfw_setting(chat_id)
        try:
            if getmode == 0:
                bot.restrict_chat_member(
                    chat_id,
                    user_id,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=False,
                        can_send_other_messages=False,
                        can_invite_users=False,
                        can_pin_messages=False,
                        can_send_polls=False,
                        can_change_info=False,
                        can_add_web_page_previews=False,
                    ),
                    until_date=(int(time.time() + 24 * 60 * 60))),
            elif getmode == 1:
                message.delete()
                chat.kick_member(user.id)
                bot.sendMessage(
                    chat.id,
                    f"Banned {user.first_name} for sending NSFW Media.",
                )
                return
            elif getmode == 2:
                try:
                    message.delete()
                except BadRequest:
                    pass
                warn(
                    user,
                    chat,
                    ("Sending NSFW Media."),
                    message,
                    user,
                )
                return
            elif getmode == 3:
                message.delete()
                bot.restrict_chat_member(
                    chat.id,
                    user.id,
                    permissions=ChatPermissions(can_send_messages=False),
                )
                bot.sendMessage(
                    chat.id,
                    f"Muted {user.first_name} for sending NSFW Media.!",
                )
                return
            elif getmode == 4:
                message.delete()
                res = chat.unban_member(user.id)
                if res:
                    bot.sendMessage(
                    chat.id,
                        f"Kicked {user.first_name} for sending NSFW Media.!",
                    )
                return
            elif getmode == 5:
                message.delete()
                bantime = extract_time(message, value)
                chat.kick_member(user.id, until_date=bantime)
                bot.sendMessage(
                    chat.id,
                    f"Banned {user.first_name} until '{value}' for sending NSFW Media.!",
                )
                return
            elif getmode == 6:
                message.delete()
                mutetime = extract_time(message, value)
                bot.restrict_chat_member(
                    chat.id,
                    user.id,
                    until_date=mutetime,
                    permissions=ChatPermissions(can_send_messages=False),
                )
                bot.sendMessage(
                    chat.id,
                    f"Muted {user.first_name} until '{value}' for sending NSFW Media.!",
                )
                return
        except:
            await message.reply_text("Delete Permissions not granted.")
        
        
@user_not_admin
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
