from tmdbv3api import TMDb
from tmdbv3api import Movie
from tmdbv3api import TV

from bs4 import BeautifulSoup

import random
from telegram.ext import(CommandHandler, MessageHandler, Filters, Updater)
from ZeroTwo import dispatcher
from ZeroTwo import TMDB_API
from telegram import ParseMode

tmdb = TMDb()
tmdb.api_key = TMDB_API

# error code - 0. couldn't find movie
# erroe code 1. couldn't find similar movie


def get_recommendation():
    movie = Movie()
    recommendation = random.choice(movie.popular())
    return {"title": recommendation.title, "overview": recommendation.overview, "vote": str(recommendation.vote_average)+"/10", "poster": "https://image.tmdb.org/t/p/w1280"+recommendation.poster_path}


def get_similar(string):
    movie = Movie()
    movies = movie.search(string)
    if len(movies) == 0:
        return 0
    similar_movies = movie.similar(random.choice(movies).id)
    if len(similar_movies) == 0:
        return 1
    similar_movie = random.choice(similar_movies)
    return {"title": similar_movie.title, "overview": similar_movie.overview, "vote": str(similar_movie.vote_average)+"/10", "poster": "https://image.tmdb.org/t/p/w1280"+similar_movie.poster_path}


def recommend(update, context):
    response = get_recommendation()
    context.bot.send_photo(
        chat_id=update.effective_chat.id, photo=response["poster"], caption="*Title* : {}\n\n*Synopsis*: _{}_\n\n*Rating*: `{}`".format(response["title"], response["overview"], response["vote"]),
    parse_mode=ParseMode.MARKDOWN)


def similar(update, context):
    message = update.message.text.replace('/similar', ' ').strip()
    if message == '':
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Type a movie name after /similar.")
    else:
        response = get_similar(message)
        if response == 0:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Couldn't find movie. Try again.")
        elif response == 1:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Couldn't find similar movie. Try again.")
        else:
            context.bot.send_photo(
                chat_id=update.effective_chat.id, photo=response["poster"], caption="*Title* : {}\n\n*Synopsis*: _{}_\n\n*Rating*: `{}`".format(response["title"], response["overview"], response["vote"]),
                parse_mode=ParseMode.MARKDOWN)

recommend_handler = CommandHandler('recommend', recommend)
dispatcher.add_handler(recommend_handler)

similar_handler = CommandHandler('similar', similar)
dispatcher.add_handler(similar_handler)
