from telegram.ext.filters import Filters
from ZeroTwo.modules.helper_funcs.decorators import botcmd, botmsg
from telegram import Update, message
from telegram.ext import CallbackContext, run_async
from ..modules.helper_funcs.anonymous import user_admin, AdminPerms
import html
from ZeroTwo.ex_plugins.dbfunctions import antichannel_status, disable_antichannel, enable_antichannel
from ZeroTwo import ZeroTwoTelethonClient as zbot

@botcmd(command="antichannel", group=100)
@user_admin(AdminPerms.CAN_RESTRICT_MEMBERS)
def set_antichannel(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    chat_id = chat.id
    args = context.args
    if len(args) > 0:
        s = args[0].lower()
        if s in ["yes", "on"]:
            enable_antichannel(chat_id)
            message.reply_html("Enabled antichannel in {}".format(html.escape(chat.title)))
        elif s in ["off", "no"]:
            disable_antichannel(chat_id)
            message.reply_html("Disabled antichannel in {}".format(html.escape(chat.title)))
        else:
            message.reply_text("Unrecognized arguments {}".format(s))
        return
    message.reply_html(
        "Antichannel setting is currently {} in {}".format(antichannel_status(chat_id), html.escape(chat.title)))

@run_async
@botmsg(Filters.chat_type.groups, group=110)
def eliminate_channel(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    chat_id = chat.id
    bot = context.bot
    if not await antichannel_status(chat_id):
        return
    if message.sender_chat and message.sender_chat.type == "channel" and not message.is_automatic_forward:
        message.delete()
        sender_chat = message.sender_chat
        bot.ban_chat_sender_chat(sender_chat_id=sender_chat.id, chat_id=chat.id)
