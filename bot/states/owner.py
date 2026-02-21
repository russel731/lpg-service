from aiogram.fsm.state import StatesGroup, State


class OwnerRegistration(StatesGroup):
    name = State()
    phone = State()
    station = State()
    location = State()