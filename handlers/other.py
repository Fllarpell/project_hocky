import logging
import asyncio
from aiogram import *
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram import types
from aiogram.fsm.context import FSMContext
import secrets
import string
from database.db_config import Database as db
from states.states import FIO
from keyboards.keyboards import get_ready_register_button
from states.states import Params_event, UploadPhotoForm
from aiogram.exceptions import TelegramMigrateToChat, TelegramForbiddenError
from aiogram.filters import Command
from aiogram import F as filters
from bot_settings import bot
from filters.chat_type import ChatTypeFilter
from aiogram.filters import Command
from database.user import User

other_router = Router()


def generate_alphanum_crypt_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    crypt_rand_string = "".join(
        secrets.choice(letters_and_digits) for i in range(length)
    )
    return crypt_rand_string


# Регистрация в боте пользователем
@other_router.message(ChatTypeFilter(chat_type=["private"]), Command("register"))
async def register_command(message: types.Message):
    ready = get_ready_register_button()
    kb = InlineKeyboardMarkup(inline_keyboard=[[ready]])
    user = User.select().where(User.tg_id == message.from_user.id).scalar()
    print(user)
    if user is None:
        await message.answer(
            'Для регистрации в данном боте будет необходимо указать своё Имя, Фамилию и Отчество. Это всё, что потребуется. Как будете готовы нажмите на кнопку под сообщением "Готов(а)"!',
            reply_markup=kb,
        )
    else:
        await bot.send_message(
            chat_id=message.from_user.id,
            text="Вы уже зарегистрированы.",
        )


# регистрация из стартового сообщения
@other_router.callback_query(lambda call: call.data == "rgstr")
async def register_from_start_message(
    callback_query: types.CallbackQuery, state: FSMContext
):
    ready = InlineKeyboardButton(text="Готов(а)", callback_data="startRegister")
    kb = InlineKeyboardMarkup(inline_keyboard=[[ready]])
    try:
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text='Для регистрации в данном боте будет необходимо указать своё Фамилию и Имя. Это всё, что потребуется. Как будете готовы нажмите на кнопку под сообщением "Готов(а)"!',
            reply_markup=kb,
        )
    except:
        await callback_query.answer("Для начала активируй меня!")


# нажал кнопку готов к регистрации/нажамал кнопку неверное ФИО
@other_router.callback_query(F.data == "startRegister")
@other_router.callback_query(F.data == "re_register")
async def startRegister(callback_query: types.CallbackQuery, state: FSMContext):
    asyncio.create_task(delete_message(callback_query.message, 0))
    user = User.select().where(User.tg_id == callback_query.from_user.id).scalar()
    print("text", user)
    if user is not None:
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text="Вы уже зарегистрированы.",
        )
    else:
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text="Пожалуйста, укажите свою Фамилию!",
        )
        await state.set_state(FIO.lastname)


# Фамилия
@other_router.message(FIO.lastname)
async def get_lastname_parent(message: types.Message, state: FSMContext):
    await state.update_data(lastname=message.text.title())

    await message.answer(
        f"Ваша Фамилия: {message.text.title()}\n" f"Пожалуйста, укажите своё Имя!"
    )

    await state.set_state(FIO.firstname)


# Имя
@other_router.message(FIO.firstname)
async def get_firstname(message: types.Message, state: FSMContext):
    await state.update_data(firstname=message.text.title())
    user_data = await state.get_data()
    """
    Allow user to cancel any action
    """
    yep = InlineKeyboardButton(text="Верно✅", callback_data="right_FIO")
    no = InlineKeyboardButton(text="Неверно❌", callback_data="re_register")
    kb = InlineKeyboardMarkup(inline_keyboard=[[yep, no]])
    await message.answer(
        f'Ваша Фамилия: {user_data["lastname"]}\n'
        f"Ваше Имя: {message.text.title()}\n"
        f"Верно ли указаны Фамилия и Имя?",
        reply_markup=kb,
    )
    state.clear()


@other_router.callback_query(F.data == "right_FIO")
async def right_fio(callback_query: types.CallbackQuery, state: FSMContext):
    userData = await state.get_data()
    user = User.create(
        tg_id=callback_query.from_user.id,
        lastname=userData["lastname"],
        firstname=userData["firstname"],
        username=callback_query.from_user.username,
    )
    await callback_query.answer("Теперь вы зарегестрированы.")
    await bot.delete_message(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
    )

    await state.clear()


# @other_router.callback_query(F.data == "re_register")
# async def right_fio(callback_query: types.CallbackQuery, state: FSMContext):
#     userData = await state.get_data()
#     print(callback_query, userData)
#     user = User.update(
#         tg_id=callback_query.from_user.id,
#         firstname=userData["firstname"],
#         lastname=userData["lastname"],
#         username=callback_query.from_user.username,
#     )
#     bot.send_message(chat_id=callback_query.from_user.id, text="re register")
#     state.clear()


# вывод организаторов
@other_router.callback_query(lambda call: call.data == "organisators")
async def output_organisators(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        grID = callback_query.message.chat.id
        gr = set(
            db.connection.execute(
                "select groups from groups where groupID=?", (grID,)
            ).fetchall()
        )
        orgs = []
        for i in gr:
            admins_temp = db.connection.execute(
                "select tgID from admins where groups=?", (i[0],)
            ).fetchall()
            for j in admins_temp:
                orgs.append(j[0])

        out = "Организаторы: \n"
        cnt = 1
        for ad in orgs:
            admins = db.connection.execute(
                "select * from parents where tgID=?", (ad,)
            ).fetchone()
            out += f"{cnt}) {admins[2]} {admins[3]} - {admins[7]}\n"
            cnt += 1

        await callback_query.message.edit_text(text=out)
    except:
        await callback_query.message.edit_text(
            text="Не могу найти организаторов, повторите попытку позже"
        )


# стартовая команда
@other_router.message(Command("start"))
async def start_command(message: types.Message):
    cht_id = str(message.chat.id)
    if cht_id[0] == "-":
        reg = InlineKeyboardButton("Зарегистрироваться✅", callback_data="rgstr")
        org = InlineKeyboardButton("Организаторы🛂", callback_data="organisators")
        kb = InlineKeyboardMarkup(inline_keyboard=[[reg, org]])
        await message.answer(
            f'🚩Доброго времени суток, участники беседы "{message.chat.title}"!👋\n\n'
            f"Я бот🤖 [@evt_assistant_bot], созданный для организации мероприятий. Если меня добавили сюда, "
            f"значит один или несколько из участников этой беседы хотят упростить себе жизнь, для чего именно я и был создан!\n\n"
            f"Если вы будете принимать участие в мероприятиях, в таком случае вам необходимо выполнить несколько последовательных действий:\n\n"
            f"1️⃣) Активировать меня, зайдя в личные сообщения со мной(если вы еще этого не делали).\n"
            f'2️⃣) Нажать кнопку под данным сообщением "Зарегистрироваться✅" для того, чтобы я вас мог зарегистрировать.\n'
            f"3️⃣) После чего я напишу вам сообщение, где вы закончите регистрацию в данном боте.\n\n"
            f"Делается это для того, чтобы организаторам мероприятий было проще: понимать, кто участвует, оплатил мероприятие или связаться с ними.\n"
            f"Если же вы уже были зарегистрированы и нажимали данную кнопку под сообщением, но делали это в другой беседе, при этом собираетесь принимать участие от организаторов этой группы, в таком случае без страха нажимайте на кнопку! 🚩",
            reply_markup=kb,
        )
    else:
        user = User.select().where(User.tg_id == message.chat.id).scalar()
        print("user", user)
        if user is not None:
            await message.answer(f"Снова здравствуйте!")
        else:
            await message.answer(
                f"Приветствую! Теперь я смогу уведомлять тебя о новых событиях. "
                f"Для регистрации в боте введите /register"
            )


# хелповая команда
@other_router.message(Command("help"))
async def help_command(message: types.Message):
    await message.reply(
        "/add - [Для админов] добавить мероприятие, после его создания, будет предложена рассылка\n\n"
        "/events - увидеть все мероприятия происходящие, начиная с сегодняшнего дня\n\n"
        "/myevents - мероприятия, в которых вы принимаете мероприятия\n\n"
        "/register - регистрация в боте(если вы еще этого не делали)\n\n"
        "/profile - ваш профиль\n\n"
        "/news - [Для админов] рассылка новостей по вашим группам, после /news через пробел пишите текст"
    )


# генератор inline-кнопок для рассылки
def genmarkup(data):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=namee, callback_data=str(i[0]))]]
    )
    for i in data:
        namee = db.connection.execute(
            "select groupTitle from groups where groupID=?", (i[0],)
        ).fetchone()[0]
    return markup


