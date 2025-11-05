from aiogram.fsm.state import State, StatesGroup

class AddUser(StatesGroup):
    telegram_id = State()
    full_name = State()
    squad = State()


class ReportForm(StatesGroup):
    direction = State()
    choose_squad =State()
    car_image = State()
    invoice_image = State()
    confirm = State() 


class ReportPDFForm(StatesGroup):
    choose_squad = State()
    choose_type = State()
    enter_date = State()


class UpdateUser(StatesGroup):
    telegram_id = State()
    choice = State()
    full_name = State()
    squad = State()

class DeleteUser(StatesGroup):
    telegram_id = State()