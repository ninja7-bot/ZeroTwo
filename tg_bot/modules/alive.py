import os
import re
from platform import python_version as kontol
from telethon import events, Button
from telegram import __version__ as telever
from telethon import __version__ as tlhver
from pyrogram import __version__ as pyrover
from tg_bot.events import register
from tg_bot import telethn as tbot


PHOTO = "https://telegra.ph/file/9c2e4c8599e3b56c9fcd8.mp4"


@register(pattern=("/alive"))
async def awake(event):
    TEXT = f"**Zero Two seems to be working perfectly!** \n\n"
    await tbot.send_photo(event.chat_id, PHOTO, caption=TEXT)