@other_router.callback_query(lambda call: call.data == "верная форма")
async def choice_rassilka(callback_query: types.CallbackQuery, state: FSMContext):
    yeah = InlineKeyboardButton(
        text="Сохранить и разослать", callback_data="хочу_разослать"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[yeah]])

    await callback_query.message.edit_text(
        text=callback_query.message.text, reply_markup=keyboard
    )


@other_router.callback_query(lambda call: call.data == "неверная форма")
async def choice_rassilka(callback_query: types.CallbackQuery, state: FSMContext):
    no = InlineKeyboardButton(text="Отмена", callback_data="exit")
    nono = InlineKeyboardButton(text="Заполнить заново", callback_data="заново")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[no, nono]])

    await callback_query.message.edit_text(
        callback_query.message.text, reply_markup=keyboard
    )


@other_router.callback_query(lambda call: call.data == "заново")
async def choice_rassilka(callback_query: types.CallbackQuery, state: FSMContext):
    adm = db.connection.execute(
        "select * from admins where tgID=?", (callback_query.from_user.id,)
    ).fetchone()

    ms1 = await callback_query.message.edit_text(text="Напишите название мероприятия:")
    await state.set_state(Params_event.mes1)
    await state.update_data(mes1=ms1)
    await state.set_state(Params_event.choosing_name_event)


# Соглашение на рассылку ( предложение групп для рассылки )
@other_router.callback_query(lambda call: call.data == "хочу_разослать")
async def choice_rassilka(callback_query: types.CallbackQuery):
    gr = db.connection.execute(
        "select groups from admins where tgID=?", (callback_query.from_user.id,)
    ).fetchone()[0]
    mer = callback_query.message.text.split("\n")[1].split(": ")[1]
    dat = callback_query.message.text.split("\n")[0].split(": ")[1]
    summ = callback_query.message.text.split("\n")[3].split(": ")[1]
    org = callback_query.message.text.split("\n")[2].split(": ")[1]
    exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
    if "Отсутствует" in callback_query.message.text:
        for i in range(1000):
            rand_str = generate_alphanum_crypt_string(16)
            if (
                db.connection.execute(
                    "select * from Event where eventID=?", (rand_str,)
                ).fetchone()
                is None
            ):
                q = f"INSERT INTO 'Event' (groups, datee, namee, org, summ, tgID, eventID) VALUES ('{gr}', '{dat}', '{mer}', '{org}', {summ}, {callback_query.from_user.id}, '{rand_str}')"
                db.connection.execute(q)
                db.connection.commit()
                break

    else:
        gr = db.connection.execute(
            "select groups from admins where tgID=?", (callback_query.from_user.id,)
        ).fetchone()[0]
        for i in range(1000):
            rand_str = generate_alphanum_crypt_string(16)
            if (
                db.connection.execute(
                    "select * from Event where eventID=?", (rand_str,)
                ).fetchone()
                is None
            ):
                q = f"INSERT INTO 'Event' (groups, datee, namee, org, summ, tgID, eventID) VALUES ('{gr}', '{dat}', '{mer}', '{org}', {summ}, {callback_query.from_user.id}, '{rand_str}')"
                db.connection.execute(q)
                db.connection.commit()
                break

    await callback_query.answer("Выбирай куда отсылать")

    data = set(
        db.connection.execute(
            "SELECT groupID FROM parents where groups=? and tgID=?",
            (gr, callback_query.from_user.id),
        ).fetchall()
    )
    await callback_query.message.edit_text(
        f"{callback_query.message.text}", reply_markup=genmarkup(data).add(exit)
    )


