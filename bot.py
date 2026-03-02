# bot.py
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN
import database  # наш модуль для работы с базой данных

# --------------------------
# Инициализация бота
# --------------------------
bot = Bot(token=BOT_TOKEN)  # создаем объект бота с токеном
storage = MemoryStorage()   # временное хранилище состояния пользователей (FSM)
dp = Dispatcher(bot, storage=storage)
import os
TOKEN = os.environ.get("BOT_TOKEN")

# Создаем таблицы, если их нет
database.init_db()

# --------------------------
# FSM (Finite State Machine)
# --------------------------
# Состояния для добавления новой машины
class AddCar(StatesGroup):
    waiting_for_car = State()  # ожидаем ввод марки, модели, года

# Состояния для добавления сервиса
class AddService(StatesGroup):
    choosing_car = State()        # пользователь выбирает машину
    waiting_for_service = State() # ожидаем ввод данных сервиса

# --------------------------
# Главное меню с кнопками
# --------------------------
def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ Добавить машину", callback_data="add_car"),
        InlineKeyboardButton("📋 Мои машины", callback_data="my_cars"),
        InlineKeyboardButton("🛠 Добавить сервис", callback_data="add_service"),
        InlineKeyboardButton("📊 История / Затраты", callback_data="history")
    )
    return kb

# --------------------------
# Кнопки для конкретной машины
# --------------------------
def car_buttons(car_id):
    """
    Inline кнопки для одной машины:
    - История
    - Добавить сервис
    - Удалить машину
    """
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 История", callback_data=f"history_{car_id}"),
        InlineKeyboardButton("🛠 Добавить сервис", callback_data=f"add_service_{car_id}"),
        InlineKeyboardButton("❌ Удалить машину", callback_data=f"delete_car_{car_id}")
    )
    return kb

# --------------------------
# Команда /start
# --------------------------
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "Привет 👋\nЯ буду вести журнал твоего авто.",
        reply_markup=main_menu()
    )

