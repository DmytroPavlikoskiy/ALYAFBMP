from aiogram.fsm.state import State, StatesGroup

class User_Reg(StatesGroup):
    email = State()
    password = State()
    first_name = State()
    last_name = State()
    phone = State()

class User_Log(StatesGroup):
    email = State()
    password = State()