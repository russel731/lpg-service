from aiogram.fsm.state import StatesGroup, State


class OwnerRegistration(StatesGroup):
    phone = State()
    station_name = State()
    location = State()