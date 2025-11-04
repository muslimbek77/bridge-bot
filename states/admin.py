from aiogram.fsm.state import State, StatesGroup

class AddUser(StatesGroup):
    telegram_id = State()
    full_name = State()
    squad = State()