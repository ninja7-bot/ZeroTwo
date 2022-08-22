import requests, json
from ZeroTwo import dispatcher
from ZeroTwo.modules.disable import DisableAbleCommandHandler
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async
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

def dict(update:Update, context=CallbackContext):
    message = update.effective_message
    text = message.text[len("/dict ") :]

    url = 'https://api.dictionaryapi.dev/api/v2/entries/en/{}'.format(text)

    response = requests.get(url)

# return a custom response if an invalid word is provided
    if response.status_code == 404:
        error_response = 'We are not able to provide any information about your word. Please confirm that the word is ' \
                         'correctly spelt or try the search again at a later time.'
        return message.reply_text(error_response)

    word_info = response.json()[0]
    
    word = word_info['word']

    meanings = '\n'
    synonyms = ''
    definition = ''
    example = ''
    antonyms = ''

    
    for word_meaning in word_info['meanings']:
        meanings += 'Meaning ' + ':\n'

        for word_definition in word_meaning['definitions']:
            # extract the each of the definitions of the word
            definition = word_definition['definition']

            # extract each example for the respective definition
            if 'example' in word_definition:
                example = word_definition['example']

            # extract the collection of synonyms for the word based on the definition
            for word_synonym in word_definition['synonyms']:
                synonyms += word_synonym + ', '

            # extract the antonyms of the word based on the definition
            for word_antonym in word_definition['antonyms']:
                antonyms += word_antonym + ', '

        meanings += '*Definition*: ' + definition + '\n\n'
        meanings += '*Example*: ' + example + '\n\n'
        meanings += '*Synonym*: ' + synonyms + '\n\n'
        meanings += '*Antonym*: ' + antonyms + '\n\n\n'

        meaning_counter += 1

    # format the data into a string
    meaning = f"Word: *{word}*\n\n{meanings}"
    message.reply_text(meaning, parse_mode=ParseMode.MARKDOWN)




UD_HANDLER = DisableAbleCommandHandler(["ud"], ud, run_async=True)
DICT_HANDLER = DisableAbleCommandHandler(["dict"], dict, run_async=True)

dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(DICT_HANDLER)

__command_list__ = ["ud", "dict"]
__handlers__ = [UD_HANDLER, DICT_HANDLER]
