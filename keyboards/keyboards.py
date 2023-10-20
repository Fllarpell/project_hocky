from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from callbacks.keyboard_callbacks import callback_data


def get_button(text, callback_data) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def get_back_button() -> InlineKeyboardButton:
    return get_button(text="Назад", callback_data=callback_data["back"])


def get_ready_register_button() -> InlineKeyboardButton:
    return get_button(text="Готов/а", callback_data=callback_data["startRegister"])


def get_event_kb() -> InlineKeyboardMarkup:
    kbm = InlineKeyboardMarkup()


def get_back_exit_row() -> [InlineKeyboardButton]:
    get_back_button
