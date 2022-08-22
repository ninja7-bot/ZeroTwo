import requests, json
from ZeroTwo import dispatcher
from ZeroTwo.modules.disable import DisableAbleCommandHandler
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async

from ZeroTwo import util

from ZeroTwo import OXFORD_APP_ID as APP_ID
from ZeroTwo import OXFORD_APP_KEY as APP_KEY

def ud(update: Update, context: CallbackContext):
    message = update.effective_message
    text = message.text[len("/ud ") :]
    results = requests.get(
        f"https://api.urbandictionary.com/v0/define?term={text}"
    ).json()
    try:
        reply_text = f'*{text}*\n\n{results["list"][0]["definition"]}\n\n_{results["list"][0]["example"]}_'
    except:
        reply_text = "No results found."
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

def dict(update: Update, context: CallbackContext):
    message = update.effective_message
    endpoint = "entries"
    language_code = "en-us"
    word_id = message.text[len("/dict"):]
    url = "https://od-api.oxforddictionaries.com/api/v2/" + endpoint + "/" + language_code + "/" + word_id.lower()
    r = requests.get(url, headers = {"app_id": APP_ID, "app_key": APP_KEY})
    try:
        try:
            definitions = r.json()['results'][0]['lexicalEntries'][0]['entries'][0]['senses'][0]['definitions'][0]
            sentence = r.json()['results'][0]['lexicalEntries'][0]['entries'][0]['senses'][0]['examples'][0]['text']
            message.reply_text(message.chat.id, f'*Word* - {word_id}\n*Definition* - {definitions}\n*Example* - {sentence.capitalize()}.')
        except:
            message.reply_text('Meaning not found!', parse_mode=ParseMode.MARKDOWN)
    except:
        message.reply_text(message.chat.id, 'Something went wrong...')





UD_HANDLER = DisableAbleCommandHandler(["ud"], ud, run_async=True)
DICT_HANDLER = DisableAbleCommandHandler(["dict"], dict, run_async=True)

dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(DICT_HANDLER)

__command_list__ = ["ud", "dict"]
__handlers__ = [UD_HANDLER, DICT_HANDLER]
