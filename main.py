import logging
import sqlite3
import aiogram.utils.exceptions
import aiogram.utils.markdown as md
import asyncio
from aiogram.types import (ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton,
						   InlineKeyboardButton, InlineKeyboardMarkup)
from contextlib import suppress
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import (MessageToEditNotFound, MessageCantBeEdited, MessageCantBeDeleted,
                                      MessageToDeleteNotFound)
import fix_file

#Исправить username( есть не у всех), также возможность дублировать добавление /add мероприятий


# АПИ ТОКЕН
API_TOKEN = '6356019230:AAE8KnskdGCIGw9M1tRVL7tgJVBCNPKW-zA'

# БД - основная
conn_u = sqlite3.connect("events.db")
c_u = conn_u.cursor()

# Логирование
logging.basicConfig(level=logging.INFO)

# подключаем бота
bot = Bot(token = API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Секрет-слово или секрет-фраза для получения админки
@dp.message_handler(lambda message: message.text.lower() == 'админами не становятся - админами рождаются!')
async def Russia_become_the_admin(message: types.Message):
	gr = c_u.execute('select groups from admins').fetchall()
	if gr == []:
		gr = 'group_1'
	else:
		gr1 = sorted([int(x[0].split('_')[1]) for x in c_u.execute('select groupss from admins').fetchall()])
		gr = 'group_' + str(gr1[-1]+1)
	if c_u.execute('select * from admins where tgID=?', (message.from_user.id, )).fetchone() is None:
		c_u.execute('insert into admins (groups, tgID) values ("{}", {})'.format(gr, message.from_user.id))
		conn_u.commit()
		await message.answer('О Великий админ, премного благодарен, что вы с нами!')
		c_u.execute('INSERT INTO parents (groups, tgID, last_name, first_name, groupID, organisator, nickname, username) '
					'VALUES ("{}", {}, "{}", "{}", {}, "{}", "{}", "{}")'
					''.format(gr, message.from_user.id, 'None', 'None', 0, 'True', message.from_user.first_name, "@"+message.from_user.username))
		conn_u.commit()
		kb = InlineKeyboardMarkup()
		ready = InlineKeyboardButton(text = 'Готов(а)✅', callback_data = 'Ready_for_register')
		await message.answer(
							   text = 'Для регистрации в данном боте будет необходимо указать свои Фамилию и Имя. Как будете готовы нажмите на кнопку под сообщением "Готов(а)"!',
							   reply_markup = kb.add(ready))
	else:
		await message.answer('О Великий админ, как бы ни было прискорбно, но вы не можете стать админом дважды!')

# Параметры мероприятия
class Params_event(StatesGroup):
	choosing_name_event = State()
	mes1 = State()
	choosing_date = State()
	mes2 = State()
	choosing_sum = State()
	mes3 = State()
	choosing_whom = State()
	mes4 = State()

# Параметры ФИО родителей
class FIO(StatesGroup):
	mes = State()
	f = State()
	i = State()

# Cкрины-подтверждения
class UploadPhotoForm(StatesGroup):
    photo = State()
    mer = State()
    dat = State()
    org = State()
    summ = State()

# ИСПРАВИТЬ ВОЗМОЖНОЕ ОТСУТСТВИЕ USERNAME!
# Реакция на добавление бота в группу
@dp.message_handler(content_types = ['new_chat_members'])
async def send_welcome(message: types.Message):
	kb = InlineKeyboardMarkup()
	reg = InlineKeyboardButton('Зарегистрироваться✅', callback_data = 'rgstr')
	org = InlineKeyboardButton('Организаторы🛂', callback_data = 'organisators')
	bot_obj = await bot.get_me()
	bot_id = bot_obj.id
	for chat_member in message.new_chat_members:
		if chat_member.id == bot_id:
			gr = c_u.execute('select groups from admins where tgID=?', (message.from_user.id,)).fetchone()[0]
			q = """INSERT INTO groups (groups, groupID, groupTitle) VALUES ('{}', {}, '{}') """
			c_u.execute(q.format(gr, message.chat.id, message.chat.title))
			conn_u.commit()


			_users = await fix_file.vecher_v_hatu(message.chat.id)
			for us in _users:
				exist_parent = c_u.execute('select * from parents where tgID=?', (us[0],)).fetchone()

				if exist_parent is not None:

					if c_u.execute('select * from parents where groups=? and tgID=? and username=? and nickname=? and groupID=?', (gr, us[0], us[2], us[1], message.chat.id)).fetchone() is None:
						if c_u.execute('select groupID from parents where groups=? and tgID=? and username=? and nickname=?', (gr, us[0], us[2], us[1])).fetchone() == 0:
							c_u.execute('update parents set groupID=? where groups=? and tgID=? and username=? and nickname=?', (message.chat.id, gr, us[0], us[2], us[1]))
							conn_u.commit()
						else:
							q2 = c_u.execute('insert into parents (groups, tgID, last_name, first_name, groupID, organisator, nickname, username) '
											 'values ("{}", {}, "{}", "{}", {}, "{}", "{}", "{}")'.format(gr, us[0], exist_parent[2], exist_parent[3], message.chat.id, "False", us[1], us[2]))
							conn_u.commit()
				else:
					if c_u.execute('select * from parents where groups=? and tgID=? and username=? and nickname=? and groupID=?', (gr, us[0], us[2], us[1], message.chat.id)).fetchone() is None:

						q2 = c_u.execute('insert into parents (groups, tgID, last_name, first_name, groupID, organisator, nickname, username) '
										 'values ("{}", {}, "{}", "{}", {}, "{}", "{}", "{}")'.format(gr, us[0], 'None', 'None', message.chat.id, "False", us[1], us[2]))
						conn_u.commit()

			await message.answer(f'🚩Доброго времени суток, участники беседы "{message.chat.title}"!👋\n\n'
								 f'Я бот🤖, созданный для организации мероприятий. Если меня добавили сюда, '
								 f'значит один или несколько из участников этой беседы хотят упростить себе жизнь, для чего именно я и был создан!\n\n'
								 f'Если вы будете принимать участие в мероприятиях, в таком случае вам необходимо выполнить несколько последовательных действий:\n\n'
								 f'1️⃣) Активировать меня, зайдя в личные сообщения со мной(если вы еще этого не делали).\n'
								 f'2️⃣) Нажать кнопку под данным сообщением "Зарегистрироваться✅" для того, чтобы я вас мог зарегистрировать.\n'
								 f'3️⃣) После чего я напишу вам сообщение, где вы закончите регистрацию в данном боте.\n\n'
								 f'Делается это для того, чтобы организаторам мероприятий было проще: понимать, кто участвует, оплатил мероприятие или связаться с ними.\n'
								 f'Если же вы уже были зарегистрированы и нажимали данную кнопку под сообщением, но делали это в другой беседе, при этом собираетесь принимать участие от организаторов этой группы, в таком случае без страха нажимайте на кнопку! 🚩',
								 reply_markup = kb.add(reg, org))
		else:
			_users = await fix_file.yopta(message.chat.id)
			gr2 = c_u.execute('select groups from groups where groupID=?', (message.chat.id,)).fetchall()
			for grps in gr2:
				for us in _users:
					if c_u.execute('select * from parents where groups=? and tgID=? and username=? and nickname=? and groupID=?', (grps[0], us[0], us[2], us[1], message.chat.id)).fetchone() is None:
						q2 = c_u.execute('insert into parents (groups, tgID, last_name, first_name, groupID, organisator, nickname, username) '
										 'values ("{}", {}, "{}", "{}", {}, "{}", "{}", "{}")'.format(grps[0], us[0], "None", "None", message.chat.id, "False", us[1], us[2]))
						conn_u.commit()

						await message.reply(f'@{us[2]}\n\n'
											 f'🚩 Приветствую тебя, {us[1]}, новый участник, беседы "{message.chat.title}"!👋\n'
											 f'Я бот🤖, созданный для организации мероприятий и приглашенный одним из организаторов этой беседы!\n'
											 f'Если вы будете принимать участие в мероприятиях, в таком случае вам необходимо выполнить несколько последовательных действий:\n\n'
											 f'1️⃣) Активировать меня, зайдя в личные сообщения со мной(если вы еще этого не делали).\n'
											 f'2️⃣) Нажать кнопку под данным сообщением "Зарегистрироваться✅" для того, чтобы я вас мог зарегистрировать.\n'
											 f'3️⃣) После чего я напишу вам сообщение, где вы закончите регистрацию в данном боте.\n\n'
											 f'Делается это для того, чтобы организаторам мероприятий было проще: понимать, кто участвует, оплатил мероприятие или связаться с ними.\n'
											 f'Если же вы уже были зарегистрированы и нажимали данную кнопку под сообщением, но делали это в другой беседе, при этом собираетесь принимать участие от организаторов этой группы, в таком случае без страха нажимайте на кнопку! 🚩',
											 reply_markup = kb.add(reg, org))

# Регистрация в боте пользователем
@dp.message_handler(lambda message: message.text.lower() == '/register' and message.chat.type == 'private')
async def register_command(message: types.Message):
	kb = InlineKeyboardMarkup()
	ready = InlineKeyboardButton(text = 'Готов(а)', callback_data = 'Ready_for_register')
	await message.answer('Для регистрации в данном боте будет необходимо указать своё Имя, Фамилию и Отчество. Это всё, что потребуется. Как будете готовы нажмите на кнопку под сообщением "Готов(а)"!', reply_markup = kb.add(ready))

# регистрация из стартового сообщения
@dp.callback_query_handler(lambda call: call.data == 'rgstr')
async def register_from_start_message(callback_query: types.CallbackQuery, state: FSMContext):
	grID = callback_query.chat.id
	gr = c_u.execute('select groups from groups where groupID=?', (grID, )).fetchone()[0]
	q1 = """INSERT INTO parents (groups, tgID, last_name, first_name, groupID, organisator, nickname, username) VALUES ('{}', {}, '{}', '{}', {}, '{}', '{}', '{}')"""
	c_u.execute(q1.format(gr, callback_query.from_user.id, None, None, grID, 'False', callback_query.from_user.first_name, callback_query.from_user.username))
	conn_u.commit()
	kb = InlineKeyboardMarkup()
	ready = InlineKeyboardButton(text = 'Готов(а)', callback_data = 'Ready_for_register')
	try:
		await bot.send_message(chat_id = callback_query.from_user.id, text = 'Для регистрации в данном боте будет необходимо указать своё Фамилию и Имя. Это всё, что потребуется. Как будете готовы нажмите на кнопку под сообщением "Готов(а)"!', reply_markup = kb.add(ready))
	except:
		await callback_query.answer('Для начала активируй меня!')

# нажал кнопку готов к регистрации/нажамал кнопку неверное ФИО
@dp.callback_query_handler(lambda call: call.data == 'Ready_for_register')
async def ready_for_register(callback_query: types.CallbackQuery, state: FSMContext):
	asyncio.create_task(delete_message(callback_query.message, 0))
	await bot.send_message(chat_id = callback_query.from_user.id, text = 'Пожалуйста, укажите свою Фамилию!')

	await state.set_state(FIO.f)

# Фамилия
@dp.message_handler(state = FIO.f)
async def get_f_parent(message: types.Message, state: FSMContext):
	await state.update_data(familia = message.text.title())

	await message.answer(f'Ваша Фамилия: {message.text.title()}\n'
						 f'Пожалуйста, укажите своё Имя!')

	await state.set_state(FIO.i)

# Имя
@dp.message_handler(state = FIO.i)
async def get_i_parent(message: types.Message, state: FSMContext):
	await state.update_data(imya = message.text.title())
	user_data = await state.get_data()
	await state.finish()

	kb = InlineKeyboardMarkup()
	yep = InlineKeyboardButton('Верно✅', callback_data = 'right_FIO')
	no = InlineKeyboardButton('Неверно❌', callback_data = 'Ready_for_register')
	await message.answer(f'Ваша Фамилия: {user_data["familia"]}\n'
						 f'Ваше Имя: {message.text.title()}\n'
						 f'Верно ли указаны Фамилия и Имя?', reply_markup = kb.add(yep, no))

# Верно указано ФИО
@dp.callback_query_handler(lambda call: call.data == 'right_FIO')
async def right_fio(callback_query: types.CallbackQuery, state: FSMContext):
	F = callback_query.message.text.split('\n')[0].split(': ')[1]
	I = callback_query.message.text.split('\n')[1].split(': ')[1]
	c_u.execute("UPDATE parents SET last_name=?, first_name=?WHERE tgID=?", (F, I, callback_query.from_user.id))
	conn_u.commit()
	all_FIO = f'{F} {I}'
	c_u.execute("UPDATE active_events SET parent=? WHERE tgID=?", (all_FIO, callback_query.from_user.id))
	conn_u.commit()

	gr = set(c_u.execute('select groups from active_events where tgID=?', (callback_query.from_user.id,)).fetchall())
	kb = InlineKeyboardMarkup()
	my_ev = InlineKeyboardButton(text = 'Мои события', callback_data = 'myevents')
	all_ev = InlineKeyboardButton(text = 'Все события', callback_data = 'allevents')
	change_FIO = InlineKeyboardButton(text = 'Сменить Фамилию и/или Имя', callback_data = 'Ready_for_register')
	ln = 0
	for g in gr:
		ln += len(c_u.execute('select * from Event where groups=?', (g[0],)).fetchall())

	await callback_query.message.edit_text(f'Фамилия: {F}\n'
						 f'Имя: {I}\n'
						 f'==========\n'
						 f'🆔: {callback_query.from_user.id}\n'
						 f'Кол-во мероприятий, где вы участвуете: {len(c_u.execute("select * from active_events where tgID=? and particip=?", (callback_query.from_user.id, "True")).fetchall())}\n'
						 f'Кол-во мероприятий, доступные вам: {ln}\n'
						 f'✅Оплачено мероприятий, в которых вы участвуете: {len(c_u.execute("select * from active_events where tgID=? and paid=?", (callback_query.from_user.id, "True")).fetchall())}\n'
						 f'❌Не оплачено мероприятий, в которых вы участвуете: {len(c_u.execute("select * from active_events where tgID=? and paid=?", (callback_query.from_user.id, "False")).fetchall())}',
						 reply_markup = kb.add(my_ev, all_ev).add(change_FIO))

# вывод организаторов
@dp.callback_query_handler(lambda call: call.data == 'organisators')
async def output_organisators(callback_query: types.CallbackQuery, state: FSMContext):
	try:
		grID = callback_query.message.chat.id
		gr = set(c_u.execute('select groups from groups where groupID=?', (grID,)).fetchall())
		orgs = []
		for i in gr:
			admins_temp = c_u.execute('select tgID from admins where groups=?', (i[0],)).fetchall()
			for j in admins_temp:
				orgs.append(j[0])

		out = 'Организаторы: \n'
		cnt = 1
		for ad in orgs:
			admins = c_u.execute('select * from parents where tgID=?', (ad)).fetchone()
			out += f'{cnt}) {admins[2]} {admins[3]} {admins[4]}\n'
			cnt += 1

		await callback_query.message.edit_text(text = out)
	except:
		await callback_query.message.edit_text(text = 'Не могу найти организаторов, повторите попытку позже')

# стартовая команда
@dp.message_handler(lambda message: message.text == "/start")
async def start_command(message: types.Message):
	cht_id = str(message.chat.id)
	if cht_id[0] == '-':
		kb = InlineKeyboardMarkup()
		reg = InlineKeyboardButton('Зарегистрироваться✅', callback_data = 'rgstr')
		org = InlineKeyboardButton('Организаторы🛂', callback_data = 'organisators')
		await message.answer(f'🚩Доброго времени суток, участники беседы "{message.chat.title}"!👋\n\n'
							 f'Я бот🤖, созданный для организации мероприятий. Если меня добавили сюда, '
							 f'значит один или несколько из участников этой беседы хотят упростить себе жизнь, для чего именно я и был создан!\n\n'
							 f'Если вы будете принимать участие в мероприятиях, в таком случае вам необходимо выполнить несколько последовательных действий:\n\n'
							 f'1️⃣) Активировать меня, зайдя в личные сообщения со мной(если вы еще этого не делали).\n'
							 f'2️⃣) Нажать кнопку под данным сообщением "Зарегистрироваться✅" для того, чтобы я вас мог зарегистрировать.\n'
							 f'3️⃣) После чего я напишу вам сообщение, где вы закончите регистрацию в данном боте.\n\n'
							 f'Делается это для того, чтобы организаторам мероприятий было проще: понимать, кто участвует, оплатил мероприятие или связаться с ними.\n'
							 f'Если же вы уже были зарегистрированы и нажимали данную кнопку под сообщением, но делали это в другой беседе, при этом собираетесь принимать участие от организаторов этой группы, в таком случае без страха нажимайте на кнопку! 🚩',
							 reply_markup = kb.add(reg, org))
	else:
		await message.answer("Приветствую! Теперь я смогу уведомлять тебя о новых событиях. "
							 "А для того, чтобы стать админом и составлять запланированные мероприятия, "
							 "и уведомлять о них участников ваших групп- отправьте мне секретное слово.")

# хелповая команда
@dp.message_handler(lambda message: message.text == "/help")
async def help_command(message: types.Message):
	await message.reply('\t\t\t/add - добавить мероприятие, после его создания, будет предложена рассылка\n\n'
						'\t\t\t/events - увидеть все мероприятия происходящие, начиная с сегодняшнего дня\n\n'
						'\t\t\t/myevents - мероприятия, в которых вы принимаете мероприятия\n\n'
						'\t\t\t/register - регистрация в боте(если вы еще этого не делали)\n\n'
						'\t\t\t/profile - ваш профиль')

# Название мероприятия
@dp.message_handler(lambda message: message.text.lower() == '/add' and message.chat.type == 'private')
async def event_name(message: types.Message, state: FSMContext):
	if c_u.execute('select * from admins where tgID=?', (message.from_user.id, )).fetchone() is None:
		await message.answer('У вас нет прав на выполнение данной команды. Введите, пожалуйста, секретную слово/фразу, чтобы получить доступ!')
		return
	ms1 = await message.answer(
		text = 'Напишите название мероприятия:'
	)
	await state.set_state(Params_event.mes1)
	await state.update_data(mes1 = ms1)
	await state.set_state(Params_event.choosing_name_event)

# Сумма мероприятия
@dp.message_handler(state = Params_event.choosing_name_event)
async def event_sum(message: types.Message, state: FSMContext):
	user_data = await state.get_data()
	await state.update_data(chosen_name_event = message.text.lower())
	asyncio.create_task(delete_message(message, 0))
	asyncio.create_task(delete_message(user_data['mes1'], 0))
	ms2 = await message.answer(
		text = f"Название мероприятия: {message.text.lower()}\n"
			   "Напишите сумму мероприятия с каждого человека:"
	)
	await state.set_state(Params_event.mes2)
	await state.update_data(mes2 = ms2)
	await state.set_state(Params_event.choosing_sum)

# Дата мероприятия --- Сделать валидацию dd.mm.yyyy!!!!
@dp.message_handler(state = Params_event.choosing_sum)
async def event_date(message: types.Message, state: FSMContext):
	user_data = await state.get_data()
	await state.update_data(chosen_sum_event = message.text.lower())
	asyncio.create_task(delete_message(message, 0))
	asyncio.create_task(delete_message(user_data['mes2'], 0))
	ms3 = await message.answer(
		text = f"Название мероприятия: {user_data['chosen_name_event']}\n"
			   f"Сумма мероприятия: {message.text.lower()}\n"
			   f"Напишите дату мероприятия:"

	)
	await state.set_state(Params_event.mes3)
	await state.update_data(mes3 = ms3)
	await state.set_state(Params_event.choosing_date)

# Организатор мероприятия
@dp.message_handler(state = Params_event.choosing_date)
async def event_whom(message: types.Message, state: FSMContext):
	user_data = await state.get_data()
	await state.update_data(chosen_date_event = message.text.lower())
	asyncio.create_task(delete_message(message, 0))
	asyncio.create_task(delete_message(user_data['mes3'], 0))

	ms4 = await message.answer(
		text = f"Название мероприятия: {user_data['chosen_name_event']}\n"
			   f"Сумма мероприятия: {user_data['chosen_sum_event']}\n"
			   f"Дата мероприятия: {message.text.lower()}\n"
			   f"Напишите, кто организатор мероприятия: "

	)
	await state.set_state(Params_event.mes4)
	await state.update_data(mes4 = ms4)
	await state.set_state(Params_event.choosing_whom)

# Вывод мероприятия + запись в БД
@dp.message_handler(state = Params_event.choosing_whom)
async def event_output(message: types.Message, state: FSMContext):
	user_data = await state.get_data()
	keyboard = InlineKeyboardMarkup()
	yeah = InlineKeyboardButton(text = 'Хочу разослать', callback_data = 'хочу_разослать')
	nope = InlineKeyboardButton(text = 'Не хочу рассылать', callback_data = 'не_хочу_разослать')
	asyncio.create_task(delete_message(message, 0))
	asyncio.create_task(delete_message(user_data['mes4'], 0))

	await message.answer(
		text = f"1️⃣Дата мероприятия: {user_data['chosen_date_event']}\n"
			   f"2️⃣Название мероприятия: {user_data['chosen_name_event']}\n"
			   f"3️⃣Организатор: {message.text}\n"
			   f"4️⃣Сумма с каждого: {user_data['chosen_sum_event']}\n",
		reply_markup = keyboard.add(yeah, nope)
	)
	gr = c_u.execute('select groups from admins where tgID=?', (message.from_user.id, )).fetchone()[0]
	q = f"INSERT INTO 'Event' (groups, datee, namee, org, summ, tgID) VALUES ('{gr}', '{user_data['chosen_date_event']}', '{user_data['chosen_name_event']}', '{message.text}', '{user_data['chosen_sum_event']}', {message.from_user.id})"
	c_u.execute(q)
	conn_u.commit()
	await state.finish()

# генератор inline-кнопок для рассылки
def genmarkup(data):
	markup = InlineKeyboardMarkup()
	markup.row_width = 2
	for i in data:
		namee = c_u.execute('select groupTitle from groups where groupID=?', (i[0],)).fetchone()[0]
		markup.add(InlineKeyboardButton(namee, callback_data = str(i[0])))
	return markup

# Соглашение на рассылку ( предложение групп для рассылки )
@dp.callback_query_handler(lambda call: call.data == 'хочу_разослать')
async def choice_rassilka(callback_query: types.CallbackQuery):
	await callback_query.answer('Выбирай куда отсылать')

	gr = c_u.execute('select groups from admins where tgID=?', (callback_query.from_user.id, )).fetchone()[0]
	data = set(c_u.execute('SELECT groupID FROM parents where groups=? and tgID=?', (gr, callback_query.from_user.id)).fetchall())
	neras = InlineKeyboardButton(text = 'Назад', callback_data = 'Назад')
	await callback_query.message.edit_text(f'{callback_query.message.text}', reply_markup = genmarkup(data).add(neras))

# Отказ от рассылки ( удаление сообщения с предложением )
@dp.callback_query_handler(lambda call: call.data == 'не_хочу_разослать')
async def ne_rassilka(callback_query: types.CallbackQuery):
	await callback_query.answer('Правильно, нахер надо')
	asyncio.create_task(delete_message(callback_query.message, 0))

# Сама рассылка
@dp.callback_query_handler(lambda call: '-' in call.data)
async def rasslka(callback_query: types.CallbackQuery):

	adm_id = callback_query.from_user.id
	gr = c_u.execute('select groups from admins where tgID=?', (adm_id,)).fetchone()[0]

	# FIX TUTA
	if c_u.execute('select organisator from parents where tgID=?', (callback_query.from_user.id,)).fetchone()[0] == 'False':
		c_u.execute('update parents set organisator=? where tgID=?', ('True', callback_query.from_user.id,))
		conn_u.commit()
	if c_u.execute('select * from parents where groupID=? and groups=?', (callback_query.data, gr)).fetchone() is None:
		prnts = c_u.execute('select * from parents where groupID=?', (callback_query.data,)).fetchall()
		for parent in prnts:
			if c_u.execute('select * from groups where groups=? and groupID=?', (gr, parent[5])).fetchone() is None:
				namee = c_u.execute('select groupTitle from groups where groupID=?', (parent[5],)).fetchone()[0]
				c_u.execute('insert into groups (groups, groupID, groupTitle) '
							'values ("{}", {}, "{}")'.format(gr, parent[5], namee))
				conn_u.commit()

			# FIX TUTA
			if adm_id == parent[5]:
				c_u.execute('insert into parents (groups, tgID, last_name, first_name, groupID, organisator, nickname, username) '
						'values ("{}", {}, "{}", "{}", {}, "{}", "{}", "{}")'.format(gr, parent[1], parent[2], parent[3], parent[5], "True", parent[7], parent[8]))
				conn_u.commit()
			else:
				c_u.execute('insert into parents (groups, tgID, last_name, first_name, groupID, organisator, nickname, username) '
					'values ("{}", {}, "{}", "{}", {}, "{}", "{}", "{}")'.format(gr, parent[1], parent[2],parent[3], parent[5], "False", parent[7], parent[8]))
				conn_u.commit()


	await callback_query.answer('Отправил куда надо!')
	kb = InlineKeyboardMarkup()
	uch = InlineKeyboardButton(text = 'Участвую', callback_data = 'Участвую')
	neuch = InlineKeyboardButton(text = 'Не участвую', callback_data = 'Не участвую')

	try:
		await bot.send_message(chat_id = callback_query.data, text = callback_query.message.text, reply_markup = kb.add(uch, neuch))
	except aiogram.utils.exceptions.MigrateToChat as e:
		chat_ID = str(e).split(' New id: ')[1].split('.')[0].strip()
		c_u.execute('update groups set groupID=? where groupID=?', (int(chat_ID), int(callback_query.data), ))
		conn_u.commit()
		await bot.send_message(chat_id = chat_ID, text = callback_query.message.text, reply_markup = kb.add(uch, neuch))

# Принимает участие в мероприятии
@dp.callback_query_handler(lambda call: call.data == 'Участвую')
async def participation(callback_query: types.CallbackQuery, state: FSMContext):
	mer = callback_query.message.text.split('\n')[1].split(': ')[1]
	summ = callback_query.message.text.split('\n')[3].split(': ')[1]
	dat = callback_query.message.text.split('\n')[0].split(': ')[1]
	org = callback_query.message.text.split('\n')[2].split(': ')[1]

	# личные сообщения с ботом
	if callback_query.message.chat.type == "private":
		gr1 = c_u.execute('select groups from Event where namee=? and summ=? and datee=? and org=?', (mer, summ, dat, org)).fetchall()
		gr = ''
		# поиск верной группы(не беседы)
		for i in gr1:
			adm = c_u.execute('select tgID from admins where groups=?', (i[0],)).fetchone()[0]
			if c_u.execute('select groups from Event where namee=? and datee=? and summ=? and org=? and tgID=?',(mer, dat, summ, org, adm)).fetchone()[0] == i[0]:
				gr = i[0]  # нахождение нужной группы(не беседы)
				break
		exist_parents_in_active_events = c_u.execute('select * from active_events where groups=? and namee=? and datee=? and tgID=?',(gr, mer, dat, callback_query.from_user.id)).fetchone()
		regist_parents = c_u.execute('select * from parents where tgID=?', (callback_query.from_user.id,)).fetchone()
	# сообщение в беседах
	else:
		gr = c_u.execute('select groups from Event where namee=? and summ=? and datee=? and org=?',(mer, summ, dat, org)).fetchone()[0]
		exist_parents_in_active_events = c_u.execute('select * from active_events where groups=? and namee=? and datee=? and tgID=? and org=?',(gr, mer, dat, callback_query.from_user.id, org)).fetchone()
		regist_parents = c_u.execute('select * from parents where tgID=?', (callback_query.from_user.id,)).fetchone()
	# пользователь не нажимал на кнопку участвоваю
	if exist_parents_in_active_events is None:
		# пользователь не регистрировался в боте
		if regist_parents[2] == 'None':
			await callback_query.answer('Пожалуйста, зарегистрируйтесь во мне!')
		# пользователь зарегистрирован в боте
		else:

			# бесплатное мероприятие
			if int(summ) == 0:
				c_u.execute('insert into active_events '
							'(groups, tgID, namee, datee, parent, particip, paid, org, summ)'
							'values ("{}", {}, "{}", "{}", "{}", "{}", "{}", "{}", {})'
							''.format(gr, callback_query.from_user.id, mer, dat,regist_parents[2] + ' ' + regist_parents[3], 'True', 'True', org, summ))
				conn_u.commit()
			# платное мероприятие
			else:
				c_u.execute('insert into active_events '
							'(groups, tgID, namee, datee, parent, particip, paid, org, summ)'
							'values ("{}", {}, "{}", "{}", "{}", "{}", "{}", "{}", {})'
							''.format(gr, callback_query.from_user.id, mer, dat,regist_parents[2] + ' ' + regist_parents[3], 'True', 'False', org, summ))
				conn_u.commit()
			try:
				# Мероприятие бесплатное
				if int(summ) == 0:
					await bot.send_message(chat_id = callback_query.from_user.id,
										   text = f'Здравствуйте, {regist_parents[2] + " " + regist_parents[3]}👋!\nВы участвуете в мероприятии "{mer}", '
												  f'проходящее {dat}🗓!\n\n'
												  f'Данное мероприятие не требует перевода денежных средств, то есть является бесплатным, в следствие чего подтверждение не требуется!')
					await callback_query.answer('Записал тебя на данное мероприятие')
				# Мероприятие платное - требуется подтверждение оплаты
				else:
					kb = InlineKeyboardMarkup()
					paid = InlineKeyboardButton(text = 'Оплачено', callback_data = 'paid')
					await state.set_state(UploadPhotoForm.mer)
					await state.update_data(namee_mer = mer)
					await state.set_state(UploadPhotoForm.dat)
					await state.update_data(datee_mer = dat)
					await state.set_state(UploadPhotoForm.org)
					await state.update_data(org_mer = org)
					await state.set_state(UploadPhotoForm.summ)
					await state.update_data(summ_mer = summ)
					await bot.send_message(chat_id = callback_query.from_user.id,
										   text = f'Здравствуйте, {regist_parents[2] + " " + regist_parents[3]}👋!\n'
												  f'Вы участвуете в мероприятии "{mer}", проходящее {dat}🗓!\n\n'
												  f'Пожалуйста, оплатите мероприятие суммой в размере {summ}, после чего нажмите нажмите на кнопку под сообщением "Оплачено💸", а затем пришлите скрин-подтверждение оплаты!',
										   reply_markup = kb.add(paid))
					await callback_query.answer('Записал тебя на данное мероприятие')
			# бот не может написать пользователю
			except aiogram.utils.exceptions.CantInitiateConversation:
				await callback_query.answer(text = 'Я не могу тебе написать первым, активируй меня!')
	# пользователь нажимал на кнопку участвоваю
	else:
		if c_u.execute(f'select particip from active_events where tgID=? and namee=? and datee=? and groups=? and org=? and summ=?',(callback_query.from_user.id, mer, dat, gr, org, summ)).fetchone()[0] == 'False':
			await callback_query.answer('Записал тебя на данное мероприятие')
			c_u.execute(f'update active_events set particip=? where tgID=? and namee=? and datee=? and groups=? and org=? and summ=?',('True', callback_query.from_user.id, mer, dat, gr, org, summ))
			conn_u.commit()
		else:
			await callback_query.answer(text = 'Вы уже участвуете в данном мероприятии!😁')

# Не принимает участие в мероприятии
@dp.callback_query_handler(lambda call: call.data == 'Не участвую')
async def participation(callback_query: types.CallbackQuery, state: FSMContext):
	mer = callback_query.message.text.split('\n')[1].split(': ')[1]
	summ = callback_query.message.text.split('\n')[3].split(': ')[1]
	dat = callback_query.message.text.split('\n')[0].split(': ')[1]
	org = callback_query.message.text.split('\n')[2].split(': ')[1]

	# личные сообщения с ботом
	if callback_query.message.chat.type == "private":
		gr1 = c_u.execute('select groups from Event where namee=? and summ=? and datee=? and org=?', (mer, summ, dat, org)).fetchall()
		gr = ''
		# поиск верной группы(не беседы)
		for i in gr1:
			adm = c_u.execute('select tgID from admins where groups=?', (i[0],)).fetchone()[0]
			if c_u.execute('select groups from Event where namee=? and datee=? and summ=? and org=? and tgID=?', (mer, dat, summ, org, adm)).fetchone()[0] == i[0]:
				gr = i[0]  # нахождение нужной группы(не беседы)
				break
		exist_parents_in_active_events = c_u.execute('select * from active_events where groups=? and namee=? and datee=? and tgID=?',(gr, mer, dat, callback_query.from_user.id)).fetchone()
		regist_parents = c_u.execute('select * from parents where tgID=?', (callback_query.from_user.id,)).fetchone()
	# сообщение в беседах
	else:
		gr = c_u.execute('select groups from Event where namee=? and summ=? and datee=? and org=?', (mer, summ, dat, org)).fetchone()[0]
		exist_parents_in_active_events = c_u.execute('select * from active_events where groups=? and namee=? and datee=? and tgID=? and org=?',(gr, mer, dat, callback_query.from_user.id, org)).fetchone()
		regist_parents = c_u.execute('select * from parents where tgID=?', (callback_query.from_user.id,)).fetchone()
	# пользователь не нажимал на кнопку участвоваю
	if exist_parents_in_active_events is None:
		# пользователь не регистрировался в боте
		if regist_parents[2] == 'None':
			await callback_query.answer('Пожалуйста, зарегистрируйтесь во мне!')
		# пользователь зарегистрирован в боте
		else:
			# бесплатное мероприятие
			if int(summ) == 0:
				c_u.execute('insert into active_events '
							'(groups, tgID, namee, datee, parent, particip, paid, org, summ)'
							'values ("{}", {}, "{}", "{}", "{}", "{}", "{}", "{}", {})'
							''.format(gr, callback_query.from_user.id, mer, dat,
									  regist_parents[2] + ' ' + regist_parents[3], 'False', 'False', org, summ))
				conn_u.commit()
			# платное мероприятие
			else:
				c_u.execute('insert into active_events '
							'(groups, tgID, namee, datee, parent, particip, paid, org, summ)'
							'values ("{}", {}, "{}", "{}", "{}", "{}", "{}", "{}", {})'
							''.format(gr, callback_query.from_user.id, mer, dat,
									  regist_parents[2] + ' ' + regist_parents[3], 'False', 'False', org, summ))
				conn_u.commit()
	# пользователь нажимал на кнопку не участвоваю
	else:
		if c_u.execute(f'select particip from active_events where tgID=? and namee=? and datee=? and groups=? and org=? and summ=?', (callback_query.from_user.id, mer, dat, gr, org, summ)).fetchone()[0] == 'True':
			await callback_query.answer('Убрал вас из списка участвующих.')
			c_u.execute(f'update active_events set particip=? where tgID=? and namee=? and datee=? and groups=? and org=? and summ=?', ('False', callback_query.from_user.id, mer, dat, gr, org, summ))
			conn_u.commit()
		else:
			await callback_query.answer(text = 'Вы уже не участвуете в данном мероприятии!😔')

# Захват скрина-подтверждения
@dp.callback_query_handler(lambda call: call.data == 'paid')
async def paid_mer(callback_query: types.CallbackQuery, state: FSMContext):
	await callback_query.answer('Пришлите, пожалуйста, скрин-подтверждение')
	await bot.send_message(chat_id = callback_query.from_user.id, text = 'Пришлите, пожалуйста, скрин-подтверждение')
	await state.set_state(UploadPhotoForm.photo)

# Перессылка админам
@dp.message_handler(content_types=['photo', 'text'], state=UploadPhotoForm.photo)
async def process_photo(message: types.Message, state: FSMContext):
	if message.content_type == 'photo':
		user_data = await state.get_data()
		await state.finish()

		temp_fio = c_u.execute('SELECT * FROM parents WHERE tgID=?', (message.from_user.id, )).fetchone()
		name_group = c_u.execute('SELECT groups FROM groups WHERE groupID=?', (temp_fio[4], )).fetchone()
		admins = c_u.execute('SELECT * FROM admins where groups=?', (name_group, )).fetchall()

		FIO = f"Мероприятие: {user_data['namee_mer']}\nДата: {user_data['datee_mer']}\nСумма: {user_data['summ_mer']}\nОрганизатор: {user_data['org_mer']}\n" + temp_fio[2] + ' ' + temp_fio[3] + f'\nUsername: @{temp_fio[7]}'
		for ad in admins:
			await bot.send_photo(chat_id = ad[1], photo = message.photo[0].file_id, caption = FIO)
		await state.finish()
		c_u.execute('UPDATE active_events SET paid=? WHERE tgID=? and groups=? and namee=? and datee=? and org=? and summ=?',
					('True', message.from_user.id, temp_fio[4], user_data['namee_mer'], user_data['datee_mer'], user_data['org_mer'], user_data['summ_mer']))
		conn_u.commit()
		await message.answer("Спасибо за подтверждение оплаты!\nДанный скриншот был отправлен организатору мероприятия!")
	else:
		await message.answer('Скрина-подтверждения не замечено, пришлите, пожалуйста, скрин-подтверждение!')

# Вывод всех записанных мероприятий из БД
@dp.message_handler(lambda message: message.text.lower() == '/events') # and message.chat.type == 'private'
async def all_events_command(message: types.Message):
	kb = InlineKeyboardMarkup()
	exit = InlineKeyboardButton(text = 'Закрыть', callback_data = 'exit')
	try:
		# группы через таблицу groups искать
		gr = c_u.execute('select groups from parents where tgID=?', (message.from_user.id, )).fetchone()[0]
	except:
		await message.answer(text = 'Не нашел вас в базе участников, пожалуйста, зарегистрируйтесь в боте и повторите попытку', reply_markup = kb.add(exit))
		return 0
	ev = c_u.execute('SELECT * FROM Event where groups = ? ', (gr, )).fetchall()
	out = ""
	cnt = 1
	flag = False
	for e in ev:
		if len(e) == 0:
			flag = True
			break
		kb.add(InlineKeyboardButton(text = f'{e[2]}', callback_data = f'{e[2]}'))
		out += f"{cnt} мероприятие:\n\t\tДата мероприятия: {e[1]}\n\t\tНазвание мероприятия: {e[2]}\n\t\tОрганизатор мероприятия: {e[3]}\n\t\tСумма с каждого: {e[4]}\n\n"
		cnt += 1

	if flag:
		await message.answer(text = 'Пока мероприятий нет, но скоро они здесь появятся!', reply_markup = kb.add(exit))
	else:
		await message.answer(out, reply_markup = kb.add(exit))

# Мои ивенты - ивенты в которых я участвую
@dp.message_handler(lambda message: message.text.lower() == '/myevents' and message.chat.type == 'private')
async def my_events_command(message: types.Message):

	kb = InlineKeyboardMarkup()
	exit = InlineKeyboardButton(text = 'Закрыть', callback_data = 'exit')
	my_ev = []

	try:
		gr = c_u.execute('select groups from parents where tgID=?', (message.from_user.id, )).fetchone()[0]
	except:
		await message.answer('Не нашел вас в списке зарегистрированных пользователей')
		return 0

	try:
		my_ev_temp = [x[0] for x in c_u.execute('select namee from active_events where tgID=? and groups=? and particip=?', (message.from_user.id, gr, 'True')).fetchall()]
		for i in my_ev_temp:
			appended = c_u.execute('select * from Event where groups=? and namee=?', (gr, i)).fetchone()
			my_ev.append(appended)
		out = ""
		cnt = 1
		for e in my_ev:
			kb.add(InlineKeyboardButton(text = f'{e[2]}', callback_data = f'my_{e[2]}'))
			if c_u.execute('select paid from active_events where tgID=? and groups=? and particip=?', (message.from_user.id, gr, 'True')).fetchone()[0] == 'True':
				out += f"{cnt} мероприятие - Оплачено✅:\n\t\tДата мероприятия: {e[1]}\n\t\tНазвание мероприятия: {e[2]}\n\t\tОрганизатор мероприятия: {e[3]}\n\t\tСумма с каждого: {e[4]}\n\n"
			elif c_u.execute('select paid from active_events where tgID=? and groups=? and particip=?', (message.from_user.id, gr, 'True')).fetchone()[0] == 'False':
				out += f"{cnt} мероприятие - Не оплачено❌:\n\t\tДата мероприятия: {e[1]}\n\t\tНазвание мероприятия: {e[2]}\n\t\tОрганизатор мероприятия: {e[3]}\n\t\tСумма с каждого: {e[4]}\n\n"
			cnt += 1
		await message.answer(out, reply_markup = kb.add(exit))
	except aiogram.utils.exceptions.MessageTextIsEmpty:

		await message.answer('Вы не участвуете ни в одном из мероприятий.')
		return 0

# Мой профиль
@dp.message_handler(lambda message: message.text.lower() == '/profile' and message.chat.type == 'private')
async def profile(message: types.Message):

	try:
		F = c_u.execute('select last_name from parents where tgID=?', (message.from_user.id,)).fetchone()[0]
	except:
		F = 'Не указано'

	try:
		I = c_u.execute('select first_name from parents where tgID=?', (message.from_user.id,)).fetchone()[0]
	except:
		I = 'Не указано'

	gr = set(c_u.execute('select groups from active_events where tgID=?', (message.from_user.id,)).fetchall())
	kb = InlineKeyboardMarkup()
	my_ev = InlineKeyboardButton(text = 'Мои события', callback_data = 'myevents')
	all_ev = InlineKeyboardButton(text = 'Все события', callback_data = 'allevents')
	change_FIO = InlineKeyboardButton(text = 'Сменить ФИО', callback_data = 'Ready_for_register')
	ln = 0
	for g in gr:
		ln += len(c_u.execute('select * from Event where groups=?', (g[0], )).fetchall())

	await message.answer(f'Last name: {F}\n'
						 f'First Name: {I}\n' 
						 f'🆔: {message.from_user.id}\n'
						 f'Username: @{message.from_user.username}\n'
						 f'==========\n'
						 f'Кол-во мероприятий, где вы участвуете: {len(c_u.execute("select * from active_events where tgID=? and particip=?", (message.from_user.id, "True")).fetchall())}\n'
						 f'Кол-во мероприятий, доступные вам: {ln}\n'
						 f'✅Оплачено мероприятий, в которых вы участвуете: {len(c_u.execute("select * from active_events where tgID=? and paid=?", (message.from_user.id, "True")).fetchall())}\n'
						 f'❌Не оплачено мероприятий, в которых вы участвуете: {len(c_u.execute("select * from active_events where tgID=? and paid=?", (message.from_user.id, "False")).fetchall())}', reply_markup = kb.add(my_ev, all_ev).add(change_FIO))

# вывод моих событий через профиль
@dp.callback_query_handler(lambda call: call.data == 'myevents')
async def ready_for_register(callback_query: types.CallbackQuery):
	kb = InlineKeyboardMarkup()
	exit = InlineKeyboardButton(text = 'Закрыть', callback_data = 'exit')
	bck = InlineKeyboardButton(text = 'Назад', callback_data = 'back_to_profile')
	my_ev = []

	try:
		gr = set(c_u.execute('select groups from active_events where tgID=?', (callback_query.from_user.id,)).fetchall())
	except:
		await callback_query.message.edit_text(text = 'Не нашел вас в списке зарегистрированных пользователей', reply_markup = kb.add(bck).add(exit))
		return 0


	my_ev_temp = [x[0] for x in c_u.execute('select namee from active_events where tgID=? and particip=?', (callback_query.from_user.id, 'True')).fetchall()]
	for j in gr:
		for i in my_ev_temp:

			appended = c_u.execute('select * from Event where groups=? and namee=?', (j[0], i)).fetchone()
			if appended is None:
				continue
			my_ev.append(appended)

	out = "ВАШИ МЕРОПРИЯТИЯ:\n\n"
	cnt = 1

	for e in my_ev:

		# Убрать try - except
		try:
			kb.add(InlineKeyboardButton(text = f'{e[2]}', callback_data = f'my_{e[2]}'))

			if c_u.execute('select paid from active_events where tgID=? and particip=? and namee=? and datee=? and org=? and summ=?', (callback_query.from_user.id, 'True', e[2], e[1], e[3], e[4])).fetchone()[0] == 'True':
				out += f"{cnt} мероприятие - Оплачено✅:\n\t\tДата мероприятия: {e[1]}\n\t\tНазвание мероприятия: {e[2]}\n\t\tОрганизатор мероприятия: {e[3]}\n\t\tСумма с каждого: {e[4]}\n\n"
			elif c_u.execute('select paid from active_events where tgID=? and particip=? and namee=? and datee=? and org=? and summ=?', (callback_query.from_user.id, 'True', e[2], e[1], e[3], e[4])).fetchone()[0] == 'False':
				out += f"{cnt} мероприятие - Не оплачено❌:\n\t\tДата мероприятия: {e[1]}\n\t\tНазвание мероприятия: {e[2]}\n\t\tОрганизатор мероприятия: {e[3]}\n\t\tСумма с каждого: {e[4]}\n\n"
			cnt += 1
		except Exception as e:
			print(e)


	if out == "ВАШИ МЕРОПРИЯТИЯ:\n\n":
		await callback_query.message.edit_text(text = 'Вы не участвуете ни в одном из мероприятий.', reply_markup = kb.add(bck, exit))
	else:
		await callback_query.message.edit_text(text = out, reply_markup = kb.add(bck, exit))

# вывод всех событий через профиль
@dp.callback_query_handler(lambda call: call.data == 'allevents')
async def ready_for_register(callback_query: types.CallbackQuery):
	kb = InlineKeyboardMarkup()
	exit = InlineKeyboardButton(text = 'Закрыть', callback_data = 'exit')
	bck = InlineKeyboardButton(text = "Профиль", callback_data = 'back_to_profile')
	gr = c_u.execute('select groups from parents where tgID=?', (callback_query.from_user.id,)).fetchone()[0]
	ev = c_u.execute('SELECT * FROM Event where groups = ? ', (gr,)).fetchall()
	out = "ВСЕ МЕРОПРИЯТИЯ:\n\n"
	cnt = 1
	for e in ev:
		kb.add(InlineKeyboardButton(text = f'{e[2]}', callback_data = f'{e[2]}'))
		out += f"{cnt} мероприятие:\n\t\tДата мероприятия: {e[1]}\n\t\tНазвание мероприятия: {e[2]}\n\t\tОрганизатор мероприятия: {e[3]}\n\t\tСумма с каждого: {e[4]}\n\n"
		cnt += 1
	await callback_query.message.edit_text(out, reply_markup = kb.add(bck, exit))

# обратно в профиль
@dp.callback_query_handler(lambda call: call.data == 'back_to_profile')
async def ready_for_register(callback_query: types.CallbackQuery):
	F = c_u.execute('select last_name from parents where tgID=?', (callback_query.from_user.id,)).fetchone()[0]
	I = c_u.execute('select first_name from parents where tgID=?', (callback_query.from_user.id,)).fetchone()[0]
	gr = set(c_u.execute('select groups from active_events where tgID=?', (callback_query.from_user.id,)).fetchall())
	kb = InlineKeyboardMarkup()
	my_ev = InlineKeyboardButton(text = 'Мои события', callback_data = 'myevents')
	all_ev = InlineKeyboardButton(text = 'Все события', callback_data = 'allevents')
	change_FIO = InlineKeyboardButton(text = 'Сменить ФИО', callback_data = 'Ready_for_register')
	ln = 0
	for g in gr:
		ln += len(c_u.execute('select * from Event where groups=?', (g[0],)).fetchall())

	await callback_query.message.edit_text(f'Фамилия: {F}\n'
						 f'Имя: {I}\n'
						 f'==========\n'
						 f'🆔: {callback_query.from_user.id}\n'
						 f'Кол-во событий, где вы участвуете: {len(c_u.execute("select * from active_events where tgID=? and particip=?", (callback_query.from_user.id, "True")).fetchall())}\n'
						 f'Кол-во событий, доступные вам: {ln}\n'
						 f'✅Оплачено мероприятий, в которых вы участвуете: {len(c_u.execute("select * from active_events where tgID=? and paid=?", (callback_query.from_user.id, "True")).fetchall())}\n'
						 f'❌Не оплачено мероприятий, в которых вы участвуете: {len(c_u.execute("select * from active_events where tgID=? and paid=?", (callback_query.from_user.id, "False")).fetchall())}',
						 reply_markup = kb.add(my_ev, all_ev).add(change_FIO))

# Выход из сообщения
@dp.callback_query_handler(lambda call: call.data == 'exit')
async def exit(callback_query: types.CallbackQuery):
	await callback_query.answer('Закрываю.')
	asyncio.create_task(delete_message(callback_query.message, 0))

# Вывод какого то "моего" ивента
@dp.callback_query_handler(lambda call: call.data in ['my_'+x[0] for x in c_u.execute('select namee from Event').fetchall()])
async def react_ev(callback_query: types.CallbackQuery):
	await callback_query.answer('Получаю информацию о мероприятии...')

	if c_u.execute('select * from admins where tgID=?', (callback_query.from_user.id, )).fetchone() is not None:
		kb = InlineKeyboardMarkup()
		bck = InlineKeyboardButton(text = 'Назад', callback_data = 'back_my_ev')
		ras = InlineKeyboardButton(text = 'Разослать', callback_data = 'хочу_разослать')
		uch = InlineKeyboardButton(text = 'Участвую', callback_data = 'Участвую')
		neuch = InlineKeyboardButton(text = 'Не участвую', callback_data = 'Не участвую')
		spisok = InlineKeyboardButton(text = 'Список участников', callback_data = 'Список участников')
		change = InlineKeyboardButton(text = 'Изменить событие(не работает)', callback_data = 'Изменить событие')
		remove = InlineKeyboardButton(text = 'Удалить событие(не работает)', callback_data = 'Удалить событие')
		gr = c_u.execute('select groups from admins where tgID=?', (callback_query.from_user.id,)).fetchone()[0]
		q = c_u.execute(f'select * from Event where namee = ? and groups=?', (callback_query.data.split('_')[1], gr)).fetchone()
		await callback_query.message.edit_text(text = f"|Дата мероприятия: {q[1]}\n"
		f"|Название мероприятия: {q[2]}\n"
		f"|Организатор: {q[3]}\n"
		f"|Сумма мероприятия: {q[4]}\n", reply_markup = kb.add(ras,spisok).add(uch, neuch).add(change, remove).add(bck))
	else:
		kb = InlineKeyboardMarkup()
		uch = InlineKeyboardButton(text = 'Участвую', callback_data = 'Участвую')
		neuch = InlineKeyboardButton(text = 'Не участвую', callback_data = 'Не участвую')
		bck = InlineKeyboardButton(text = 'Назад', callback_data = 'back_my_ev')
		spisok = InlineKeyboardButton(text = 'Список участников', callback_data = 'Список участников')
		gr = c_u.execute('select groups from parents where tgID=?', (callback_query.from_user.id,)).fetchone()[0]
		q = c_u.execute(f'select * from Event where namee = ? and groups=?', (callback_query.data.split('_')[1], gr)).fetchone()
		await callback_query.message.edit_text(text = f"|Дата мероприятия: {q[1]}\n"
													  f"|Название мероприятия: {q[2]}\n"
													  f"|Организатор: {q[3]}\n"
													  f"|Сумма мероприятия: {q[4]}\n",
											   reply_markup = kb.add(uch, neuch).add(spisok).add(bck))

# Возврат в список всех моих ивентов
@dp.callback_query_handler(lambda call: call.data == 'back_my_ev')
async def spisok_pers(callback_query: types.CallbackQuery):
	kb = InlineKeyboardMarkup()
	exit = InlineKeyboardButton(text = 'Закрыть', callback_data = 'exit')
	bck = InlineKeyboardButton(text = 'Назад', callback_data = 'back_to_profile')
	my_ev = []

	try:
		gr = set(c_u.execute('select groups from active_events where tgID=?', (callback_query.from_user.id,)).fetchall())
	except:
		await callback_query.message.edit_text(text = 'Не нашел вас в списке зарегистрированных пользователей',
											   reply_markup = kb.add(bck).add(exit))
		return 0


	my_ev_temp = [x[0] for x in c_u.execute('select namee from active_events where tgID=? and particip=?',
											(callback_query.from_user.id, 'True')).fetchall()]
	for j in gr:
		for i in my_ev_temp:

			appended = c_u.execute('select * from Event where groups=? and namee=?', (j[0], i)).fetchone()
			if appended is None:
				continue
			my_ev.append(appended)

	out = "ВАШИ МЕРОПРИЯТИЯ:\n\n"
	cnt = 1

	for e in my_ev:

		# Убрать try - except
		try:
			kb.add(InlineKeyboardButton(text = f'{e[2]}', callback_data = f'my_{e[2]}'))

			if c_u.execute(
					'select paid from active_events where tgID=? and particip=? and namee=? and datee=? and org=? and summ=?',
					(callback_query.from_user.id, 'True', e[2], e[1], e[3], e[4])).fetchone()[0] == 'True':
				out += f"{cnt} мероприятие - Оплачено✅:\n\t\tДата мероприятия: {e[1]}\n\t\tНазвание мероприятия: {e[2]}\n\t\tОрганизатор мероприятия: {e[3]}\n\t\tСумма с каждого: {e[4]}\n\n"
			elif c_u.execute(
					'select paid from active_events where tgID=? and particip=? and namee=? and datee=? and org=? and summ=?',
					(callback_query.from_user.id, 'True', e[2], e[1], e[3], e[4])).fetchone()[0] == 'False':
				out += f"{cnt} мероприятие - Не оплачено❌:\n\t\tДата мероприятия: {e[1]}\n\t\tНазвание мероприятия: {e[2]}\n\t\tОрганизатор мероприятия: {e[3]}\n\t\tСумма с каждого: {e[4]}\n\n"
			cnt += 1
		except Exception as e:
			print(e)
	if out == "ВАШИ МЕРОПРИЯТИЯ:\n\n":
		await callback_query.message.edit_text(text = 'Вы не участвуете ни в одном из мероприятий.', reply_markup = kb.add(bck, exit))
	else:
		await callback_query.message.edit_text(text = out, reply_markup = kb.add(bck, exit))

# После выбора мероприятия для рассылки
@dp.callback_query_handler(lambda call: call.data in [x[0] for x in c_u.execute('select namee from Event').fetchall()])
async def react_ev(callback_query: types.CallbackQuery):
	await callback_query.answer('Получаю информацию о мероприятии...')

	if c_u.execute('select * from admins where tgID=?', (callback_query.from_user.id, )).fetchone() is not None:
		gr = c_u.execute('select groups from admins where tgID=?', (callback_query.from_user.id,)).fetchone()[0]
		q = c_u.execute(f'select * from Event where namee = ? and groups=?', (callback_query.data, gr)).fetchone()
		kb = InlineKeyboardMarkup()
		bck = InlineKeyboardButton(text = 'Назад', callback_data = 'Назад')
		ras = InlineKeyboardButton(text = 'Разослать', callback_data = 'хочу_разослать')
		uch = InlineKeyboardButton(text = 'Участвую', callback_data = 'Участвую')
		neuch = InlineKeyboardButton(text = 'Не участвую', callback_data = 'Не участвую')
		spisok = InlineKeyboardButton(text = 'Список участников', callback_data = 'Список участников')
		change = InlineKeyboardButton(text = 'Изменить событие(не работает)', callback_data = 'Изменить событие')
		remove = InlineKeyboardButton(text = 'Удалить событие(не работает)', callback_data = 'Удалить событие')
		await callback_query.message.edit_text(text = f"|Дата мероприятия: {q[1]}\n"
		f"|Название мероприятия: {q[2]}\n"
		f"|Организатор: {q[3]}\n"
		f"|Сумма мероприятия: {q[4]}\n", reply_markup = kb.add(ras,spisok).add(uch, neuch).add(change, remove).add(bck))
	else:
		gr = c_u.execute('select groups from parents where tgID=?', (callback_query.from_user.id,)).fetchone()[0]
		uch = InlineKeyboardButton(text = 'Участвую', callback_data = 'Участвую')
		neuch = InlineKeyboardButton(text = 'Не участвую', callback_data = 'Не участвую')
		q = c_u.execute(f'select * from Event where namee = ? and groups=?', (callback_query.data, gr)).fetchone()
		kb = InlineKeyboardMarkup()
		bck = InlineKeyboardButton(text = 'Назад', callback_data = 'Назад')
		spisok = InlineKeyboardButton(text = 'Список участников', callback_data = 'Список участников')
		await callback_query.message.edit_text(text = f"|Дата мероприятия: {q[1]}\n"
													  f"|Название мероприятия: {q[2]}\n"
													  f"|Организатор: {q[3]}\n"
													  f"|Сумма мероприятия: {q[4]}\n",
											   reply_markup = kb.add(uch, neuch).add(spisok).add(bck))

# Вывод списка участников какого-либо мероприятия
@dp.callback_query_handler(lambda call: call.data == 'Список участников')
async def spisok_pers(callback_query: types.CallbackQuery):
	await callback_query.answer('Предоставляю список участников...')

	kb = InlineKeyboardMarkup()
	bck = InlineKeyboardButton(text = 'Назад', callback_data = 'Назад')
	await callback_query.answer('Предоставляю список участников!')
	mer = callback_query.message.text.split('\n')[1].split(': ')[1]
	all_pers = c_u.execute('select * from active_events where namee=?', (mer, )).fetchall()
	out = f'В мероприятии "{mer}" участвуют следующие лица:\n'
	cnt = 1
	for pers in all_pers:
		if pers [6] == 'True':
			out += f"{cnt}) {pers[4]} - Оплачено✅\n"
		else:
			out += f"{cnt}) {pers[4]} - Не оплачено❌\n"
		cnt += 1

	if out == f'В мероприятии "{mer}" участвуют следующие лица:\n':
		await callback_query.message.edit_text(text = 'В данном мероприятии пока не участвует ни один человек', reply_markup = kb.add(bck))
	else:
		await callback_query.message.edit_text(text = out,  reply_markup = kb.add(bck))

# Назад к мероприятиям
@dp.callback_query_handler(lambda call: call.data == 'Назад')
async def bck(callback_query: types.CallbackQuery):
	kb = InlineKeyboardMarkup()
	exit = InlineKeyboardButton(text = 'Закрыть', callback_data = 'exit')
	bck = InlineKeyboardButton(text = "Профиль", callback_data = 'back_to_profile')
	gr = c_u.execute('select groups from parents where tgID=?', (callback_query.from_user.id,)).fetchone()[0]
	ev = c_u.execute('SELECT * FROM Event where groups = ? ', (gr,)).fetchall()
	out = "ВСЕ МЕРОПРИЯТИЯ:\n\n"
	cnt = 1
	for e in ev:
		kb.add(InlineKeyboardButton(text = f'{e[2]}', callback_data = f'{e[2]}'))
		out += f"{cnt} мероприятие:\n\t\tДата мероприятия: {e[1]}\n\t\tНазвание мероприятия: {e[2]}\n\t\tОрганизатор мероприятия: {e[3]}\n\t\tСумма с каждого: {e[4]}\n\n"
		cnt += 1
	await callback_query.message.edit_text(out, reply_markup = kb.add(bck, exit))

# Удаление сообщений - (сообщение, через сколько удалить)
async def delete_message(message: types.Message, sleep_time: int = 0):
    await asyncio.sleep(sleep_time)
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await message.delete()

# классический запуск
if __name__ == "__main__":
	executor.start_polling(dp, skip_updates = True)