# Сама рассылка
@other_router.callback_query(lambda call: "-" in call.data)
async def rasslka(callback_query: types.CallbackQuery):
    if callback_query.message.text.split(" ")[0] != "/news":
        adm_id = callback_query.from_user.id
        gr = db.connection.execute(
            "select groups from admins where tgID=?", (adm_id,)
        ).fetchone()[0]

        # FIX TUTA
        if (
            db.connection.execute(
                "select organisator from parents where tgID=?",
                (callback_query.from_user.id,),
            ).fetchone()[0]
            == "False"
        ):
            db.connection.execute(
                "update parents set organisator=? where tgID=?",
                (
                    "True",
                    callback_query.from_user.id,
                ),
            )
            db.connection.commit()
        if (
            db.connection.execute(
                "select * from parents where groupID=? and groups=?",
                (callback_query.data, gr),
            ).fetchone()
            is None
        ):
            prnts = db.connection.execute(
                "select * from parents where groupID=?", (callback_query.data,)
            ).fetchall()
            for parent in prnts:
                if (
                    db.connection.execute(
                        "select * from groups where groups=? and groupID=?",
                        (gr, parent[5]),
                    ).fetchone()
                    is None
                ):
                    namee = db.connection.execute(
                        "select groupTitle from groups where groupID=?",
                        (parent[5],),
                    ).fetchone()[0]
                    db.connection.execute(
                        "insert into groups (groups, groupID, groupTitle) "
                        'values ("{}", {}, "{}")'.format(gr, parent[5], namee)
                    )
                    db.connection.commit()

                # FIX TUTA
                if adm_id == parent[5]:
                    db.connection.execute(
                        "insert into parents (groups, tgID, last_name, first_name, groupID, organisator, nickname, username) "
                        'values ("{}", {}, "{}", "{}", {}, "{}", "{}", "{}")'.format(
                            gr,
                            parent[1],
                            parent[2],
                            parent[3],
                            parent[5],
                            "True",
                            parent[7],
                            parent[8],
                        )
                    )
                    db.connection.commit()
                else:
                    db.connection.execute(
                        "insert into parents (groups, tgID, last_name, first_name, groupID, organisator, nickname, username) "
                        'values ("{}", {}, "{}", "{}", {}, "{}", "{}", "{}")'.format(
                            gr,
                            parent[1],
                            parent[2],
                            parent[3],
                            parent[5],
                            "False",
                            parent[7],
                            parent[8],
                        )
                    )
                    db.connection.commit()

        await callback_query.answer("Отправил куда надо!")
        uch = InlineKeyboardButton(text="Участвую", callback_data="Участвую")
        neuch = InlineKeyboardButton(text="Не участвую", callback_data="Не участвую")
        kb = InlineKeyboardMarkup(inline_keyboard=[[uch, neuch]])

        try:
            await bot.send_message(
                chat_id=callback_query.data,
                text=callback_query.message.text,
                reply_markup=kb,
            )
        except TelegramMigrateToChat as e:
            chat_ID = str(e).split(" New id: ")[1].split(".")[0].strip()
            db.connection.execute(
                "update groups set groupID=? where groupID=?",
                (
                    int(chat_ID),
                    int(callback_query.data),
                ),
            )
            db.connection.commit()
            await bot.send_message(
                chat_id=chat_ID,
                text=callback_query.message.text,
                reply_markup=kb,
            )
    else:
        adm_id = callback_query.from_user.id
        gr = db.connection.execute(
            "select groups from admins where tgID=?", (adm_id,)
        ).fetchone()[0]

        # FIX TUTA
        if (
            db.connection.execute(
                "select organisator from parents where tgID=?",
                (callback_query.from_user.id,),
            ).fetchone()[0]
            == "False"
        ):
            db.connection.execute(
                "update parents set organisator=? where tgID=?",
                (
                    "True",
                    callback_query.from_user.id,
                ),
            )
            db.connection.commit()
        if (
            db.connection.execute(
                "select * from parents where groupID=? and groups=?",
                (callback_query.data, gr),
            ).fetchone()
            is None
        ):
            prnts = db.connection.execute(
                "select * from parents where groupID=?", (callback_query.data,)
            ).fetchall()
            for parent in prnts:
                if (
                    db.connection.execute(
                        "select * from groups where groups=? and groupID=?",
                        (gr, parent[5]),
                    ).fetchone()
                    is None
                ):
                    namee = db.connection.execute(
                        "select groupTitle from groups where groupID=?",
                        (parent[5],),
                    ).fetchone()[0]
                    db.connection.execute(
                        "insert into groups (groups, groupID, groupTitle) "
                        'values ("{}", {}, "{}")'.format(gr, parent[5], namee)
                    )
                    db.connection.commit()

                # FIX TUTA
                if adm_id == parent[5]:
                    db.connection.execute(
                        "insert into parents (groups, tgID, last_name, first_name, groupID, organisator, nickname, username) "
                        'values ("{}", {}, "{}", "{}", {}, "{}", "{}", "{}")'.format(
                            gr,
                            parent[1],
                            parent[2],
                            parent[3],
                            parent[5],
                            "True",
                            parent[7],
                            parent[8],
                        )
                    )
                    db.connection.commit()
                else:
                    db.connection.execute(
                        "insert into parents (groups, tgID, last_name, first_name, groupID, organisator, nickname, username) "
                        'values ("{}", {}, "{}", "{}", {}, "{}", "{}", "{}")'.format(
                            gr,
                            parent[1],
                            parent[2],
                            parent[3],
                            parent[5],
                            "False",
                            parent[7],
                            parent[8],
                        )
                    )
                    db.connection.commit()

        await callback_query.answer("Отправил куда надо!")

        try:
            fious = db.connection.execute(
                "select * from parents where tgID=?", (callback_query.from_user.id,)
            ).fetchone()
            await bot.send_message(
                chat_id=callback_query.data,
                text=callback_query.message.text.replace("/news", "", 1)
                + f"\n\nОтправил: {fious[7]}",
            )
        except TelegramMigrateToChat as e:
            fious = db.connection.execute(
                "select * from parents where tgID=?", (callback_query.from_user.id,)
            ).fetchone()
            chat_ID = str(e).split(" New id: ")[1].split(".")[0].strip()
            db.connection.execute(
                "update groups set groupID=? where groupID=?",
                (
                    int(chat_ID),
                    int(callback_query.data),
                ),
            )
            db.connection.commit()
            await bot.send_message(
                chat_id=chat_ID,
                text=callback_query.message.text.replace("/news", "", 1)
                + f"\n\nОтправил: {fious[7]}",
            )


# Принимает участие в мероприятии
@other_router.callback_query(lambda call: call.data == "Участвую")
async def participation(callback_query: types.CallbackQuery, state: FSMContext):
    mer = callback_query.message.text.split("\n")[1].split(": ")[1]
    summ = callback_query.message.text.split("\n")[3].split(": ")[1]
    dat = callback_query.message.text.split("\n")[0].split(": ")[1]
    org = callback_query.message.text.split("\n")[2].split(": ")[1]

    # личные сообщения с ботом
    if callback_query.message.chat.type == "private":
        gr1 = db.connection.execute(
            "select groups from Event where namee=? and summ=? and datee=? and org=?",
            (mer, summ, dat, org),
        ).fetchall()
        gr = ""
        # поиск верной группы(не беседы)
        for i in gr1:
            adm = db.connection.execute(
                "select tgID from admins where groups=?", (i[0],)
            ).fetchone()[0]
            if (
                db.connection.execute(
                    "select groups from Event where namee=? and datee=? and summ=? and org=? and tgID=?",
                    (mer, dat, summ, org, adm),
                ).fetchone()[0]
                == i[0]
            ):
                gr = i[0]  # нахождение нужной группы(не беседы)
                break
        exist_parents_in_active_events = db.connection.execute(
            "select * from active_events where groups=? and namee=? and datee=? and tgID=?",
            (gr, mer, dat, callback_query.from_user.id),
        ).fetchone()
        regist_parents = db.connection.execute(
            "select * from parents where tgID=?", (callback_query.from_user.id,)
        ).fetchone()
    # сообщение в беседах
    else:
        gr = db.connection.execute(
            "select groups from Event where namee=? and summ=? and datee=? and org=?",
            (mer, summ, dat, org),
        ).fetchone()[0]
        exist_parents_in_active_events = db.connection.execute(
            "select * from active_events where groups=? and namee=? and datee=? and tgID=? and org=?",
            (gr, mer, dat, callback_query.from_user.id, org),
        ).fetchone()
        regist_parents = db.connection.execute(
            "select * from parents where tgID=?", (callback_query.from_user.id,)
        ).fetchone()
    # пользователь не нажимал на кнопку участвоваю
    if exist_parents_in_active_events is None:
        # пользователь не регистрировался в боте
        if regist_parents[2] == "None":
            await callback_query.answer("Пожалуйста, пройдите регистрацию!")
        # пользователь зарегистрирован в боте
        else:
            # бесплатное мероприятие
            if int(summ) == 0:
                db.connection.execute(
                    "insert into active_events "
                    "(groups, tgID, namee, datee, parent, particip, paid, org, summ)"
                    'values ("{}", {}, "{}", "{}", "{}", "{}", "{}", "{}", {})'
                    "".format(
                        gr,
                        callback_query.from_user.id,
                        mer,
                        dat,
                        regist_parents[2] + " " + regist_parents[3],
                        "True",
                        "True",
                        org,
                        summ,
                    )
                )
                db.connection.commit()
            # платное мероприятие
            else:
                db.connection.execute(
                    "insert into active_events "
                    "(groups, tgID, namee, datee, parent, particip, paid, org, summ)"
                    'values ("{}", {}, "{}", "{}", "{}", "{}", "{}", "{}", {})'
                    "".format(
                        gr,
                        callback_query.from_user.id,
                        mer,
                        dat,
                        regist_parents[2] + " " + regist_parents[3],
                        "True",
                        "False",
                        org,
                        summ,
                    )
                )
                db.connection.commit()
            try:
                # Мероприятие бесплатное
                if int(summ) == 0:
                    await bot.send_message(
                        chat_id=callback_query.from_user.id,
                        text=f'Здравствуйте, {regist_parents[2] + " " + regist_parents[3]}👋!\nВы участвуете в мероприятии "{mer}", '
                        f"проходящее {dat}🗓!\n\n"
                        f"Данное мероприятие не требует перевода денежных средств, то есть является бесплатным, в следствие чего подтверждение не требуется!",
                    )
                    await callback_query.answer("Записал тебя на данное мероприятие")
                # Мероприятие платное - требуется подтверждение оплаты
                else:
                    paid = InlineKeyboardButton(
                        text="Оплачено", callback_data=f"paiid_{grp}"
                    )
                    kb = InlineKeyboardMarkup(inline_keyboard=[[paid]])
                    grp = db.connection.execute(
                        "select groups from Event where namee=? and summ=? and datee=? and org=?",
                        (mer, summ, dat, org),
                    ).fetchone()[0]

                    await bot.send_message(
                        chat_id=callback_query.from_user.id,
                        text=f'Здравствуйте, {regist_parents[2] + " " + regist_parents[3]}👋!\n'
                        f'Вы участвуете в мероприятии "{mer}", проходящее {dat}🗓\n'
                        f"Дополнительная информация о мероприятии: {org}\n\n"
                        f'Пожалуйста, оплатите мероприятие суммой в размере {summ}, после чего нажмите нажмите на кнопку под сообщением "Оплачено💸", а затем пришлите скрин-подтверждение оплаты!',
                        reply_markup=kb,
                    )
                    await callback_query.answer("Записал тебя на данное мероприятие")
            # бот не может написать пользователю
            except TelegramForbiddenError:
                await callback_query.answer(
                    text="Я не могу тебе написать первым, активируй меня!"
                )
    # пользователь нажимал на кнопку участвоваю
    else:
        if (
            db.connection.execute(
                f"select particip from active_events where tgID=? and namee=? and datee=? and groups=? and org=? and summ=?",
                (callback_query.from_user.id, mer, dat, gr, org, summ),
            ).fetchone()[0]
            == "False"
        ):
            await callback_query.answer("Записал тебя на данное мероприятие")
            db.connection.execute(
                f"update active_events set particip=? where tgID=? and namee=? and datee=? and groups=? and org=? and summ=?",
                ("True", callback_query.from_user.id, mer, dat, gr, org, summ),
            )
            db.connection.commit()
        else:
            await callback_query.answer(text="Вы уже участвуете в данном мероприятии!😁")


