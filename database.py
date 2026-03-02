# database.py
import sqlite3

DB_NAME = "garage_log.db"  # имя базы

# --------------------------
# Инициализация базы
# --------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица машин
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            make TEXT,
            model TEXT,
            year INTEGER
        )
    """)

    # Таблица сервисов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER,
            description TEXT,
            mileage INTEGER,
            date TEXT,
            cost REAL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


# --------------------------
# Добавление новой машины
# --------------------------
def add_car(user_id, make, model, year):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cars (user_id, make, model, year) VALUES (?, ?, ?, ?)",
        (user_id, make, model, year)
    )
    conn.commit()
    conn.close()


# --------------------------
# Получение списка машин пользователя
# --------------------------
def get_user_cars(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, make, model, year FROM cars WHERE user_id=?", (user_id,))
    cars = cursor.fetchall()
    conn.close()
    return cars


# --------------------------
# Удаление машины и всех сервисов
# --------------------------
def delete_car(car_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM services WHERE car_id=?", (car_id,))
    cursor.execute("DELETE FROM cars WHERE id=?", (car_id,))
    conn.commit()
    conn.close()


# --------------------------
# Добавление сервисной записи
# --------------------------
def add_service(car_id, description, mileage, date, cost):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO services (car_id, description, mileage, date, cost) VALUES (?, ?, ?, ?, ?)",
        (car_id, description, mileage, date, cost)
    )
    conn.commit()
    conn.close()


# --------------------------
# Получение всех сервисов для одной машины
# --------------------------
def get_car_services(car_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT description, mileage, date, cost FROM services WHERE car_id=?", (car_id,))
    services = cursor.fetchall()
    conn.close()
    return services


# --------------------------
# Получение истории по всем машинам пользователя
# --------------------------
def get_user_history(user_id):
    """
    Возвращает список словарей:
    [
        {
            'id': car_id,
            'make': make,
            'model': model,
            'year': year,
            'services': [(desc, mileage, date, cost), ...],
            'total_cost': сумма затрат
        }, ...
    ]
    """
    cars = get_user_cars(user_id)
    history = []

    for c in cars:
        car_id, make, model, year = c
        services = get_car_services(car_id)
        total_cost = sum([s[3] for s in services])
        history.append({
            'id': car_id,
            'make': make,
            'model': model,
            'year': year,
            'services': services,
            'total_cost': total_cost
        })
    return history