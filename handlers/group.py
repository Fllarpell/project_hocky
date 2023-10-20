from aiogram import Router, types
from aiogram import F
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated, Message
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from database.db_config import Database as db
from bot_settings import bot, bot_username
import fix_file
from aiogram.handlers import MessageHandler
from database.admin import Admin

groupRouter = Router()


@groupRouter.message(F.new_chat_members)
async def send_welcome(message: types.Message):
    reg = InlineKeyboardButton(text="Зарегистрироваться✅", callback_data="rgstr")
    kb = InlineKeyboardMarkup(inline_keyboard=[[reg]])
    bot_obj = await bot.get_me()
    bot_id = bot_obj.id
    for chat_member in message.new_chat_members:
        if (
            message.new_chat_members
            and message.new_chat_members[0].is_bot
            and message.new_chat_members[0].id == bot.id
        ):
            chat_id = message.chat.id
            user_id = message.from_user.id
            # Пользователь добавил бота в группу, теперь отправим ему личное сообщение
            await bot.send_message(user_id, "Спасибо, что добавили меня в группу!")
            is_admin = Admin.get(
                Admin.tg_id == user_id, Admin.group_ID == chat_id
            ).save()
            print(is_admin)
            if is_admin == 1:
                await bot.send_message(user_id, "Снова здравствуйте!")
            else:
                Admin.create(tg_id=user_id, group_ID=chat_id)
        if chat_member.id == bot_id:
            await message.answer(
                f'🚩Доброго времени суток, участники беседы "{message.chat.title}"!👋\n\n'
                f"Я бот🤖, созданный для организации мероприятий. Если меня добавили сюда, "
                f"значит один или несколько из участников этой беседы хотят упростить себе жизнь, для чего именно я и был создан!\n\n"
                f"Если вы будете принимать участие в мероприятиях, в таком случае вам необходимо начать со мной диалог:\n"
                f"1) Перейдите в личные сообщения со мной: {bot_username}\n"
                f"2) отправьте команду /start (в личных сообщениях со мной)\n"
                f"Дальнейшие инструкции я приведу в личных сообщениях.",
                reply_markup=kb,
            )