# --------------------------
# Обработка главных кнопок
# --------------------------
@dp.callback_query_handler(lambda c: True)
async def process_callback(callback_query: types.CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id

    # Добавление новой машины
    if data == "add_car":
        await bot.send_message(user_id, "Введите машину в формате: марка, модель, год")
        await AddCar.waiting_for_car.set()

    # Показать список машин с кнопками
    elif data == "my_cars":
        await show_cars_buttons(user_id)

    # Добавление сервиса через выбор машины
    elif data == "add_service":
        await start_add_service(user_id)

    # Показать историю и затраты по всем машинам
    elif data == "history":
        await show_history(user_id)

# --------------------------
# Добавление новой машины (FSM)
# --------------------------
@dp.message_handler(state=AddCar.waiting_for_car)
async def process_add_car(message: types.Message, state: FSMContext):
    try:
        make, model, year = map(str.strip, message.text.split(","))
        year = int(year)
    except:
        await message.answer("Неверный формат. Попробуй снова: марка, модель, год")
        return

    database.add_car(message.from_user.id, make, model, year)
    await message.answer(f"Машина добавлена: {make} {model}, {year}", reply_markup=main_menu())
    await state.finish()

# --------------------------
# Показ списка машин с кнопками
# --------------------------
async def show_cars_buttons(user_id):
    cars = database.get_user_cars(user_id)
    if not cars:
        await bot.send_message(user_id, "У тебя пока нет добавленных машин.", reply_markup=main_menu())
        return

    for car in cars:
        car_id, make, model, year = car
        await bot.send_message(
            user_id,
            f"{make} {model} ({year})",
            reply_markup=car_buttons(car_id)  # для каждой машины отдельные кнопки
        )

# --------------------------
# Добавление сервиса (начало)
# --------------------------
async def start_add_service(user_id):
    cars = database.get_user_cars(user_id)
    if not cars:
        await bot.send_message(user_id, "Сначала добавь машину через кнопку 'Добавить машину'", reply_markup=main_menu())
        return

    text = "Выбери машину для добавления сервиса (введи номер):\n"
    for c in cars:
        text += f"{c[0]}. {c[1]} {c[2]}, {c[3]}\n"
    await bot.send_message(user_id, text)
    await AddService.choosing_car.set()

# --------------------------
# Выбор машины для сервиса (FSM)
# --------------------------
@dp.message_handler(state=AddService.choosing_car)
async def process_choose_car(message: types.Message, state: FSMContext):
    try:
        car_id = int(message.text)
    except:
        await message.answer("Неверный ввод. Введи номер машины.")
        return

    await state.update_data(car_id=car_id)
    await message.answer("Введите сервис в формате: описание, пробег, дата (ДД.ММ.ГГГГ), затраты")
    await AddService.waiting_for_service.set()

# --------------------------
# Добавление сервиса (FSM)
# --------------------------
@dp.message_handler(state=AddService.waiting_for_service)
async def process_add_service(message: types.Message, state: FSMContext):
    data = await state.get_data()
    car_id = data['car_id']

    try:
        description, mileage, date, cost = map(str.strip, message.text.split(","))
        mileage = int(mileage)
        cost = float(cost)
    except:
        await message.answer("Неверный формат. Попробуй снова: описание, пробег, дата, затраты")
        return

    database.add_service(car_id, description, mileage, date, cost)
    await message.answer(f"Сервисная запись добавлена для машины {car_id}", reply_markup=main_menu())
    await state.finish()

# --------------------------
# Показ истории конкретной машины
# --------------------------
async def show_car_history(user_id, car_id):
    services = database.get_car_services(car_id)
    if not services:
        await bot.send_message(user_id, "Для этой машины нет записей.", reply_markup=main_menu())
        return

    total_cost = sum([s[3] for s in services])
    text = ""
    for s in services:
        text += f"- {s[0]}, пробег: {s[1]} км, дата: {s[2]}, затраты: {s[3]}\n"
    text += f"Общие затраты: {total_cost}"
    await bot.send_message(user_id, text, reply_markup=main_menu())

# --------------------------
# Добавление сервиса через кнопку конкретной машины
# --------------------------
async def start_add_service_for_car(user_id, car_id):
    await bot.send_message(user_id, "Введите сервис в формате: описание, пробег, дата (ДД.ММ.ГГГГ), затраты")
    await AddService.waiting_for_service.set()
    state = dp.current_state(user=user_id)
    await state.update_data(car_id=car_id)

# --------------------------
# Обработка callback кнопок по конкретной машине
# --------------------------
@dp.callback_query_handler(lambda c: c.data.startswith(("history_", "add_service_", "delete_car_")))
async def handle_car_buttons(callback_query: types.CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id

    if data.startswith("history_"):
        car_id = int(data.split("_")[1])
        await show_car_history(user_id, car_id)
    elif data.startswith("add_service_"):
        car_id = int(data.split("_")[2])
        await start_add_service_for_car(user_id, car_id)
    elif data.startswith("delete_car_"):
        car_id = int(data.split("_")[2])
        database.delete_car(car_id)  # удалить машину и все сервисы
        await bot.send_message(user_id, "Машина удалена ✅", reply_markup=main_menu())

# --------------------------
# Показ истории всех машин с подсчетом затрат
# --------------------------
async def show_history(user_id):
    history = database.get_user_history(user_id)
    if not history:
        await bot.send_message(user_id, "Нет машин для отображения истории.", reply_markup=main_menu())
        return

    text = ""
    for car in history:
        text += f"{car['make']} {car['model']} ({car['year']}):\n"
        if not car['services']:
            text += "  Нет записей\n"
        else:
            for s in car['services']:
                text += f"  - {s[0]}, пробег: {s[1]} км, дата: {s[2]}, затраты: {s[3]}\n"
            text += f"  Общие затраты: {car['total_cost']}\n"
    await bot.send_message(user_id, text, reply_markup=main_menu())

# --------------------------
# Запуск бота
# --------------------------
if __name__ == "__main__":
    print("Бот запущен с последними изменениями ✅")
    executor.start_polling(dp, skip_updates=True)