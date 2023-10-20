from aiogram import Router, types
from aiogram import F as filters
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated, Message
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from database.db_config import Database as db
from bot_settings import bot
import fix_file

chat_control_router = Router()


async def get_chat_participants(chat_id):
    try:
        # Call the get_chat_members method to retrieve information about all chat members
        response = await bot.get_chat_members(chat_id)

        # Iterate over the response and extract the user IDs
        participant_ids = [member.user.id for member in response]

        # Return the list of participant IDs
        return participant_ids

    except Exception as e:
        print(f"An error occurred: {e}")