# Не принимает участие в мероприятии
@other_router.callback_query(lambda call: call.data == "Не участвую")
async def participation(callback_query: types.CallbackQuery, state: FSMContext):
    mer = callback_query.message.text.split("\n")[1].split(": ")[1]
    summ = callback_query.message.text.split("\n")[3].split(": ")[1]
    dat = callback_query.message.text.split("\n")[0].split(": ")[1]
    org = callback_query.message.text.split("\n")[2].split(": ")[1]

    # личные сообщения с ботом
    if callback_query.message.chat.type == "private":
        gr1 = db.connection.execute(
            "select groups from Event where namee=? and summ=? and datee=? and org=?",
            (mer, summ, dat, org),
        ).fetchall()
        gr = ""
        # поиск верной группы(не беседы)
        for i in gr1:
            adm = db.connection.execute(
                "select tgID from admins where groups=?", (i[0],)
            ).fetchone()[0]
            if (
                db.connection.execute(
                    "select groups from Event where namee=? and datee=? and summ=? and org=? and tgID=?",
                    (mer, dat, summ, org, adm),
                ).fetchone()[0]
                == i[0]
            ):
                gr = i[0]  # нахождение нужной группы(не беседы)
                break
        exist_parents_in_active_events = db.connection.execute(
            "select * from active_events where groups=? and namee=? and datee=? and tgID=?",
            (gr, mer, dat, callback_query.from_user.id),
        ).fetchone()
        regist_parents = db.connection.execute(
            "select * from parents where tgID=?", (callback_query.from_user.id,)
        ).fetchone()
    # сообщение в беседах
    else:
        gr = db.connection.execute(
            "select groups from Event where namee=? and summ=? and datee=? and org=?",
            (mer, summ, dat, org),
        ).fetchone()[0]
        exist_parents_in_active_events = db.connection.execute(
            "select * from active_events where groups=? and namee=? and datee=? and tgID=? and org=?",
            (gr, mer, dat, callback_query.from_user.id, org),
        ).fetchone()
        regist_parents = db.connection.execute(
            "select * from parents where tgID=?", (callback_query.from_user.id,)
        ).fetchone()
    # пользователь не нажимал на кнопку участвоваю
    if exist_parents_in_active_events is None:
        # пользователь не регистрировался в боте
        if regist_parents[2] == "None":
            await callback_query.answer("Пожалуйста, зарегистрируйтесь во мне!")
        # пользователь зарегистрирован в боте
        else:
            # бесплатное мероприятие
            if int(summ) == 0:
                db.connection.execute(
                    "insert into active_events "
                    "(groups, tgID, namee, datee, parent, particip, paid, org, summ)"
                    'values ("{}", {}, "{}", "{}", "{}", "{}", "{}", "{}", {})'
                    "".format(
                        gr,
                        callback_query.from_user.id,
                        mer,
                        dat,
                        regist_parents[2] + " " + regist_parents[3],
                        "False",
                        "False",
                        org,
                        summ,
                    )
                )
                db.connection.commit()
            # платное мероприятие
            else:
                db.connection.execute(
                    "insert into active_events "
                    "(groups, tgID, namee, datee, parent, particip, paid, org, summ)"
                    'values ("{}", {}, "{}", "{}", "{}", "{}", "{}", "{}", {})'
                    "".format(
                        gr,
                        callback_query.from_user.id,
                        mer,
                        dat,
                        regist_parents[2] + " " + regist_parents[3],
                        "False",
                        "False",
                        org,
                        summ,
                    )
                )
                db.connection.commit()
    # пользователь нажимал на кнопку не участвоваю
    else:
        if (
            db.connection.execute(
                f"select particip from active_events where tgID=? and namee=? and datee=? and groups=? and org=? and summ=?",
                (callback_query.from_user.id, mer, dat, gr, org, summ),
            ).fetchone()[0]
            == "True"
        ):
            await callback_query.answer("Убрал вас из списка участвующих.")
            db.connection.execute(
                f"update active_events set particip=? where tgID=? and namee=? and datee=? and groups=? and org=? and summ=?",
                ("False", callback_query.from_user.id, mer, dat, gr, org, summ),
            )
            db.connection.commit()
        else:
            await callback_query.answer(
                text="Вы уже не участвуете в данном мероприятии!😔"
            )


# Захват скрина-подтверждения
@other_router.callback_query(lambda call: "paiid_" in call.data)
async def paid_mer(callback_query: types.CallbackQuery, state: FSMContext):
    txt = callback_query.message.text
    await state.set_state(UploadPhotoForm.grps)
    await state.update_data(grpss=callback_query.data.split("paiid_")[1])
    await state.set_state(UploadPhotoForm.mer)
    await state.update_data(
        namee_mer=txt.split('Вы участвуете в мероприятии "')[1].split('", проходящее ')[
            0
        ]
    )
    await state.set_state(UploadPhotoForm.dat)
    await state.update_data(datee_mer=txt.split(" проходящее ")[1].split("🗓")[0])
    await state.set_state(UploadPhotoForm.summ)
    await state.update_data(summ_mer=txt.split(" в размере ")[1].split(", ")[0])
    await state.set_state(UploadPhotoForm.org)
    await state.update_data(
        org_mer=txt.split("Дополнительная информация о мероприятии: ")[1].split(
            "\n\nПожалуйста, оплатите мероприятие суммой в размере "
        )[0]
    )
    await callback_query.answer("Пришлите, пожалуйста, скрин-подтверждение")
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="Пришлите, пожалуйста, скрин-подтверждение",
    )
    await state.set_state(UploadPhotoForm.photo)


