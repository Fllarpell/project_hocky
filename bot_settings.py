from aiogram import Bot as bot1, Dispatcher
from aiogram.enums import ParseMode
import logging
from aiogram.fsm.storage.memory import MemoryStorage

# АПИ ТОКЕН
API_TOKEN = "6461874385:AAHHgOml-_v5NMHq3_YNcRTvPLhRoSutvVk"
# БД - основная
bot_username = "@beta_evt_bot"
# Логирование
logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
bot = bot1(token=API_TOKEN, parse_mode=ParseMode.HTML)
