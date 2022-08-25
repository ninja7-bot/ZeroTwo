from telegram.ext import CallbackContext

from telegram import ParseMode, Update
from telegram.error import BadRequest, Unauthorized
from telegram.utils.helpers import escape_markdown
from ZeroTwo import dispatcher, LOGGER
from telegram.ext import CommandHandler

from ZeroTwo.ex_plugins.dbfunctions import (stop_chat_logging, set_admin_chat, get_admin_chat)
from ZeroTwo.modules.helper_funcs.chat_status import user_admin

@user_admin
def send_log(
    context: CallbackContext, admin_chat_id: str, orig_chat_id: str, result: str):
    bot = context.bot
    try:
        bot.send_message(
            admin_chat_id,
            result,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except BadRequest as excp:
        if excp.message == "Chat not found":
            bot.send_message(
                orig_chat_id, "This admin chat has been deleted."
            )
            stop_chat_logging(orig_chat_id)
        else:
            bot.send_message(
                admin_chat_id,
                result
                + "\n\nFormatting has been disabled due to an unexpected error.",
                )
@user_admin
def logging(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    chat = update.effective_chat

    admin_chat = get_admin_chat(chat.id)
    if admin_chat:
        admin_chat_info = bot.get_chat(admin_chat)
        message.reply_text(
            f"This group's admin chat is:"
            f" {escape_markdown(admin_chat_info.title)} (`{admin_chat}`)",
            parse_mode=ParseMode.MARKDOWN,
        )

    else:
        message.reply_text("No admin chat has been set for this group!")

@user_admin        
def set_chat(update, context):
    args = context.args
    bot = context.bot
    message = update.effective_message
    chat = update.effective_chat
    if len(args) == 1:
        try:
            admin_chat = set_admin_chat(chat.id, chat_id)
            if admin_chat:
                bot.sendMessage(int(chat_id), f"This group will be admin chat for {chat.title}.")
        except TelegramError:
            LOGGER.warning("Couldn't set group as admin chat: %s", str(chat_id))
            update.effective_message.reply_text(
                "Couldn't set the group as admin chat. Perhaps I'm not part of that group?"
            )

    else:
        message.reply_text(
            "The steps to set a admin chat are:\n"
            " - add bot to the desired admin chat\n"
            " - send /setchat chat_id where chat_id is the ID of admin chat\n"
        )
        
@user_admin
def unsetlog(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    chat = update.effective_chat

    admin_chat = stop_chat_logging(chat.id)
    if admin_chat:
        bot.send_message(
            admin_chat, f"Admin chat has been unlinked from {chat.title}"
        )
        message.reply_text("Admin chat has been un-set.")
    else:
        message.reply_text("No admin chat has been set yet!")

LOG_HANDLER = CommandHandler("logchat", logging, run_async=True)
SET_LOG_HANDLER = CommandHandler("setchat", set_chat, run_async=True)
UNSET_LOG_HANDLER = CommandHandler("unlogchat", unsetlog, run_async=True)

dispatcher.add_handler(LOG_HANDLER)
dispatcher.add_handler(SET_LOG_HANDLER)
dispatcher.add_handler(UNSET_LOG_HANDLER)
