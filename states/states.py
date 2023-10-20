from aiogram.fsm.state import State, StatesGroup


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
    lastname = State()
    firstname = State()
    check = State()


# Cкрины-подтверждения
class UploadPhotoForm(StatesGroup):
    photo = State()
    mer = State()
    dat = State()
    org = State()
    summ = State()
    grps = State()
