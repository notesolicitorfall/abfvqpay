import hashlib
import hmac
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).parent
DB_PATH = ROOT / "internet_provider.db"

ENTITIES = {
    "clients": {
        "label": "Клиенты",
        "singular": "клиента",
        "icon": "◉",
        "label_field": "full_name",
        "display": ["full_name", "phone", "email", "registration_date", "status"],
        "fields": [
            ("full_name", "ФИО", "text", True, None),
            ("phone", "Телефон", "tel", True, None),
            ("email", "Электронная почта", "email", False, None),
            ("registration_date", "Дата регистрации", "date", True, None),
            ("status", "Статус", "status", True, None),
        ],
    },
    "contracts": {
        "label": "Договоры",
        "singular": "договор",
        "icon": "▤",
        "label_field": "contract_number",
        "display": ["contract_number", "client_id", "tariff_id", "address_id", "employee_id", "start_date", "status"],
        "fields": [
            ("contract_number", "Номер договора", "text", True, None),
            ("client_id", "Клиент", "reference", True, "clients"),
            ("tariff_id", "Тариф", "reference", True, "tariffs"),
            ("address_id", "Адрес подключения", "reference", True, "addresses"),
            ("employee_id", "Сотрудник", "employee", True, None),
            ("start_date", "Дата начала", "date", True, None),
            ("end_date", "Дата окончания", "date", False, None),
            ("status", "Статус", "status", True, None),
        ],
    },
    "tariffs": {
        "label": "Тарифы",
        "singular": "тариф",
        "icon": "◈",
        "label_field": "name",
        "display": ["name", "speed_mbps", "price", "description", "status"],
        "fields": [
            ("name", "Название тарифа", "text", True, None),
            ("speed_mbps", "Скорость, Мбит/с", "number", True, None),
            ("price", "Стоимость в месяц, ₽", "decimal", True, None),
            ("description", "Описание", "textarea", False, None),
            ("status", "Статус", "status", True, None),
        ],
    },
    "addresses": {
        "label": "Адреса",
        "singular": "адрес",
        "icon": "⌖",
        "label_field": "street",
        "display": ["city", "street", "house", "apartment"],
        "fields": [
            ("city", "Город", "text", True, None),
            ("street", "Улица", "text", True, None),
            ("house", "Дом", "text", True, None),
            ("apartment", "Квартира", "text", False, None),
        ],
    },
    "devices": {
        "label": "Оборудование",
        "singular": "устройство",
        "icon": "⌘",
        "label_field": "model",
        "display": ["model", "device_type", "mac_address", "client_id", "status"],
        "fields": [
            ("client_id", "Клиент", "reference", True, "clients"),
            ("mac_address", "MAC-адрес", "text", True, None),
            ("device_type", "Тип устройства", "text", True, None),
            ("model", "Модель", "text", True, None),
            ("status", "Статус", "status", True, None),
        ],
    },
    "ip_addresses": {
        "label": "IP-адреса",
        "singular": "IP-адрес",
        "icon": "⌁",
        "label_field": "ip",
        "display": ["ip", "type", "address_id", "status"],
        "fields": [
            ("address_id", "Адрес подключения", "reference", True, "addresses"),
            ("ip", "IP-адрес", "text", True, None),
            ("type", "Тип адреса", "text", True, None),
            ("status", "Статус", "status", True, None),
        ],
    },
    "payments": {
        "label": "Платежи",
        "singular": "платёж",
        "icon": "₽",
        "label_field": "amount",
        "display": ["contract_id", "amount", "payment_date", "payment_method", "status"],
        "fields": [
            ("contract_id", "Договор", "reference", True, "contracts"),
            ("amount", "Сумма, ₽", "decimal", True, None),
            ("payment_date", "Дата и время оплаты", "datetime-local", True, None),
            ("payment_method", "Способ оплаты", "text", True, None),
            ("status", "Статус", "status", True, None),
        ],
    },
    "support_tickets": {
        "label": "Заявки",
        "singular": "заявку",
        "icon": "✳",
        "label_field": "subject",
        "display": ["subject", "client_id", "contract_id", "created_at", "status"],
        "fields": [
            ("client_id", "Клиент", "reference", True, "clients"),
            ("contract_id", "Договор", "reference", False, "contracts"),
            ("subject", "Тема обращения", "text", True, None),
            ("description", "Описание", "textarea", False, None),
            ("status", "Статус", "status", True, None),
            ("created_at", "Создана", "datetime-local", True, None),
            ("closed_at", "Закрыта", "datetime-local", False, None),
        ],
    },
}

