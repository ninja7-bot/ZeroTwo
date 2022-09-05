from telegram.ext import CallbackContext, run_async
from ..modules.helper_funcs.anonymous import user_admin, AdminPerms

from pyrogram import filters
from pyrogram.types import Message

from ZeroTwo.ex_plugins.dbfunctions import antichannel_status, disable_antichannel, enable_antichannel
from ZeroTwo import ZeroTwoTelethonClient as zbot

@user_admin(AdminPerms.CAN_RESTRICT_MEMBERS)
@zbot.on_message(filters.command("antichannel"), group=3)
async def set_antichannel(_, message: Message):
    chat_id = message.chat.id
    args = message.command
    if len(args) > 1:
        s = args[1].lower()
        if s in ["yes", "on"]:
            await enable_antichannel(chat_id)
            await message.reply_text(f"Enabled antichannel in **{message.chat.title}**")
        elif s in ["off", "no"]:
            await disable_antichannel(chat_id)
            await message.reply_text(f"Disabled antichannel in **{message.chat.title}**")
        else:
            await message.reply_text(f"Unrecognized arguments `{s}`")
        return
    elif len(args) == 1:
        status=await antichannel_status(chat_id)
        title=message.chat.title
        await message.reply_text(
            f"Antichannel setting is currently `{status}` in **{title}**.")

    
custom_message_filter = filters.create(
    lambda _, __, message: not message.forward_from_chat and not message.from_user
)
custom_chat_filter = filters.create(lambda _, __, message: bool(message.sender_chat))
@zbot.on_message(custom_message_filter & filters.group & custom_chat_filter)
async def eliminate_channel(_, message: Message):
    chat_id = message.chat.id
    sender_chat = message.sender_chat.id
    if not await antichannel_status(chat_id):
        return
    try:
        message.delete()
        zbot.ban_chat_member(chat_id, sender_chat)
    except:
        return await message.reply_text("Admin rights gib wen?")