# Перессылка админам
@other_router.message(UploadPhotoForm.photo, filters.photo, filters.text)
async def process_photo(message: types.Message, state: FSMContext):
    if message.content_type == "photo":
        user_data = await state.get_data()
        print(user_data)
        await state.finish()

        temp_fio = db.connection.execute(
            "SELECT * FROM parents WHERE tgID=?", (message.from_user.id,)
        ).fetchone()
        name_group = user_data["grpss"]
        admins = db.connection.execute(
            "SELECT * FROM admins where groups=?", (name_group,)
        ).fetchall()

        FIO = (
            f"Мероприятие: {user_data['namee_mer']}\nДата: {user_data['datee_mer']}\nСумма: {user_data['summ_mer']}\nДополнительная информация: {user_data['org_mer']}\nОплативший: "
            + temp_fio[2]
            + " "
            + temp_fio[3]
            + f"\nUsername: {temp_fio[7]}"
        )
        for ad in admins:
            await bot.send_photo(
                chat_id=ad[1], photo=message.photo[0].file_id, caption=FIO
            )
        await state.finish()
        db.connection.execute(
            "UPDATE active_events SET paid=? WHERE tgID=? and namee=? and datee=? and org=? and summ=? and groups=?",
            (
                "True",
                message.from_user.id,
                user_data["namee_mer"],
                user_data["datee_mer"],
                user_data["org_mer"],
                user_data["summ_mer"],
                name_group,
            ),
        )
        db.connection.commit()
        await message.answer(
            "Спасибо за подтверждение оплаты!\nДанный скриншот был отправлен организатору мероприятия!"
        )

    else:
        await message.answer(
            "Скрина-подтверждения не замечено, пришлите, пожалуйста, скрин-подтверждение!"
        )


# Вывод всех записанных мероприятий из БД
@other_router.message(Command("events"))  # and message.chat.type == 'private'
async def all_events_command(message: types.Message):
    exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
    my_ev = InlineKeyboardButton(text="Мои события", callback_data="myevents")
    profile = InlineKeyboardButton(text="Мой профиль", callback_data="back_to_profile")
    kb = InlineKeyboardMarkup(inline_keyboard=[[my_ev, profile], [exit]])
    kb_arr = []
    gr = set(
        db.connection.execute(
            "select groups from parents where tgID=?", (message.from_user.id,)
        ).fetchall()
    )

    mers = []
    for grp in gr:
        ev = db.connection.execute(
            "SELECT * FROM Event where groups = ? ", (grp[0],)
        ).fetchall()
        for e in ev:
            mers.append(e)
    out = ""
    cnt = 1
    flag = False
    if len(mers) == 0:
        flag = True
    for e in mers:
        if len(e) == 0:
            flag = True
            break
        kb_arr.append(InlineKeyboardButton(text=f"{e[2]}", callback_data=f"{e[6]}"))
        out += f"{cnt} мероприятие:\n\t\tДата мероприятия: {e[1]}\n\t\tНазвание мероприятия: {e[2]}\n\t\tДополнительная информация: {e[3]}\n\t\tСумма с каждого: {e[4]}\n\n"
        cnt += 1
    print(flag)
    if flag:
        kb = InlineKeyboardMarkup(inline_keyboard=[[profile, exit]])
        await message.answer(
            text="Пока мероприятий нет, но скоро они здесь появятся!",
            reply_markup=kb,
        )
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[[kb_arr], [profile, exit]])
        await message.answer(out, reply_markup=kb)


# Мои ивенты - ивенты в которых я участвую
@other_router.message(
    filters.text, ChatTypeFilter(chat_type=["private"]), Command("myevents")
)
async def my_events_command(message: types.Message):
    kb = InlineKeyboardMarkup()
    exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
    profile = InlineKeyboardButton(text="Мой профиль", callback_data="back_to_profile")
    all_ev = InlineKeyboardButton(text="Все события", callback_data="allevents")
    my_ev = []
    kb_arr = []

    try:
        gr = db.connection.execute(
            "select groups from parents where tgID=?", (message.from_user.id,)
        ).fetchone()[0]
    except:
        await message.answer("Не нашел вас в списке зарегистрированных пользователей")
        return 0

    my_ev_temp = [
        x[0]
        for x in db.connection.execute(
            "select namee from active_events where tgID=? and groups=? and particip=?",
            (message.from_user.id, gr, "True"),
        ).fetchall()
    ]
    for i in my_ev_temp:
        appended = db.connection.execute(
            "select * from Event where groups=? and namee=?", (gr, i)
        ).fetchone()
        my_ev.append(appended)
    out = "ВАШИ МЕРОПРИЯТИЯ:\n\n"
    cnt = 1
    for e in my_ev:
        kb_arr.append(InlineKeyboardButton(text=f"{e[2]}", callback_data=f"my_{e[6]}"))
        if (
            db.connection.execute(
                "select paid from active_events where tgID=? and groups=? and particip=? and namee=? and datee=? and org=? and summ=?",
                (message.from_user.id, gr, "True", e[2], e[1], e[3], e[4]),
            ).fetchone()[0]
            == "True"
        ):
            out += f"{cnt} мероприятие - Оплачено✅:\n\t\t1️⃣Дата мероприятия: {e[1]}\n\t\t2️⃣Название мероприятия: {e[2]}\n\t\t3️⃣Дополнительная информация: {e[3]}\n\t\t4️⃣Сумма с каждого: {e[4]}\n\n"
        elif (
            db.connection.execute(
                "select paid from active_events where tgID=? and groups=? and particip=? and namee=? and datee=? and org=? and summ=?",
                (message.from_user.id, gr, "True", e[2], e[1], e[3], e[4]),
            ).fetchone()[0]
            == "False"
        ):
            out += f"{cnt} мероприятие - Не оплачено❌:\n\t\t1️⃣Дата мероприятия: {e[1]}\n\t\t2️⃣Название мероприятия: {e[2]}\n\t\t3️⃣Дополнительная информация: {e[3]}\n\t\t4️⃣Сумма с каждого: {e[4]}\n\n"
        cnt += 1
    kb = InlineKeyboardMarkup(inline_keyboard=[[kb_arr], [all_ev], [profile, exit]])
    await message.answer(out, reply_markup=kb)
    # except aiogram.error():
    #     await message.answer(
    #         "Вы не участвуете ни в одном из мероприятий.",
    #         reply_markup=kb.add(profile, all_ev).add(exit),
    #     )
    #     return 0


# Мой профиль
@other_router.message(
    filters.text, ChatTypeFilter(chat_type=["private"]), Command("profile")
)
async def profile(message: types.Message):
    try:
        F = db.connection.execute(
            "select last_name from parents where tgID=?", (message.from_user.id,)
        ).fetchone()[0]
    except:
        F = "Не указано"
    try:
        I = db.connection.execute(
            "select first_name from parents where tgID=?", (message.from_user.id,)
        ).fetchone()[0]
    except:
        I = "Не указано"

    gr = set(
        db.connection.execute(
            "select groups from active_events where tgID=?", (message.from_user.id,)
        ).fetchall()
    )
    exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
    my_ev = InlineKeyboardButton(text="Мои события", callback_data="myevents")
    all_ev = InlineKeyboardButton(text="Все события", callback_data="allevents")
    change_FIO = InlineKeyboardButton(
        text="Сменить Фамилию и/или Имя", callback_data="startRegister"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[my_ev, all_ev], [change_FIO], [exit]])

    ln = 0
    for g in gr:
        ln += len(
            db.connection.execute(
                "select * from Event where groups=?", (g[0],)
            ).fetchall()
        )
    await message.answer(
        f"Фамилия: {F}\n"
        f"Имя: {I}\n"
        f"Username: @{message.from_user.username}\n"
        f"==========\n"
        f'Кол-во мероприятий, где вы участвуете: {len(db.connection.execute("select * from active_events where tgID=? and particip=?", (message.from_user.id, "True")).fetchall())}\n'
        f"Кол-во мероприятий, доступные вам: {ln}\n"
        f'✅Оплачено мероприятий, в которых вы участвуете: {len(db.connection.execute("select * from active_events where tgID=? and paid=?", (message.from_user.id, "True")).fetchall())}\n'
        f'❌Не оплачено мероприятий, в которых вы участвуете: {len(db.connection.execute("select * from active_events where tgID=? and paid=?", (message.from_user.id, "False")).fetchall())}',
        reply_markup=kb,
    )


