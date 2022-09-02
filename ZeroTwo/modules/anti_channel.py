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
    await message.reply_text(
        f"Antichannel setting is currently `{antichannel_status(chat_id)}` in **{message.chat.title}**.")

@zbot.on_message(~filters.group, group=3)
async def eliminate_channel(_, message: Message):
    chat_id = message.chat.id
    if not await antichannel_status(chat_id):
        return
    if message.sender_chat and message.sender_chat.type == "channel" and not message.linked_chat:
        await message.delete()
        sender_chat = message.sender_chat.id
        await zbot.ban_chat_member(chat_id, sender_chat)
