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
            await message.reply_text(f"Enabled antichannel in **{chat.title}**")
        elif s in ["off", "no"]:
            await disable_antichannel(chat_id)
            await message.reply_text(f"Disabled antichannel in **{chat.title}**")
        else:
            await message.reply_text(f"Unrecognized arguments `{s}`")
        return
    message.reply_text(
        f"Antichannel setting is currently `{antichannel_status(chat_id)}` in **{chat.title}**.")

@zbot.on_message(filters.command("antichannel"), group=3)
async def eliminate_channel(_, message: Message):
    chat_id = chat.id
    if not await antichannel_status(chat_id):
        return
    if message.sender_chat and message.sender_chat.type == "channel" and not message.is_automatic_forward:
        await message.delete()
        message.chat.ban_member(sender_chat_id=channel.id, chat_id=chat.id)