# вывод моих событий через профиль
@other_router.callback_query(lambda call: call.data == "myevents")
async def startRegister(callback_query: types.CallbackQuery):
    exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
    bck = InlineKeyboardButton(text="Мой профиль", callback_data="back_to_profile")
    all_ev = InlineKeyboardButton(text="Все события", callback_data="allevents")
    kb = InlineKeyboardMarkup(inline_keyboard=[[bck], [exit]])
    kb_arr = []
    my_ev = []

    try:
        gr = set(
            db.connection.execute(
                "select groups from active_events where tgID=?",
                (callback_query.from_user.id,),
            ).fetchall()
        )
    except:
        await callback_query.message.edit_text(
            text="Не нашел вас в списке зарегистрированных пользователей",
            reply_markup=kb,
        )
        return 0

    my_ev_temp = [
        x[0]
        for x in db.connection.execute(
            "select namee from active_events where tgID=? and particip=?",
            (callback_query.from_user.id, "True"),
        ).fetchall()
    ]
    for j in gr:
        for i in my_ev_temp:
            appended = db.connection.execute(
                "select * from Event where groups=? and namee=?", (j[0], i)
            ).fetchone()
            if appended is None:
                continue
            my_ev.append(appended)

    out = "ВАШИ МЕРОПРИЯТИЯ:\n\n"
    cnt = 1

    for e in my_ev:
        kb_arr.append(InlineKeyboardButton(text=f"{e[2]}", callback_data=f"my_{e[6]}"))

        if (
            db.connection.execute(
                "select paid from active_events where tgID=? and particip=? and namee=? and datee=? and org=? and summ=?",
                (callback_query.from_user.id, "True", e[2], e[1], e[3], e[4]),
            ).fetchone()[0]
            == "True"
        ):
            out += f"{cnt} мероприятие - Оплачено✅:\n\t\t1️⃣Дата мероприятия: {e[1]}\n\t\t2️⃣Название мероприятия: {e[2]}\n\t\t3️⃣Дополнительная информация: {e[3]}\n\t\t4️⃣Сумма с каждого: {e[4]}\n\n"
        elif (
            db.connection.execute(
                "select paid from active_events where tgID=? and particip=? and namee=? and datee=? and org=? and summ=?",
                (callback_query.from_user.id, "True", e[2], e[1], e[3], e[4]),
            ).fetchone()[0]
            == "False"
        ):
            out += f"{cnt} мероприятие - Не оплачено❌:\n\t\t1️⃣Дата мероприятия: {e[1]}\n\t\t2️⃣Название мероприятия: {e[2]}\n\t\t3️⃣Дополнительная информация: {e[3]}\n\t\t4️⃣Сумма с каждого: {e[4]}\n\n"
        cnt += 1

    if out == "ВАШИ МЕРОПРИЯТИЯ:\n\n":
        kb = InlineKeyboardMarkup(inline_keyboard=[[all_ev], [bck, exit]])
        await callback_query.message.edit_text(
            text="Вы не участвуете ни в одном из мероприятий.", reply_markup=kb
        )
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[[kb_arr][all_ev], [bck, exit]])
        await callback_query.message.edit_text(text=out, reply_markup=kb)


# вывод всех событий через профиль
@other_router.callback_query(lambda call: call.data == "allevents")
async def startRegister(callback_query: types.CallbackQuery):
    exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
    bck = InlineKeyboardButton(text="Мой профиль", callback_data="back_to_profile")
    my_ev = InlineKeyboardButton(text="Мои события", callback_data="myevents")
    kb_arr = []
    gr = set(
        db.connection.execute(
            "select groups from parents where tgID=?", (callback_query.from_user.id,)
        ).fetchall()
    )

    mers = []
    for grp in gr:
        ev = db.connection.execute(
            "SELECT * FROM Event where groups = ? ", (grp[0],)
        ).fetchall()
        for e in ev:
            mers.append(e)
    out = "ВСЕ МЕРОПРИЯТИЯ:\n\n"
    cnt = 1
    for e in mers:
        btn = InlineKeyboardButton(text=f"{e[2]}", callback_data=f"{e[6]}")
        kb_arr.append(btn)
        out += f"{cnt} мероприятие:\n\t\t1️⃣Дата мероприятия: {e[1]}\n\t\t2️⃣Название мероприятия: {e[2]}\n\t\t3️⃣Дополнительная информация: {e[3]}\n\t\t4️⃣Сумма с каждого: {e[4]}\n\n"
        cnt += 1
    if len(kb_arr) == 0:
        kb = InlineKeyboardMarkup(inline_keyboard=[[bck, my_ev], [exit]])
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[[kb_arr], [bck, my_ev], [exit]])
    await callback_query.message.edit_text(out, reply_markup=kb)


# обратно в профиль
@other_router.callback_query(lambda call: call.data == "back_to_profile")
async def startRegister(callback_query: types.CallbackQuery):
    F = db.connection.execute(
        "select last_name from parents where tgID=?", (callback_query.from_user.id,)
    ).fetchone()[0]
    I = db.connection.execute(
        "select first_name from parents where tgID=?",
        (callback_query.from_user.id,),
    ).fetchone()[0]
    gr = set(
        db.connection.execute(
            "select groups from active_events where tgID=?",
            (callback_query.from_user.id,),
        ).fetchall()
    )
    exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
    my_ev = InlineKeyboardButton(text="Мои события", callback_data="myevents")
    all_ev = InlineKeyboardButton(text="Все события", callback_data="allevents")
    change_FIO = InlineKeyboardButton(
        text="Сменить Фамилию и/или Имя", callback_data="startRegister"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[my_ev, all_ev], [change_FIO], [exit]])
    ln = 0
    for g in gr:
        ln += len(
            db.connection.execute(
                "select * from Event where groups=?", (g[0],)
            ).fetchall()
        )

    await callback_query.message.edit_text(
        f"Фамилия: {F}\n"
        f"Имя: {I}\n"
        f"Username: @{callback_query.from_user.username}\n"
        f"==========\n"
        f'Кол-во событий, где вы участвуете: {len(db.connection.execute("select * from active_events where tgID=? and particip=?", (callback_query.from_user.id, "True")).fetchall())}\n'
        f"Кол-во событий, доступные вам: {ln}\n"
        f'✅Оплачено мероприятий, в которых вы участвуете: {len(db.connection.execute("select * from active_events where tgID=? and paid=?", (callback_query.from_user.id, "True")).fetchall())}\n'
        f'❌Не оплачено мероприятий, в которых вы участвуете: {len(db.connection.execute("select * from active_events where tgID=? and paid=?", (callback_query.from_user.id, "False")).fetchall())}',
        reply_markup=kb,
    )


# Выход из сообщения
@other_router.callback_query(lambda call: call.data == "exit")
async def exit(callback_query: types.CallbackQuery):
    await callback_query.answer("Закрываю.")
    asyncio.create_task(delete_message(callback_query.message, 0))


