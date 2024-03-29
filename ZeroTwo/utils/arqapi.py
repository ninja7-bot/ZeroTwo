import json
import sys
from random import randint
from time import time
import socket
import aiohttp
from ZeroTwo import aiohttpsession
from aiohttp import ClientSession

from google_trans_new import google_translator
from Python_ARQ import ARQ
from search_engine_parser import GoogleSearch

from ZeroTwo import BOT_ID, OWNER_ID, ARQ_API_KEY
from ZeroTwo import ZeroTwoTelethonClient

SUDOERS = OWNER_ID
ARQ_API_URL = "https://arq.hamker.in"

# Aiohttp Client
print("[INFO]: INITIALZING AIOHTTP SESSION")
aiohttpsession = ClientSession()
# ARQ Client
print("[INFO]: INITIALIZING ARQ CLIENT")
arq = ARQ(ARQ_API_URL, ARQ_API_KEY, aiohttpsession)

app = ZeroTwoTelethonClient

