# Секрет-слово или секрет-фраза для получения админки
from aiogram import Router
from database.db_config import Database
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.types import Message
from aiogram.filters import Filter
from filters.chat_type import ChatTypeFilter
from aiogram import F as filters
from database.admin import Admin
from aiogram import types
from bot_settings import dp
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from states.states import Params_event, UploadPhotoForm
import asyncio
from datetime import datetime
from database.events import Event
from database.admin import Admin

router = Router()


# Название мероприятия
@router.message(filters.text, ChatTypeFilter(chat_type=["private"]), Command("add"))
async def event_name(message: types.Message, state: FSMContext):
    channels = Admin.get_channels(tg_id=message.chat.id)
    if channels is None:
        message.answer("Нет групп, где вы являетесь администратором")
        return
    userChannels = []
    for row in channels:
        tg_id, group_ID = row  # Assuming each row has two values: tg_id and group_ID
        userChannels.append(group_ID)
    ms1 = await message.answer(text="Напишите название мероприятия:")
    await state.set_state(Params_event.mes1)
    await state.update_data(mes1=ms1)
    await state.update_data(userChannels=userChannels)
    await state.set_state(Params_event.choosing_name_event)


# Сумма мероприятия
@router.message(Params_event.choosing_name_event)
async def event_sum(message: types.Message, state: FSMContext):
    user_data = await state.get_data()

    await state.update_data(chosen_name_event=message.text.lower())
    asyncio.create_task(delete_message(message, 0))
    asyncio.create_task(delete_message(user_data["mes1"], 0))
    ms2 = await message.answer(
        text=f"Название мероприятия: {message.text.lower()}\n"
        "Напишите сумму мероприятия с каждого человека:"
    )
    await state.set_state(Params_event.mes2)
    await state.update_data(mes2=ms2)
    await state.set_state(Params_event.choosing_sum)


# Дата мероприятия --- Сделать валидацию dd.mm.yyyy!!!!
@router.message(Params_event.choosing_sum)
async def event_date(message: types.Message, state: FSMContext):
    date_str = message.text
    try:
        # Проверяем корректность даты
        date = datetime.strptime(date_str, "%d.%m.%y")
        if date < datetime.now():
            raise ValueError
    except ValueError:
        await message.answer("Введте дату в формате  ДД.ММ.ГГ (например, 27.03.23)")
    else:
        async with state.proxy() as data:
            data["date"] = date
    user_data = await state.get_data()

    await state.update_data(chosen_sum_event=message.text.lower())
    asyncio.create_task(delete_message(message, 0))
    asyncio.create_task(delete_message(user_data["mes2"], 0))
    ms3 = await message.answer(
        text=f"Название мероприятия: {user_data['chosen_name_event']}\n"
        f"Сумма мероприятия: {message.text.lower()}\n"
        f"Напишите дату мероприятия:"
    )
    await state.set_state(Params_event.mes3)
    await state.update_data(mes3=ms3)
    await state.set_state(Params_event.choosing_date)


# Организатор мероприятия
@router.message(Params_event.choosing_date)
async def event_whom(message: types.Message, state: FSMContext):
    user_data = await state.get_data()

    await state.update_data(chosen_date_event=message.text.lower())
    asyncio.create_task(delete_message(message, 0))
    asyncio.create_task(delete_message(user_data["mes3"], 0))

    ms4 = await message.answer(
        text=f"Название мероприятия: {user_data['chosen_name_event']}\n"
        f"Сумма мероприятия: {user_data['chosen_sum_event']}\n"
        f"Дата мероприятия: {message.text.lower()}\n"
        f"Дополнительная информация: напишите 'Нет', если хотите ее оставить пустой"
    )
    await state.set_state(Params_event.mes4)
    await state.update_data(mes4=ms4)
    await state.set_state(Params_event.choosing_whom)


# Вывод мероприятия + запись в БД
@router.message(Params_event.choosing_whom)
async def event_output(message: types.Message, state: FSMContext):
    ver = InlineKeyboardButton(text="Верно", callback_data="верная форма")
    never = InlineKeyboardButton(text="Неверно", callback_data="неверная форма")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[ver, never]])
    user_data = await state.get_data()

    print(user_data)

    channels = user_data["userChannels"]

    Event.save_event(
        orgID=message.from_user.id,
        group=channels[0],
        name=user_data["chosen_name_event"],
        event_date=user_data["chosen_date_event"],
        fund=user_data["chosen_sum_event"],
    )
    asyncio.create_task(delete_message(message, 0))
    asyncio.create_task(delete_message(user_data["mes4"], 0))
    if message.text.lower() != "нет":
        await message.answer(
            text=f"1️⃣Дата мероприятия: {user_data['chosen_date_event']}\n"
            f"2️⃣Название мероприятия: {user_data['chosen_name_event']}\n"
            f"3️⃣Дополнительная информация: {message.text}\n"
            f"4️⃣Сумма с каждого: {user_data['chosen_sum_event']}\n",
            reply_markup=keyboard,
        )

    else:
        await message.answer(
            text=f"1️⃣Дата мероприятия: {user_data['chosen_date_event']}\n"
            f"2️⃣Название мероприятия: {user_data['chosen_name_event']}\n"
            f"3️⃣Дополнительная информация: Отсутствует\n"
            f"4️⃣Сумма с каждого: {user_data['chosen_sum_event']}\n",
            reply_markup=keyboard,
        )
    await state.clear()


async def delete_message(message: types.Message, sleep_time: int = 0):
    await asyncio.sleep(sleep_time)
    await message.delete()
