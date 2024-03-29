from ast import Call
import html
import json
import os
from typing import Optional

from ZeroTwo import (
    MOD_USERS,
    OWNER_ID,
    SUDOS,
    SUPPORT_CHAT,
    RONIN,
    REAPERS,
    HELLHOUND,
    dispatcher,
)
from ZeroTwo.modules.helper_funcs.chat_status import (is_user_admin, dev_plus, sudo_plus,
                                                      whitelist_plus,
                                                      support_plus,
                                                      user_admin)
from ZeroTwo.modules.helper_funcs.extraction import (extract_user,
                                                          extract_user_and_text)
from ZeroTwo.modules.helper_funcs.misc import send_to_list
from ZeroTwo.modules.sql.users_sql import get_all_chats
from telegram import ParseMode, Update
from telegram.error import BadRequest, TelegramError
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, run_async)
from telegram.utils.helpers import mention_html
from ZeroTwo.modules.log_channel import gloggable

ELEVATED_USERS_FILE = os.path.join(os.getcwd(),
                                   'ZeroTwo/elevated_users.json')


def check_user_id(user_id: int, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    if not user_id:
        reply = "Not a User ID."

    elif user_id == bot.id:
        reply = "Bot ID detected."

    else:
        reply = None
    return reply


# This can serve as a deeplink example.
#disasters =
# """ Text here """

# do not async, not a handler
#def send_disasters(update):
#    update.effective_message.reply_text(
#        disasters, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

### Deep link example ends

#SUDO Users have all the rights within Zero Two. If Zero Two is admin, they're also admin in the group, for the bot.
@run_async
@dev_plus
@gloggable
def addsudo(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDOS:
        message.reply_text("This member is already a Sudo Class.")
        return ""

    if user_id in REAPERS:
        rt += "Promoting Reaper to Sudo Class."
        data['supports'].remove(user_id)
        REAPERS.remove(user_id)

    if user_id in HELLHOUND:
        rt += "Promoting Hellhound to Sudo Class."
        data['whitelists'].remove(user_id)
        HELLHOUND.remove(user_id)

    data['sudos'].append(user_id)
    SUDOS.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + "\nAppointing Sudo Class to {}!".format(
            user_member.first_name))

    log_message = (
        f"#SUDO\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message

#REAPERS have right to gban. They are free to gban anyone and everyone.
@run_async
@sudo_plus
@gloggable
def addsupport(
    update: Update,
    context: CallbackContext,
) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDOS:
        rt += "Demoting to Reaper Class."
        data['sudos'].remove(user_id)
        SUDOS.remove(user_id)

    if user_id in REAPERS:
        message.reply_text("This user is already a Reaper Class.")
        return ""

    if user_id in HELLHOUND:
        rt += "Promoting Hellhound to Reaper Class."
        data['whitelists'].remove(user_id)
        HELLHOUND.remove(user_id)

    data['supports'].append(user_id)
    REAPERS.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + f"\n{user_member.first_name} was added as a Reaper Class!")

    log_message = (
        f"#SUPPORT\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message

#HELLHOUNDS are excluded from all sort of admin mutes, bans and everything else.
@run_async
@sudo_plus
@gloggable
def addwhitelist(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDOS:
        rt += "This member is a Sudo, Demoting to Hellhound."
        data['sudos'].remove(user_id)
        SUDOS.remove(user_id)

    if user_id in REAPERS:
        rt += "This user is already a Reaper, Demoting to Hellhound."
        data['supports'].remove(user_id)
        REAPERS.remove(user_id)

    if user_id in HELLHOUND:
        message.reply_text("This user is already a Hellhound Class.")
        return ""

    data['whitelists'].append(user_id)
    HELLHOUND.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt +
        f"\nSuccessfully promoted {user_member.first_name} to a Hellhound Class!")

    log_message = (
        f"#WHITELIST\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))} \n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message

#RONINS can be banned and muted.
@run_async
@sudo_plus
@gloggable
def addronin(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDOS:
        rt += "This member is a Sudo, Demoting to Ronin User."
        data['sudos'].remove(user_id)
        SUDOS.remove(user_id)

    if user_id in REAPERS:
        rt += "This user is already a Reaper, Demoting to Ronin User."
        data['supports'].remove(user_id)
        REAPERS.remove(user_id)

    if user_id in HELLHOUND:
        rt += "This user is already a Hellhound, Demoting to Ronin User."
        data['whitelists'].remove(user_id)
        HELLHOUND.remove(user_id)

    if user_id in RONIN:
        message.reply_text("This user is already a Ronin User.")
        return ""

    data['RONIN'].append(user_id)
    RONIN.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt +
        f"\nSuccessfully promoted {user_member.first_name} to a Ronin Class!"
    )

    log_message = (
        f"#RONIN\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))} \n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
@dev_plus
@gloggable
def removesudo(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDOS:
        message.reply_text("Dismissing Sudo Class.")
        SUDOS.remove(user_id)
        data['sudos'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNSUDO\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != 'private':
            log_message = "<b>{}:</b>\n".format(html.escape(
                chat.title)) + log_message

        return log_message

    else:
        message.reply_text("This user is not a Sudo!")
        return ""


@run_async
@sudo_plus
@gloggable
def removesupport(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in REAPERS:
        message.reply_text("Dismissing Reaper Class.")
        REAPERS.remove(user_id)
        data['supports'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNSUPPORT\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != 'private':
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message

    else:
        message.reply_text("This user is not a Reaper.")
        return ""


@run_async
@sudo_plus
@gloggable
def removewhitelist(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in HELLHOUND:
        message.reply_text("Demoting to normal user")
        HELLHOUND.remove(user_id)
        data['whitelists'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNWHITELIST\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != 'private':
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        message.reply_text("This user is not a Hellhound!")
        return ""


@run_async
@sudo_plus
@gloggable
def removeronin(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in RONIN:
        message.reply_text("Demoting to normal user")
        RONIN.remove(user_id)
        data['RONIN'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#RMRONIN\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != 'private':
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        message.reply_text("This user is not a Ronin!")
        return ""


@run_async
@whitelist_plus
def whitelistlist(update: Update, context: CallbackContext):
    reply = "<b>HELLHOUNDS</b>\n"
    bot = context.bot
    for each_user in HELLHOUND:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)

            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def roninlist(update: Update, context: CallbackContext):
    reply = "<b>RONINS</b>\n"
    bot = context.bot
    for each_user in RONIN:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def supportlist(update: Update, context: CallbackContext):
    bot = context.bot
    reply = "<b>REAPERS</b>\n"
    for each_user in REAPERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def sudolist(update: Update, context: CallbackContext):
    bot = context.bot
    true_sudo = list(set(SUDOS) - set(MOD_USERS))
    reply = "<b>SUDO</b>\n"
    for each_user in true_sudo:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


CLASS_DETAILS="""
• Moderators
Developers who can access the bots server and can execute, modify bot code. Can also manage other Class Members.

• Watcher
Only one exists, bot owner. 
Owner has complete bot access, including bot admin-ship in chats Zero Two is at.

• Sudo
Sudo super user access, can gban, manage class members lower than them and are admins in Zero Two. 

• Reapers
Also known as Support users, reapers have access to globally ban users across Zero Two.

• Ronins
Ronins are fully immune to mute, ban, kicks etc.

• Hellhound
Cannot be banned, flood kicked but can be manually banned by admins.
They can be muted
"""

def classdes(update: Update, context: CallbackContext):
    update.effective_message.reply_text(CLASS_DETAILS,
        parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    

@run_async
@whitelist_plus
def devlist(update: Update, context: CallbackContext):
    bot = context.bot
    true_dev = list(set(MOD_USERS) - {OWNER_ID})
    reply = "<b>MODERATORS</b>\n"
    for each_user in true_dev:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


__help__ = f"""
*Notice:*
Commands listed here only work for users with special access are mainly used for troubleshooting, debugging purposes.
Group admins/group owners do not need these commands. 

 ╔ *List all special users:*
 ╠ `/sudo`*:* Lists all Sudo
 ╠ `/reapers`*:* Lists all Reapers
 ╠ `/ronin`*:* Lists all Ronins
 ╠ `/hellhound`*:* Lists all Hellhounds
 ╚ `/mods`*:* Lists all Moderators

 ╔ *Ping:*
 ╠ `/ping`*:* gets ping time of bot to telegram server
 ╚ `/pingall`*:* gets all listed ping times

 ╔ *Broadcast: (Bot owner only)*
 ╠  *Note:* This supports basic markdown
 ╠ `/broadcastall`*:* Broadcasts everywhere
 ╠ `/broadcastusers`*:* Broadcasts too all users
 ╚ `/broadcastgroups`*:* Broadcasts too all groups

 ╔ *Groups Info:*
 ╠ `/groups`*:* List the groups with Name, ID, members count as a txt
 ╚ `/getchats`*:* Gets a list of group names the user has been seen in. Bot owner only

 ╔ *Blacklist:* 
 ╠ `/ignore`*:* Blacklists a user from 
 ╠  using the bot entirely
 ╚ `/notice`*:* Whitelists the user to allow bot usage

 ╔ *Speedtest:*
 ╚ `/speedtest`*:* Runs a speedtest and gives you 2 options to choose from, text or image output

 ╔ *Global Bans:*
 ╠ `/gban user reason`*:* Globally bans a user
 ╚ `/ungban user reason`*:* Unbans the user from the global bans list

 ╔ *Module loading:*
 ╠ `/listmodules`*:* Lists names of all modules
 ╠ `/load modulename`*:* Loads the said module to 
 ╠   memory without restarting.
 ╠ `/unload modulename`*:* Loads the said module from
 ╚   memory without restarting.memory without restarting the bot 

 ╔ *Remote commands:*
 ╠ `/rban user group`*:* Remote ban
 ╠ `/runban user group`*:* Remote un-ban
 ╠ `/rpunch user group`*:* Remote kick
 ╠ `/rmute user group`*:* Remote mute
 ╠ `/runmute user group`*:* Remote un-mute
 ╚ `/ginfo username/link/ID`*:* Pulls info panel for entire group

 ╔ *Windows self hosted only:*
 ╠ `/reboot`*:* Restarts the bots service
 ╚ `/gitpull`*:* Pulls the repo and then restarts the bots service
 
 ╔ *Debugging and Shell:* 
 ╠ `/debug <on/off>`*:* Logs commands to updates.txt
 ╠ `/logs`*:* Run this in support group to get logs in pm
 ╠ `/eval`*:* Self explanatory
 ╠ `/sh`*:* Self explanator
 ╚ `/py`*:* Self explanatory

Visit @{SUPPORT_CHAT} for more information.
"""

SUDO_HANDLER = CommandHandler(("addsudo", "adddg"), addsudo)
SUPPORT_HANDLER = CommandHandler(("addsupport", "adddm"), addsupport)
RONIN_HANDLER = CommandHandler(("addronin"), addronin)
WHITELIST_HANDLER = CommandHandler(("addwhitelist", "addwl"), addwhitelist)
UNSUDO_HANDLER = CommandHandler(("removesudo", "rmvsudo"), removesudo)
UNSUPPORT_HANDLER = CommandHandler(("removesupport", "rmvreap"),
                                   removesupport)
UNRONIN_HANDLER = CommandHandler(("removeronin"), removeronin)
UNWHITELIST_HANDLER = CommandHandler(("removewhitelist", "removewolf"),
                                     removewhitelist)

WHITELISTLIST_HANDLER = CommandHandler(["whitelistlist", "HELLHOUND"],
                                       whitelistlist)
RONINLIST_HANDLER = CommandHandler(["ronin"], roninlist)
SUPPORTLIST_HANDLER = CommandHandler(["supportlist", "reapers"], supportlist)
SUDOLIST_HANDLER = CommandHandler(["sudolist", "sudos"], sudolist)
DEVLIST_HANDLER = CommandHandler(["devlist", "mods"], devlist)
CLASSDES_HANDLER = CommandHandler(["classdesc", "class"], classdes)

dispatcher.add_handler(SUDO_HANDLER)
dispatcher.add_handler(SUPPORT_HANDLER)
dispatcher.add_handler(RONIN_HANDLER)
dispatcher.add_handler(WHITELIST_HANDLER)
dispatcher.add_handler(UNSUDO_HANDLER)
dispatcher.add_handler(UNSUPPORT_HANDLER)
dispatcher.add_handler(UNRONIN_HANDLER)
dispatcher.add_handler(UNWHITELIST_HANDLER)

dispatcher.add_handler(WHITELISTLIST_HANDLER)
dispatcher.add_handler(RONINLIST_HANDLER)
dispatcher.add_handler(SUPPORTLIST_HANDLER)
dispatcher.add_handler(SUDOLIST_HANDLER)
dispatcher.add_handler(DEVLIST_HANDLER)
dispatcher.add_handler(CLASSDES_HANDLER)

__mod_name__ = "Class"
__handlers__ = [
    SUDO_HANDLER, SUPPORT_HANDLER, RONIN_HANDLER, WHITELIST_HANDLER,
    UNSUDO_HANDLER, UNSUPPORT_HANDLER, UNRONIN_HANDLER, UNWHITELIST_HANDLER,
    WHITELISTLIST_HANDLER, RONINLIST_HANDLER, SUPPORTLIST_HANDLER,
    SUDOLIST_HANDLER, DEVLIST_HANDLER, CLASSDES_HANDLER
]