# Вывод какого то "моего" ивента
@other_router.callback_query(
    lambda call: call.data
    == "myEvent"
    in [
        "my_" + x[0]
        for x in db.connection.execute("select eventID from Event").fetchall()
    ]
)
async def react_ev(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Получаю информацию о мероприятии...")

    if (
        db.connection.execute(
            "select * from admins where tgID=?", (callback_query.from_user.id,)
        ).fetchone()
        is not None
    ):
        kb = InlineKeyboardMarkup()
        exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
        bck = InlineKeyboardButton(text="Мои события", callback_data="back_my_ev")
        all_ev = InlineKeyboardButton(text="Все события", callback_data="allevents")
        ras = InlineKeyboardButton(text="Разослать", callback_data="хочу_разослать")
        uch = InlineKeyboardButton(text="Участвую", callback_data="Участвую")
        neuch = InlineKeyboardButton(text="Не участвую", callback_data="Не участвую")
        spisok = InlineKeyboardButton(
            text="Список участников", callback_data="Список участников"
        )
        change = InlineKeyboardButton(
            text="Изменить событие(не работает)", callback_data="Изменить событие"
        )
        remove = InlineKeyboardButton(
            text="Удалить событие(не работает)", callback_data="Удалить событие"
        )
        gr = db.connection.execute(
            "select groups from admins where tgID=?", (callback_query.from_user.id,)
        ).fetchone()[0]
        q = db.connection.execute(
            f"select * from Event where eventID=?",
            (callback_query.data.replace("my_", "", 1),),
        ).fetchone()
        pad = db.connection.execute(
            "select paid from active_events where tgID=? and namee=? "
            "and datee=? and org=? and summ=?",
            (callback_query.from_user.id, q[2], q[1], q[3], q[4]),
        ).fetchone()[0]
        grp = db.connection.execute(
            "select groups from Event where eventID=?",
            (callback_query.data.replace("my_", "", 1),),
        ).fetchone()[0]

        paid = InlineKeyboardButton(text="Оплатить", callback_data=f"paid_myev_{grp}")
        if pad == "True":
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[ras, spisok], [uch, neuch], [all_ev], [bck, exit]]
            )

            await callback_query.message.edit_text(
                text=f"1️⃣Дата мероприятия: {q[1]}\n"
                f"2️⃣Название мероприятия: {q[2]}\n"
                f"3️⃣Дополнительная информация: {q[3]}\n"
                f"4️⃣Сумма с каждого: {q[4]}\n"
                f"5️⃣Статус: Оплачено✅",
                reply_markup=kb,
            )
        else:
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[uch, neuch], [spisok, paid], [bck, exit], [all_ev]]
            )
            await callback_query.message.edit_text(
                text=f"1️⃣Дата мероприятия: {q[1]}\n"
                f"2️⃣Название мероприятия: {q[2]}\n"
                f"3️⃣Дополнительная информация: {q[3]}\n"
                f"4️⃣Сумма с каждого: {q[4]}\n"
                f"5️⃣Статус: Не оплачено❌",
                reply_markup=kb,
            )

    else:
        kb = InlineKeyboardMarkup()
        exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
        bck = InlineKeyboardButton(text="Мои события", callback_data="back_my_ev")
        all_ev = InlineKeyboardButton(text="Все события", callback_data="allevents")
        uch = InlineKeyboardButton(text="Участвую", callback_data="Участвую")
        neuch = InlineKeyboardButton(text="Не участвую", callback_data="Не участвую")
        spisok = InlineKeyboardButton(
            text="Список участников", callback_data="Список участников"
        )
        q = db.connection.execute(
            f"select * from Event where eventID=?",
            (callback_query.data.replace("my_", "", 1),),
        ).fetchone()
        gr = db.connection.execute(
            "select groups from parents where tgID=?",
            (callback_query.from_user.id,),
        ).fetchone()[0]
        pad = db.connection.execute(
            "select paid from active_events where tgID=? and namee=? "
            "and datee=? and org=? and summ=?",
            (callback_query.from_user.id, q[2], q[1], q[3], q[4]),
        ).fetchone()[0]
        grp = db.connection.execute(
            "select groups from Event where eventID=?",
            (callback_query.data.replace("my_", "", 1),),
        ).fetchone()[0]

        paid = InlineKeyboardButton(text="Оплатить", callback_data=f"paid_myev_{grp}")
        if pad == "True":
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[spisok], [uch, neuch], [all_ev], [bck, exit]]
            )
            await callback_query.message.edit_text(
                text=f"1️⃣Дата мероприятия: {q[1]}\n"
                f"2️⃣Название мероприятия: {q[2]}\n"
                f"3️⃣Дополнительная информация: {q[3]}\n"
                f"4️⃣Сумма с каждого: {q[4]}\n"
                f"5️⃣Статус: Оплачено✅",
                reply_markup=kb,
            )
        else:
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[spisok, paid], [uch, neuch], [all_ev], [bck, exit]]
            )
            await callback_query.message.edit_text(
                text=f"1️⃣Дата мероприятия: {q[1]}\n"
                f"2️⃣Название мероприятия: {q[2]}\n"
                f"3️⃣Дополнительная информация: {q[3]}\n"
                f"4️⃣Сумма с каждого: {q[4]}\n"
                f"5️⃣Статус: Не оплачено❌",
                reply_markup=kb,
            )


@other_router.callback_query(lambda call: "paid_myev_" in call.data)
async def paid_mer(callback_query: types.CallbackQuery, state: FSMContext):
    txt = callback_query.message.text
    await state.set_state(UploadPhotoForm.grps)
    await state.update_data(grpss=callback_query.data.split("paid_myev_")[1])
    await state.set_state(UploadPhotoForm.mer)
    await state.update_data(namee_mer=txt.split("\n")[1].split(": ")[1])
    await state.set_state(UploadPhotoForm.dat)
    await state.update_data(datee_mer=txt.split("\n")[0].split(": ")[1])
    await state.set_state(UploadPhotoForm.summ)
    await state.update_data(summ_mer=txt.split("\n")[3].split(": ")[1])
    await state.set_state(UploadPhotoForm.org)
    await state.update_data(org_mer=txt.split("\n")[2].split(": ")[1])
    await callback_query.answer("Пришлите, пожалуйста, скрин-подтверждение")
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="Пришлите, пожалуйста, скрин-подтверждение",
    )
    await state.set_state(UploadPhotoForm.photo)


