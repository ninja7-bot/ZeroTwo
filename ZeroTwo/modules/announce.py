import html

from telegram import Update
from telegram.ext import CallbackContext
from telegram.utils.helpers import mention_html

from ZeroTwo.ex_plugins.dbfunctions import does_chat_log, enable_chat_log, disable_chat_log
from ZeroTwo.modules.helper_funcs.anonymous import AdminPerms
from ZeroTwo.modules.helper_funcs.anonymous import user_admin as u_admin
from ZeroTwo.modules.helper_funcs.decorators import botcmd
from ZeroTwo.modules.log_channel import loggable


@botcmd(command="announce", pass_args=True)
@u_admin(AdminPerms.CAN_CHANGE_INFO)
@loggable
def announcestat(update: Update, context: CallbackContext) -> str:
    args = context.args
    if len(args) > 0:
        update.effective_user
        message = update.effective_message
        chat = update.effective_chat
        user = update.effective_user
        chat_id=chat.id
        if args[0].lower() in ["on", "yes", "true"]:
            enable_chat_log(chat_id)
            update.effective_message.reply_text(
                "I've enabled announcemets in this group. Now any admin actions in your group will be announced."
            )
            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#ANNOUNCE_TOGGLED\n"
                f"Admin actions announcement has been <b>enabled</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name) if not message.sender_chat else message.sender_chat.title}\n "
            )
            return log_message
        elif args[0].lower() in ["off", "no", "false"]:
            disable_chat_log(chat_id)
            update.effective_message.reply_text(
                "I've disabled announcemets in this group. Now admin actions in your group will not be announced."
            )
            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#ANNOUNCE_TOGGLED\n"
                f"Admin actions announcement has been <b>disabled</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name) if not message.sender_chat else message.sender_chat.title}\n "
            )
            return log_message
    else:
        if does_chat_log(chat_it):
            result=True
        update.effective_message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {result}\n"
            "When True, any admin actions in your group will be announced."
            "When False, admin actions in your group will not be announced."
            )
        return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)
