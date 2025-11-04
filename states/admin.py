from aiogram.fsm.state import State, StatesGroup

class AddUser(StatesGroup):
    telegram_id = State()
    full_name = State()
    squad = State()


class ReportForm(StatesGroup):
    direction = State()
    car_image = State()
    invoice_image = State()
    confirm = State() 