# Возврат в список всех моих ивентов
@other_router.callback_query(lambda call: call.data == "back_my_ev")
async def spisok_pers(callback_query: types.CallbackQuery):
    kb = InlineKeyboardMarkup()
    exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
    bck = InlineKeyboardButton(text="Мой профиль", callback_data="back_to_profile")
    all_ev = InlineKeyboardButton(text="Все события", callback_data="allevents")
    my_ev = []
    add_btn = []
    try:
        gr = set(
            db.connection.execute(
                "select groups from active_events where tgID=?",
                (callback_query.from_user.id,),
            ).fetchall()
        )
    except:
        kb = InlineKeyboardMarkup(inline_keyboard=[[bck], [exit]])

        await callback_query.message.edit_text(
            text="Не нашел вас в списке зарегистрированных пользователей",
            reply_markup=kb,
        )
        return 0

    my_ev_temp = [
        x[0]
        for x in db.connection.execute(
            "select namee from active_events where tgID=? and particip=?",
            (callback_query.from_user.id, "True"),
        ).fetchall()
    ]
    for j in gr:
        for i in my_ev_temp:
            appended = db.connection.execute(
                "select * from Event where groups=? and namee=?", (j[0], i)
            ).fetchone()
            if appended is None:
                continue
            my_ev.append(appended)

    out = "ВАШИ МЕРОПРИЯТИЯ:\n\n"
    cnt = 1

    for e in my_ev:
        add_btn.append(InlineKeyboardButton(text=f"{e[2]}", callback_data=f"my_{e[6]}"))
        if (
            db.connection.execute(
                "select paid from active_events where tgID=? and particip=? and namee=? and datee=? and org=? and summ=?",
                (callback_query.from_user.id, "True", e[2], e[1], e[3], e[4]),
            ).fetchone()[0]
            == "True"
        ):
            out += f"{cnt} мероприятие - Оплачено✅:\n\t\t1️⃣Дата мероприятия: {e[1]}\n\t\t2️⃣Название мероприятия: {e[2]}\n\t\t3️⃣Дополнительная информация: {e[3]}\n\t\t4️⃣Сумма с каждого: {e[4]}\n\n"
        elif (
            db.connection.execute(
                "select paid from active_events where tgID=? and particip=? and namee=? and datee=? and org=? and summ=?",
                (callback_query.from_user.id, "True", e[2], e[1], e[3], e[4]),
            ).fetchone()[0]
            == "False"
        ):
            out += f"{cnt} мероприятие - Не оплачено❌:\n\t\t1️⃣Дата мероприятия: {e[1]}\n\t\t2️⃣Название мероприятия: {e[2]}\n\t\t3️⃣Дополнительная информация: {e[3]}\n\t\t4️⃣Сумма с каждого: {e[4]}\n\n"
        cnt += 1

    if out == "ВАШИ МЕРОПРИЯТИЯ:\n\n":
        kb = InlineKeyboardMarkup(inline_keyboard=[[add_btn, all_ev], [bck, exit]])
        await callback_query.message.edit_text(
            text="Вы не участвуете ни в одном из мероприятий.", reply_markup=kb
        )
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[[add_btn, all_ev], [bck, exit]])
        await callback_query.message.edit_text(text=out, reply_markup=kb)


# После выбора мероприятия для рассылки
@other_router.callback_query(
    lambda call: call.data
    == "rassilka"
    in [x[0] for x in db.connection.execute("select eventID from Event").fetchall()]
)
async def react_ev(callback_query: types.CallbackQuery):
    await callback_query.answer("Получаю информацию о мероприятии...")
    q = db.connection.execute(
        f"select * from Event where eventID=?", (callback_query.data,)
    ).fetchone()

    if (
        db.connection.execute(
            "select * from admins where tgID=?", (callback_query.from_user.id,)
        ).fetchone()
        is not None
    ):
        kb = InlineKeyboardMarkup()
        exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
        profile = InlineKeyboardButton(
            text="Мой профиль", callback_data="back_to_profile"
        )
        all_ev = InlineKeyboardButton(text="Все события", callback_data="allevents")
        my_ev = InlineKeyboardButton(text="Мои события", callback_data="myevents")
        ras = InlineKeyboardButton(text="Разослать", callback_data="хочу_разослать")
        uch = InlineKeyboardButton(text="Участвую", callback_data="Участвую")
        neuch = InlineKeyboardButton(text="Не участвую", callback_data="Не участвую")
        spisok = InlineKeyboardButton(
            text="Список участников", callback_data="Список участников"
        )
        change = InlineKeyboardButton(
            text="Изменить событие(не работает)", callback_data="Изменить событие"
        )
        remove = InlineKeyboardButton(
            text="Удалить событие(не работает)", callback_data="Удалить событие"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [ras, spisok],
                [uch, neuch],
                [my_ev, all_ev],
                [profile, exit],
            ]
        )
        await callback_query.message.edit_text(
            text=f"1️⃣Дата мероприятия: {q[1]}\n"
            f"2️⃣Название мероприятия: {q[2]}\n"
            f"3️⃣Дополнительная информация: {q[3]}\n"
            f"4️⃣Сумма с каждого: {q[4]}\n",
            reply_markup=kb,
        )
    else:
        kb = InlineKeyboardMarkup()
        uch = InlineKeyboardButton(text="Участвую", callback_data="Участвую")
        neuch = InlineKeyboardButton(text="Не участвую", callback_data="Не участвую")
        exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
        profile = InlineKeyboardButton(
            text="Мой профиль", callback_data="back_to_profile"
        )
        all_ev = InlineKeyboardButton(text="Все события", callback_data="allevents")
        my_ev = InlineKeyboardButton(text="Мои события", callback_data="myevents")
        spisok = InlineKeyboardButton(
            text="Список участников", callback_data="Список участников"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[spisok], [uch, neuch], [my_ev, all_ev], [profile, exit]]
        )
        await callback_query.message.edit_text(
            text=f"1️⃣Дата мероприятия: {q[1]}\n"
            f"2️⃣Название мероприятия: {q[2]}\n"
            f"3️⃣Дополнительная информация: {q[3]}\n"
            f"4️⃣Сумма с каждого: {q[4]}\n",
            reply_markup=kb,
        )


# Вывод списка участников какого-либо мероприятия
@other_router.callback_query(lambda call: call.data == "Список участников")
async def spisok_pers(callback_query: types.CallbackQuery):
    await callback_query.answer("Предоставляю список участников...")

    kb = InlineKeyboardMarkup()
    exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
    profile = InlineKeyboardButton(text="Мой профиль", callback_data="back_to_profile")
    all_ev = InlineKeyboardButton(text="Все события", callback_data="allevents")
    my_ev = InlineKeyboardButton(text="Мои события", callback_data="myevents")
    await callback_query.answer("Предоставляю список участников!")
    dat = callback_query.message.text.split("\n")[0].split(": ")[1]
    mer = callback_query.message.text.split("\n")[1].split(": ")[1]
    org = callback_query.message.text.split("\n")[2].split(": ")[1]
    summ = callback_query.message.text.split("\n")[3].split(": ")[1]
    all_pers = db.connection.execute(
        "select * from active_events where namee=? and datee=? and org=? and summ=? and particip=?",
        (mer, dat, org, summ, "True"),
    ).fetchall()
    out = f'В мероприятии "{mer}" участвуют следующие лица:\n'
    cnt = 1
    for pers in all_pers:
        if pers[6] == "True":
            out += f"{cnt}) {pers[4]} - Оплачено✅\n"
        else:
            out += f"{cnt}) {pers[4]} - Не оплачено❌\n"
        cnt += 1
    kb = InlineKeyboardMarkup(inline_keyboard=[[my_ev, all_ev], [profile, exit]])

    if out == f'В мероприятии "{mer}" участвуют следующие лица:\n':
        await callback_query.message.edit_text(
            text="В данном мероприятии пока не участвует ни один человек",
            reply_markup=kb,
        )
    else:
        await callback_query.message.edit_text(text=out, reply_markup=kb)


# # Удаление сообщений - (сообщение, через сколько удалить)
async def delete_message(message: types.Message, sleep_time: int = 0):
    await asyncio.sleep(sleep_time)
    await message.delete()


@other_router.message(
    filters.text, ChatTypeFilter(chat_type=["private"]), Command("news")
)
async def news(message: types.Message):
    try:
        gr = db.connection.execute(
            "select groups from admins where tgID=?", (message.from_user.id,)
        ).fetchone()[0]
        data = set(
            db.connection.execute(
                "SELECT groupID FROM parents where groups=? and tgID=?",
                (gr, message.from_user.id),
            ).fetchall()
        )
        exit = InlineKeyboardButton(text="Закрыть", callback_data="exit")
        await message.answer(f"{message.text}", reply_markup=genmarkup(data).add(exit))
        asyncio.create_task(delete_message(message, 0))
    except:
        await message.answer("У вас нет прав на использование этой команды!")
