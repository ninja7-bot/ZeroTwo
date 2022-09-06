from telegram.ext import CallbackContext, run_async
from ..modules.helper_funcs.anonymous import user_admin, AdminPerms

from pyrogram import filters
from pyrogram.types import Message

from ZeroTwo.ex_plugins.dbfunctions import antichannel_status, disable_antichannel, enable_antichannel, no_network, yes_network, network_status
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
        await message.delete()
        await zbot.ban_chat_member(chat_id, sender_chat)
    except:
        return await message.reply_text("Admin rights gib wen?")
    
#network_names=["『VƗŁŁȺƗNS』", "MɅͶǀɅΧ", "卐ŞΔŇΔŦΔŇI卐", "ΛӨGIЯI", "クルー"]

@zbot.on_message(filters.command("network"), group=3)
async def toggle_network(_, message: Message):
    chat_id = message.chat.id
    args = message.command
    if len(args) > 1:
        s = args[1].lower()
        if s in ["yes", "on"]:
            await no_network(chat_id)
            await message.reply_text(f"Enabled Anti Network System in **{message.chat.title}**")
        elif s in ["off", "no"]:
            await yes_network(chat_id)
            await message.reply_text(f"Disabled Anti Network System in **{message.chat.title}**")
        else:
            await message.reply_text(f"Unrecognized arguments `{s}`")
        return
    elif len(args) == 1:
        status=await network_status(chat_id)
        title=message.chat.title
        await message.reply_text(
            f"Anti Network System setting is currently `{status}` in **{title}**.")
        
@zbot.on_message(filters.group)
async def eliminate_user(_, message: Message):
    m=message
    chat_id = message.chat.id
    user=m.from_user
    name = str(m.from_user.first_name) + str(m.from_user.last_name)
    uid=m.user.id
    
    if not await network_status(chat_id):
        return
    network_names = get_tag()
    
    for banned in network_names:
        pattern = r"( |^|[^\w])" + re.escape(banned) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            try:
                await message.delete()
                await zbot.ban_chat_member(chat_id, uid)
                await message.send(f"Banned {user.mention} for Network Tag in name.")
            except:
                return await message.reply_text("Admin rights gib wen?")
        else:
            return
        
@zbot.on_message(filters.command("addnetwork"), group=3)
async def add_network(_, message: Message):
    m = message
    uid=m.from_user.id
    tag=message.command
    msg="**Currently Blacklisted Network tags are**:\n"
    
    network_names=get_tag()
    
    if len(tag)==1:
        if uid==1191870547:
            for i in network_names:
                msg+=f"- `{i}`\n"
            await message.reply_text(msg)
        else:
            await message.reply_text("You're not authorized. Bot only command for now.")
    if uid==1191870547:
        to_add=tag[1]
        
        if to_add in network_names:
            return await message.reply_text("Network is already in the banned list.")
        
        await save_tag(to_add)
        return await message.reply_text(f"Added the tag {to_add} to Banned Networks.")
    else:
        return await message.reply_text("You're not authorized. Bot owner only command for now.")