FIELD_LABELS = {
    name: label
    for entity in ENTITIES.values()
    for name, label, _kind, _required, _reference in entity["fields"]
}
DISPLAY_LABELS = {
    "registration_date": "Дата регистрации",
    "speed_mbps": "Скорость",
    "price": "Стоимость",
    "client_id": "Клиент",
    "tariff_id": "Тариф",
    "address_id": "Адрес",
    "contract_id": "Договор",
    "start_date": "Начало",
    "end_date": "Окончание",
    "payment_date": "Дата оплаты",
    "payment_method": "Способ оплаты",
    "created_at": "Создана",
    "closed_at": "Закрыта",
    "mac_address": "MAC-адрес",
    "device_type": "Тип",
    "ip": "IP-адрес",
    "type": "Тип",
    "city": "Город",
    "street": "Улица",
    "house": "Дом",
    "apartment": "Квартира",
    "full_name": "ФИО",
    "phone": "Телефон",
    "email": "Электронная почта",
    "contract_number": "Номер договора",
    "name": "Название",
    "subject": "Тема",
    "description": "Описание",
    "amount": "Сумма",
    "status": "Статус",
    "employee_id": "Сотрудник",
}

DATA_TABLES = tuple(ENTITIES)
PASSWORD_ITERATIONS = 310_000

SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    display_name TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    registration_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Активен'
);
CREATE TABLE IF NOT EXISTS tariffs (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    speed_mbps INTEGER NOT NULL CHECK (speed_mbps > 0),
    price NUMERIC NOT NULL CHECK (price >= 0),
    description TEXT,
    status TEXT NOT NULL DEFAULT 'Активен'
);
CREATE TABLE IF NOT EXISTS addresses (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    city TEXT NOT NULL,
    street TEXT NOT NULL,
    house TEXT NOT NULL,
    apartment TEXT
);
CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    contract_number TEXT NOT NULL UNIQUE,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    tariff_id INTEGER NOT NULL REFERENCES tariffs(id) ON DELETE RESTRICT,
    address_id INTEGER NOT NULL REFERENCES addresses(id) ON DELETE RESTRICT,
    employee_id INTEGER REFERENCES employees(id) ON DELETE RESTRICT,
    start_date TEXT NOT NULL,
    end_date TEXT,
    status TEXT NOT NULL DEFAULT 'Активен'
);
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    mac_address TEXT NOT NULL UNIQUE,
    device_type TEXT NOT NULL,
    model TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Активен'
);
CREATE TABLE IF NOT EXISTS ip_addresses (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    address_id INTEGER NOT NULL REFERENCES addresses(id) ON DELETE CASCADE,
    ip TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Свободен'
);
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    contract_id INTEGER NOT NULL REFERENCES contracts(id) ON DELETE RESTRICT,
    amount NUMERIC NOT NULL CHECK (amount >= 0),
    payment_date TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Оплачен'
);
CREATE TABLE IF NOT EXISTS support_tickets (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    contract_id INTEGER REFERENCES contracts(id) ON DELETE SET NULL,
    subject TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'Открыта',
    created_at TEXT NOT NULL,
    closed_at TEXT
);
"""

SEED = [
    ("clients", ["full_name", "phone", "email", "registration_date", "status"], [
        ("Александр Петров", "+7 (900) 123-45-67", "a.petrov@example.ru", "2025-03-12", "Активен"),
        ("Мария Иванова", "+7 (901) 234-56-78", "m.ivanova@example.ru", "2025-07-04", "Активен"),
        ("Дмитрий Смирнов", "+7 (902) 345-67-89", "d.smirnov@example.ru", "2026-01-19", "Активен"),
        ("Елена Кузнецова", "+7 (903) 456-78-90", "e.kuznetsova@example.ru", "2026-05-22", "Неактивен"),
    ]),
    ("tariffs", ["name", "speed_mbps", "price", "description", "status"], [
        ("Старт", 100, 550, "Для комфортной работы и видео", "Активен"),
        ("Домашний", 300, 790, "Высокая скорость для всей семьи", "Активен"),
        ("Максимум", 600, 1090, "Максимальная скорость без ограничений", "Активен"),
    ]),
    ("addresses", ["city", "street", "house", "apartment"], [
        ("Москва", "Лесная", "12", "34"),
        ("Москва", "Мира", "8", "17"),
        ("Москва", "Садовая", "21", "56"),
        ("Москва", "Центральная", "4", "9"),
    ]),
]


@contextmanager
def connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def _password_digest(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PASSWORD_ITERATIONS
    ).hex()


def create_employee(username, display_name, password):
    username = username.strip().casefold()
    display_name = display_name.strip()
    if not 3 <= len(username) <= 40 or any(character.isspace() for character in username):
        raise ValueError("Логин должен содержать от 3 до 40 символов без пробелов.")
    if not display_name:
        raise ValueError("Укажите имя сотрудника.")
    if len(password) < 8:
        raise ValueError("Пароль должен содержать не менее 8 символов.")

    salt = secrets.token_bytes(16).hex()
    password_hash = _password_digest(password, salt)
    with connect() as db:
        try:
            cursor = db.execute(
                "INSERT INTO employees (username, display_name, password_salt, password_hash, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (username, display_name, salt, password_hash, datetime.now().isoformat(timespec="seconds")),
            )
        except sqlite3.IntegrityError as error:
            if "employees.username" in str(error):
                raise ValueError("Такой логин уже зарегистрирован.") from error
            raise

        employee_id = cursor.lastrowid
        if db.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 1:
            for table in DATA_TABLES:
                db.execute(f"UPDATE {table} SET owner_id = ? WHERE owner_id IS NULL", (employee_id,))
            db.execute(
                "UPDATE contracts SET employee_id = ? WHERE owner_id = ? AND employee_id IS NULL",
                (employee_id, employee_id),
            )
        return {
            "id": employee_id,
            "username": username,
            "display_name": display_name,
        }


def authenticate_employee(username, password):
    normalized_username = username.strip().casefold()
    with connect() as db:
        employee = db.execute(
            "SELECT id, username, display_name, password_salt, password_hash "
            "FROM employees WHERE username = ?",
            (normalized_username,),
        ).fetchone()
    if employee is None:
        return None
    attempted_hash = _password_digest(password, employee["password_salt"])
    if not hmac.compare_digest(attempted_hash, employee["password_hash"]):
        return None
    return {
        "id": employee["id"],
        "username": employee["username"],
        "display_name": employee["display_name"],
    }


def initialize_database():
    with connect() as db:
        db.executescript(SCHEMA)
        for table in DATA_TABLES:
            columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
            if "owner_id" not in columns:
                db.execute(f"ALTER TABLE {table} ADD COLUMN owner_id INTEGER REFERENCES employees(id) ON DELETE CASCADE")
        contract_columns = {row["name"] for row in db.execute("PRAGMA table_info(contracts)")}
        if "employee_id" not in contract_columns:
            db.execute("ALTER TABLE contracts ADD COLUMN employee_id INTEGER REFERENCES employees(id) ON DELETE RESTRICT")
        for table in DATA_TABLES:
            db.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_owner_id ON {table}(owner_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_contracts_employee_start ON contracts(employee_id, start_date)")
        if db.execute("SELECT COUNT(*) FROM clients").fetchone()[0] == 0:
            for table, columns, rows in SEED:
                placeholders = ", ".join("?" for _ in columns)
                db.executemany(
                    f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                    rows,
                )
            db.executemany(
                "INSERT INTO contracts (contract_number, client_id, tariff_id, address_id, start_date, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [
                    ("Д-2025-001", 1, 2, 1, "2025-03-12", "Активен"),
                    ("Д-2025-002", 2, 1, 2, "2025-07-04", "Активен"),
                    ("Д-2026-003", 3, 3, 3, "2026-01-19", "Активен"),
                ],
            )
            db.executemany(
                "INSERT INTO devices (client_id, mac_address, device_type, model, status) VALUES (?, ?, ?, ?, ?)",
                [
                    (1, "A4:5E:60:12:34:01", "Роутер", "Keenetic Start", "Активен"),
                    (2, "A4:5E:60:12:34:02", "Роутер", "TP-Link Archer C6", "Активен"),
                    (3, "A4:5E:60:12:34:03", "ONT-терминал", "Huawei HG8245H", "Активен"),
                ],
            )
            db.executemany(
                "INSERT INTO ip_addresses (address_id, ip, type, status) VALUES (?, ?, ?, ?)",
                [
                    (1, "10.24.1.15", "Динамический", "Назначен"),
                    (2, "10.24.1.16", "Динамический", "Назначен"),
                    (3, "10.24.1.17", "Статический", "Назначен"),
                    (4, "10.24.1.18", "Динамический", "Свободен"),
                ],
            )
            db.executemany(
                "INSERT INTO payments (contract_id, amount, payment_date, payment_method, status) VALUES (?, ?, ?, ?, ?)",
                [
                    (1, 790, "2026-10-25 10:25", "Банковская карта", "Оплачен"),
                    (2, 550, "2026-10-24 16:40", "СБП", "Оплачен"),
                    (3, 1090, "2026-10-23 09:15", "Банковская карта", "Оплачен"),
                ],
            )
            db.executemany(
                "INSERT INTO support_tickets (client_id, contract_id, subject, description, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (1, 1, "Низкая скорость интернета", "Скорость ниже заявленной в вечернее время.", "В работе", "2026-10-26 14:20"),
                    (2, 2, "Настройка роутера", "Нужна помощь с подключением нового устройства.", "Открыта", "2026-10-26 11:05"),
                ],
            )


if __name__ == "__main__":
    from desktop import run_application

    run_application(
        ENTITIES,
        connect,
        initialize_database,
        create_employee,
        authenticate_employee,
    )
