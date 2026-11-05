import sqlite3
import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk


DISPLAY_LABELS = {
    "registration_date": "Дата регистрации",
    "speed_mbps": "Скорость, Мбит/с",
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
    "device_type": "Тип устройства",
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

STATUS_OPTIONS = {
    "clients": ["Активен", "Неактивен"],
    "contracts": ["Активен", "Приостановлен", "Завершён"],
    "tariffs": ["Активен", "Архивный"],
    "devices": ["Активен", "Неисправен", "Списан"],
    "ip_addresses": ["Свободен", "Назначен", "Зарезервирован", "Заблокирован"],
    "payments": ["Оплачен", "Ожидает оплаты", "Отклонён", "Возврат"],
    "support_tickets": ["Открыта", "В работе", "Закрыта"],
}
MONTH_LABELS = (
    "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
    "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек",
)

COLORS = {
    "navy": "#17233c",
    "blue": "#4263eb",
    "blue_light": "#eef1ff",
    "background": "#f4f6fa",
    "white": "#ffffff",
    "text": "#26334c",
    "muted": "#8491a6",
    "line": "#e4e9f1",
    "green": "#16835d",
}


class InternetProviderApp:
    def __init__(self, root, entities, connect, employee, on_logout):
        self.root = root
        self.entities = entities
        self.connect = connect
        self.employee = employee
        self.on_logout = on_logout
        self.current_table = None
        self.records = []
        self.reference_options = {}
        self.search_var = tk.StringVar()
        self.chart_period = "week"
        self.tree = None
        self.count_label = None
        self.chart_canvas = None
        self.chart_total = None

        self.root.title("СЕТЬ — информационная система интернет-провайдера")
        self.root.geometry("1280x790")
        self.root.minsize(1000, 650)
        self.root.configure(bg=COLORS["background"])
        self._configure_styles()
        self._build_shell()
        self.show_dashboard()

    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Treeview", rowheight=34, font=("Segoe UI", 10), background="white",
                        fieldbackground="white", foreground=COLORS["text"], borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#f7f8fb",
                        foreground="#6f7c92", relief="flat", padding=(9, 10))
        style.map("Treeview", background=[("selected", "#e8edff")],
                  foreground=[("selected", COLORS["text"])])
        style.configure("Vertical.TScrollbar", background="#e1e6ef", troughcolor="white", borderwidth=0)
        style.configure("Horizontal.TScrollbar", background="#e1e6ef", troughcolor="white", borderwidth=0)

    def _build_shell(self):
        self.sidebar = tk.Frame(self.root, width=238, bg=COLORS["navy"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=COLORS["navy"])
        brand.pack(fill="x", padx=18, pady=(23, 28))
        mark = tk.Label(brand, text="⌁", width=2, height=1, bg=COLORS["blue"],
                        fg="white", font=("Segoe UI", 23, "bold"))
        mark.pack(side="left", padx=(0, 11))
        brand_text = tk.Frame(brand, bg=COLORS["navy"])
        brand_text.pack(side="left")
        tk.Label(brand_text, text="СЕТЬ", bg=COLORS["navy"], fg="white",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(brand_text, text="Панель провайдера", bg=COLORS["navy"], fg="#99a6c0",
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))

        tk.Label(self.sidebar, text="РАБОЧЕЕ ПРОСТРАНСТВО", bg=COLORS["navy"], fg="#7e8ba8",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=20, pady=(0, 9))
        self.nav_frame = tk.Frame(self.sidebar, bg=COLORS["navy"])
        self.nav_frame.pack(fill="x", padx=10)
        self.nav_buttons = {}
        self._add_nav_button("dashboard", "▦", "Обзор", self.show_dashboard)
        self._add_nav_button("statistics", "▥", "Статистика", self.show_statistics)
        for table, entity in self.entities.items():
            self._add_nav_button(table, entity["icon"], entity["label"],
                                 lambda selected=table: self.show_entity(selected))

        bottom = tk.Frame(self.sidebar, bg=COLORS["navy"])
        bottom.pack(side="bottom", fill="x", padx=20, pady=20)
        tk.Label(bottom, text="●  Система работает штатно", bg=COLORS["navy"], fg="#51d6a2",
                 font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(bottom, text="Локальная база данных · SQLite", bg=COLORS["navy"], fg="#8290aa",
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(7, 0))

        main = tk.Frame(self.root, bg=COLORS["background"])
        main.pack(side="left", fill="both", expand=True)
        topbar = tk.Frame(main, height=62, bg="white", highlightbackground=COLORS["line"],
                          highlightthickness=1)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        self.breadcrumb = tk.Label(topbar, text="Управление   /   Обзор", bg="white",
                                   fg=COLORS["muted"], font=("Segoe UI", 9))
        self.breadcrumb.pack(side="left", padx=28)
        account = tk.Frame(topbar, bg="white")
        account.pack(side="right", padx=18)
        tk.Label(account, text=f"{date.today().strftime('%d.%m.%Y')}   ·   {self.employee['display_name']}",
                 bg="white", fg="#66748c", font=("Segoe UI", 9)).pack(side="left", padx=(0, 12))
        tk.Button(account, text="Выйти", command=self.on_logout, relief="flat", borderwidth=0,
                  padx=10, pady=6, bg="#eef1f6", fg=COLORS["text"],
                  font=("Segoe UI", 8), cursor="hand2").pack(side="left")

        self.content = tk.Frame(main, bg=COLORS["background"])
        self.content.pack(fill="both", expand=True, padx=28, pady=23)
        self.statusbar = tk.Label(main, text="Готово", anchor="w", bg="white",
                                  fg=COLORS["muted"], padx=18, pady=8,
                                  font=("Segoe UI", 8), highlightbackground=COLORS["line"],
                                  highlightthickness=1)
        self.statusbar.pack(fill="x", side="bottom")

    def _add_nav_button(self, key, icon, label, command):
        button = tk.Button(
            self.nav_frame, text=f"  {icon}    {label}", command=command,
            anchor="w", relief="flat", borderwidth=0, padx=10, pady=10,
            bg=COLORS["navy"], fg="#c1cbe0", activebackground="#26385b",
            activeforeground="white", font=("Segoe UI", 9), cursor="hand2",
        )
        button.pack(fill="x", pady=2)
        self.nav_buttons[key] = button

    def _select_nav(self, key):
        for name, button in self.nav_buttons.items():
            selected = name == key
            button.configure(
                bg=COLORS["blue"] if selected else COLORS["navy"],
                fg="white" if selected else "#c1cbe0",
                activebackground=COLORS["blue"] if selected else "#26385b",
            )

    def _clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()

    def _heading(self, title, subtitle, action=None):
        row = tk.Frame(self.content, bg=COLORS["background"])
        row.pack(fill="x", pady=(0, 20))
        text = tk.Frame(row, bg=COLORS["background"])
        text.pack(side="left", fill="x", expand=True)
        tk.Label(text, text=title, bg=COLORS["background"], fg=COLORS["navy"],
                 font=("Segoe UI", 19, "bold")).pack(anchor="w")
        tk.Label(text, text=subtitle, bg=COLORS["background"], fg=COLORS["muted"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))
        if action:
            button = tk.Button(row, text=action[0], command=action[1], relief="flat",
                               borderwidth=0, padx=15, pady=10, bg=COLORS["blue"], fg="white",
                               activebackground="#3453d1", activeforeground="white",
                               font=("Segoe UI", 9, "bold"), cursor="hand2")
            button.pack(side="right", anchor="center", padx=(14, 0))

    def show_dashboard(self):
        self.current_table = None
        self._select_nav("dashboard")
        self.breadcrumb.configure(text="Управление   /   Обзор")
        self._clear_content()
        self._heading("Добро пожаловать", "Сводка по работе интернет-провайдера")

        with self.connect() as db:
            counts = {
                table: db.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE owner_id = ?", (self.employee["id"],)
                ).fetchone()[0]
                for table in self.entities
            }
            active = db.execute(
                "SELECT COUNT(*) FROM contracts WHERE owner_id = ? AND status = 'Активен'",
                (self.employee["id"],),
            ).fetchone()[0]
            open_tickets = db.execute(
                "SELECT COUNT(*) FROM support_tickets WHERE owner_id = ? AND status != 'Закрыта'",
                (self.employee["id"],),
            ).fetchone()[0]
            revenue = db.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE owner_id = ? "
                "AND status = 'Оплачен' AND substr(payment_date, 1, 7) = ?",
                (self.employee["id"], date.today().strftime("%Y-%m")),
            ).fetchone()[0]
            payments = db.execute(
                "SELECT p.payment_date, p.amount, p.status, c.contract_number, cl.full_name "
                "FROM payments p JOIN contracts c ON c.id=p.contract_id "
                "JOIN clients cl ON cl.id=c.client_id WHERE p.owner_id = ? "
                "ORDER BY p.payment_date DESC LIMIT 5", (self.employee["id"],)
            ).fetchall()
            tickets = db.execute(
                "SELECT t.subject, t.status, t.created_at, cl.full_name "
                "FROM support_tickets t JOIN clients cl ON cl.id=t.client_id "
                "WHERE t.owner_id = ? ORDER BY t.created_at DESC LIMIT 5",
                (self.employee["id"],),
            ).fetchall()

        cards = [
            ("Клиенты", counts["clients"], "Всего в системе", "◉"),
            ("Активные договоры", active, "Подключений обслуживается", "▤"),
            ("Оплаты за месяц", self._money(revenue), "Успешные платежи", "₽"),
            ("Открытые заявки", open_tickets, "Требуют внимания", "✳"),
        ]
        card_row = tk.Frame(self.content, bg=COLORS["background"])
        card_row.pack(fill="x", pady=(0, 17))
        for title, value, note, icon in cards:
            card = tk.Frame(card_row, bg="white", padx=17, pady=15,
                            highlightbackground=COLORS["line"], highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=(0, 11))
            top = tk.Frame(card, bg="white")
            top.pack(fill="x")
            tk.Label(top, text=title, bg="white", fg="#76839b",
                     font=("Segoe UI", 9)).pack(side="left")
            tk.Label(top, text=icon, bg=COLORS["blue_light"], fg=COLORS["blue"],
                     font=("Segoe UI", 11, "bold"), padx=7, pady=4).pack(side="right")
            tk.Label(card, text=value, bg="white", fg=COLORS["navy"],
                     font=("Segoe UI", 19, "bold")).pack(anchor="w", pady=(8, 0))
            tk.Label(card, text=note, bg="white", fg="#97a2b5",
                     font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))

        lower = tk.Frame(self.content, bg=COLORS["background"])
        lower.pack(fill="both", expand=True)
        self._dashboard_panel(lower, "Последние платежи", payments,
                              ("Клиент", "Договор", "Дата", "Сумма", "Статус"),
                              lambda row: (row["full_name"], row["contract_number"],
                                           self._date(row["payment_date"]), self._money(row["amount"]),
                                           row["status"]))
        self._dashboard_panel(lower, "Обращения в поддержку", tickets,
                              ("Тема", "Клиент", "Создана", "Статус"),
                              lambda row: (row["subject"], row["full_name"],
                                           self._date(row["created_at"]), row["status"]))
        self.statusbar.configure(text="Обзор обновлён")

    def show_statistics(self):
        self.current_table = None
        self._select_nav("statistics")
        self.breadcrumb.configure(text="Управление   /   Статистика договоров")
        self._clear_content()
        self._heading(
            "Статистика договоров",
            f"Договоры, заключённые сотрудником: {self.employee['display_name']}",
        )

        panel = tk.Frame(self.content, bg="white", highlightbackground=COLORS["line"],
                         highlightthickness=1)
        panel.pack(fill="both", expand=True)
        controls = tk.Frame(panel, bg="white", padx=18, pady=14)
        controls.pack(fill="x")
        tk.Label(controls, text="Период:", bg="white", fg=COLORS["text"],
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 10))
        for key, title in (("week", "Неделя"), ("month", "Месяц"), ("year", "Год")):
            button = tk.Button(
                controls, text=title, command=lambda period=key: self._set_chart_period(period),
                relief="flat", borderwidth=0, padx=13, pady=7,
                bg=COLORS["blue"] if key == self.chart_period else "#eef1f6",
                fg="white" if key == self.chart_period else COLORS["text"],
                font=("Segoe UI", 9), cursor="hand2",
            )
            button.pack(side="left", padx=(0, 6))
        self.chart_total = tk.Label(controls, text="", bg="white", fg=COLORS["muted"],
                                    font=("Segoe UI", 9))
        self.chart_total.pack(side="right")
        self.chart_canvas = tk.Canvas(panel, bg="white", highlightthickness=0, height=440)
        self.chart_canvas.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.chart_canvas.bind("<Configure>", lambda _event: self._draw_contract_chart())
        self._draw_contract_chart()
        self.statusbar.configure(text="Статистика по договорам сотрудника")

    def _set_chart_period(self, period):
        self.chart_period = period
        self.show_statistics()

    def _contract_chart_data(self):
        today = date.today()
        if self.chart_period == "week":
            start = today.fromordinal(today.toordinal() - 6)
            bucket_starts = [today.fromordinal(start.toordinal() + index) for index in range(7)]
            labels = [day.strftime("%d.%m") for day in bucket_starts]
        elif self.chart_period == "month":
            start = today.fromordinal(today.toordinal() - 29)
            first_monday = start.fromordinal(start.toordinal() - start.weekday())
            bucket_starts = []
            bucket = first_monday
            while bucket <= today:
                bucket_starts.append(bucket)
                bucket = bucket.fromordinal(bucket.toordinal() + 7)
            labels = [max(day, start).strftime("%d.%m") for day in bucket_starts]
        else:
            start_month = date(today.year - (1 if today.month == 1 else 0),
                               12 if today.month == 1 else today.month - 1, 1)
            for _ in range(10):
                start_month = date(start_month.year - (1 if start_month.month == 1 else 0),
                                   12 if start_month.month == 1 else start_month.month - 1, 1)
            start = start_month
            bucket_starts = []
            year, month = start.year, start.month
            for _ in range(12):
                bucket_starts.append(date(year, month, 1))
                year, month = (year + 1, 1) if month == 12 else (year, month + 1)
            labels = [f"{MONTH_LABELS[day.month - 1]} {day.strftime('%y')}" for day in bucket_starts]

        with self.connect() as db:
            records = db.execute(
                "SELECT date(start_date) AS contract_day FROM contracts "
                "WHERE owner_id = ? AND employee_id = ? AND date(start_date) >= ? AND date(start_date) <= ?",
                (self.employee["id"], self.employee["id"], start.isoformat(), today.isoformat()),
            ).fetchall()
        counts = [0] * len(bucket_starts)
        for record in records:
            try:
                contract_day = date.fromisoformat(record["contract_day"])
            except (TypeError, ValueError):
                continue
            if self.chart_period == "week":
                index = (contract_day - bucket_starts[0]).days
            elif self.chart_period == "month":
                index = (contract_day - bucket_starts[0]).days // 7
            else:
                index = (contract_day.year - bucket_starts[0].year) * 12 + contract_day.month - bucket_starts[0].month
            if 0 <= index < len(counts):
                counts[index] += 1
        return labels, counts

    def _draw_contract_chart(self):
        if self.chart_canvas is None or not self.chart_canvas.winfo_exists():
            return
        canvas = self.chart_canvas
        canvas.delete("all")
        labels, counts = self._contract_chart_data()
        total = sum(counts)
        self.chart_total.configure(text=f"Всего за период: {total}")
        width = max(canvas.winfo_width(), 500)
        height = max(canvas.winfo_height(), 280)
        left, right, top, bottom = 48, 22, 38, 65
        chart_width = width - left - right
        chart_height = height - top - bottom
        max_count = max(counts, default=0)
        scale_max = max(4, ((max_count + 3) // 4) * 4)
        for step in range(5):
            value = scale_max - step * scale_max / 4
            y = top + chart_height * step / 4
            canvas.create_line(left, y, width - right, y, fill="#e9edf4")
            canvas.create_text(left - 10, y, text=str(int(value)), anchor="e",
                               fill=COLORS["muted"], font=("Segoe UI", 8))
        slot = chart_width / max(len(counts), 1)
        bar_width = min(40, slot * 0.58)
        for index, (label, count) in enumerate(zip(labels, counts)):
            center = left + slot * (index + 0.5)
            bar_height = chart_height * count / scale_max
            if count:
                canvas.create_rectangle(
                    center - bar_width / 2, top + chart_height - bar_height,
                    center + bar_width / 2, top + chart_height,
                    fill=COLORS["blue"], outline="",
                )
                canvas.create_text(center, top + chart_height - bar_height - 12,
                                   text=str(count), fill=COLORS["text"],
                                   font=("Segoe UI", 8, "bold"))
            canvas.create_text(center, top + chart_height + 17, text=label,
                               fill=COLORS["muted"], font=("Segoe UI", 8))
        if total == 0:
            canvas.create_text(width / 2, top + chart_height / 2,
                               text="За выбранный период договоров нет",
                               fill=COLORS["muted"], font=("Segoe UI", 11))

    def _dashboard_panel(self, parent, title, rows, columns, values):
        panel = tk.Frame(parent, bg="white", highlightbackground=COLORS["line"], highlightthickness=1)
        panel.pack(side="left", fill="both", expand=True, padx=(0, 11))
        tk.Label(panel, text=title, bg="white", fg=COLORS["text"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(13, 9))
        tree = ttk.Treeview(panel, columns=columns, show="headings", height=5)
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=110, minwidth=75, anchor="w")
        tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        for row in rows:
            tree.insert("", "end", values=values(row))
        if not rows:
            tk.Label(panel, text="Записей пока нет", bg="white", fg=COLORS["muted"],
                     font=("Segoe UI", 9)).pack(pady=(0, 15))

    def show_entity(self, table):
        self.current_table = table
        entity = self.entities[table]
        self._select_nav(table)
        self.breadcrumb.configure(text=f"Управление   /   {entity['label']}")
        self._clear_content()
        self.search_var.set("")
        self._heading(entity["label"], f"Управление данными: {entity['label'].lower()}",
                      ("＋  Добавить запись", self._new_record))

        toolbar = tk.Frame(self.content, bg="white", padx=14, pady=11,
                           highlightbackground=COLORS["line"], highlightthickness=1)
        toolbar.pack(fill="x", pady=(0, 0))
        tk.Label(toolbar, text=f"Список: {entity['label'].lower()}", bg="white",
                 fg=COLORS["text"], font=("Segoe UI", 10, "bold")).pack(side="left")
        search = ttk.Entry(toolbar, textvariable=self.search_var, width=32)
        search.pack(side="right", padx=(8, 0))
        search.insert(0, "")
        search.bind("<KeyRelease>", lambda _event: self._render_records())
        tk.Label(toolbar, text="Поиск:", bg="white", fg=COLORS["muted"],
                 font=("Segoe UI", 9)).pack(side="right")

        table_frame = tk.Frame(self.content, bg="white", highlightbackground=COLORS["line"],
                               highlightthickness=1)
        table_frame.pack(fill="both", expand=True)
        display = entity["display"]
        self.tree = ttk.Treeview(table_frame, columns=display, show="headings", selectmode="browse")
        for field in display:
            self.tree.heading(field, text=DISPLAY_LABELS.get(field, field))
            self.tree.column(field, width=140, minwidth=90, anchor="w")
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        y_scroll.grid(row=0, column=1, sticky="ns", pady=(8, 0))
        x_scroll.grid(row=1, column=0, sticky="ew", padx=(8, 0))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", lambda _event: self._edit_selected())
        self.tree.bind("<Return>", lambda _event: self._edit_selected())

        actions = tk.Frame(self.content, bg=COLORS["background"])
        actions.pack(fill="x", pady=(11, 0))
        self.count_label = tk.Label(actions, text="", bg=COLORS["background"],
                                    fg=COLORS["muted"], font=("Segoe UI", 8))
        self.count_label.pack(side="left")
        self._action_button(actions, "Изменить", self._edit_selected, COLORS["blue"]).pack(side="right", padx=(7, 0))
        self._action_button(actions, "Удалить", self._delete_selected, "#a8444c").pack(side="right")
        self._refresh_records()

    @staticmethod
    def _action_button(parent, text, command, color):
        return tk.Button(parent, text=text, command=command, relief="flat", borderwidth=0,
                         padx=13, pady=8, bg=color, fg="white", activeforeground="white",
                         font=("Segoe UI", 8, "bold"), cursor="hand2")

    def _reference_label(self, table, row):
        if table == "addresses":
            label = f"{row['city']}, ул. {row['street']}, д. {row['house']}"
            if row["apartment"]:
                label += f", кв. {row['apartment']}"
            return label
        return str(row[self.entities[table]["label_field"]])

    def _load_reference_options(self):
        result = {}
        with self.connect() as db:
            for table, entity in self.entities.items():
                rows = db.execute(
                    f"SELECT * FROM {table} WHERE owner_id = ? ORDER BY id DESC",
                    (self.employee["id"],),
                ).fetchall()
                result[table] = {
                    f"{row['id']} — {self._reference_label(table, row)}": row["id"]
                    for row in rows
                }
        return result

    def _refresh_records(self):
        if self.current_table is None:
            return
        with self.connect() as db:
            self.records = [dict(row) for row in db.execute(
                f"SELECT * FROM {self.current_table} WHERE owner_id = ? ORDER BY id DESC",
                (self.employee["id"],),
            )]
        self._render_records()

    def _display_value(self, field, record):
        value = record.get(field)
        if value is None or value == "":
            return "—"
        if field == "employee_id":
            if value == self.employee["id"]:
                return self.employee["display_name"]
            with self.connect() as db:
                employee = db.execute(
                    "SELECT display_name FROM employees WHERE id = ?", (value,)
                ).fetchone()
            return employee["display_name"] if employee else f"#{value}"
        definition = next((item for item in self.entities[self.current_table]["fields"]
                          if item[0] == field), None)
        if definition and definition[4]:
            value = next((label for label, item_id in self.reference_options.get(definition[4], {}).items()
                          if item_id == value), f"#{value}")
        if field in ("price", "amount"):
            return self._money(value)
        if field.endswith("_date") or field.endswith("_at"):
            return self._date(value)
        if field == "speed_mbps":
            return f"{value} Мбит/с"
        if field == "description" and len(str(value)) > 48:
            return str(value)[:45] + "..."
        return str(value)

    def _render_records(self):
        if self.current_table is None or not hasattr(self, "tree"):
            return
        self.reference_options = self._load_reference_options()
        query = self.search_var.get().strip().casefold()
        filtered = [
            record for record in self.records
            if not query or any(query in str(value or "").casefold() for value in record.values())
        ]
        self.tree.delete(*self.tree.get_children())
        for record in filtered:
            self.tree.insert("", "end", iid=str(record["id"]), values=tuple(
                self._display_value(field, record) for field in self.entities[self.current_table]["display"]
            ))
        self.count_label.configure(
            text=f"Записей: {len(filtered)}" + (f" из {len(self.records)}" if query else "")
        )

    def _new_record(self):
        self._open_record_dialog()

    def _edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Редактирование", "Выберите запись в таблице.", parent=self.root)
            return
        record_id = int(selected[0])
        record = next(item for item in self.records if item["id"] == record_id)
        self._open_record_dialog(record)

    def _open_record_dialog(self, record=None):
        table = self.current_table
        entity = self.entities[table]
        self.reference_options = self._load_reference_options()
        dialog = tk.Toplevel(self.root)
        dialog.title("Новая запись" if record is None else "Редактирование записи")
        dialog.configure(bg="white")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, True)
        dialog.geometry(f"520x{min(180 + 55 * len(entity['fields']), 700)}")

        tk.Label(dialog, text=f"{'Новая запись' if record is None else 'Редактирование'}: {entity['singular']}",
                 bg="white", fg=COLORS["navy"], font=("Segoe UI", 14, "bold")).pack(
                     anchor="w", padx=22, pady=(19, 13))
        form = tk.Frame(dialog, bg="white")
        form.pack(fill="both", expand=True, padx=22)
        controls = {}

        for index, (name, label, kind, required, reference) in enumerate(entity["fields"]):
            line = tk.Frame(form, bg="white")
            line.pack(fill="x", pady=5)
            tk.Label(line, text=label + (" *" if required else ""), width=22, anchor="w",
                     bg="white", fg="#59667d", font=("Segoe UI", 9)).pack(side="left")
            value = record.get(name) if record else None
            if kind == "reference":
                mapping = self.reference_options.get(reference, {})
                control = ttk.Combobox(line, state="readonly", values=list(mapping), width=34)
                if value is not None:
                    selected_label = next((label for label, item_id in mapping.items() if item_id == value), "")
                    control.set(selected_label)
                controls[name] = (control, "reference", mapping)
            elif kind == "status":
                statuses = STATUS_OPTIONS.get(table, ["Активен"])
                control = ttk.Combobox(line, state="readonly", values=statuses, width=34)
                control.set(value or statuses[0])
                controls[name] = (control, "status", None)
            elif kind == "employee":
                control = ttk.Entry(line, width=37)
                employee_id = value if value is not None else self.employee["id"]
                if employee_id == self.employee["id"]:
                    employee_name = self.employee["display_name"]
                else:
                    with self.connect() as db:
                        employee_row = db.execute(
                            "SELECT display_name FROM employees WHERE id = ?", (employee_id,)
                        ).fetchone()
                    employee_name = employee_row["display_name"] if employee_row else "Неизвестный сотрудник"
                control.insert(0, employee_name)
                control.configure(state="readonly")
                controls[name] = (control, "employee", None)
            else:
                control = ttk.Entry(line, width=37)
                if value is not None:
                    initial = str(value).replace("T", " ")
                elif kind == "date" and required:
                    initial = date.today().isoformat()
                elif kind == "datetime-local" and required:
                    initial = datetime.now().strftime("%Y-%m-%d %H:%M")
                else:
                    initial = ""
                control.insert(0, initial)
                controls[name] = (control, kind, None)
            control.pack(side="left", fill="x", expand=True)

        buttons = tk.Frame(dialog, bg="white")
        buttons.pack(fill="x", padx=22, pady=19)
        tk.Button(buttons, text="Отмена", command=dialog.destroy, relief="flat",
                  padx=15, pady=8, bg="#eef1f6", fg=COLORS["text"],
                  font=("Segoe UI", 9)).pack(side="right")
        tk.Button(buttons, text="Сохранить",
                  command=lambda: self._save_record(dialog, controls, record),
                  relief="flat", padx=15, pady=8, bg=COLORS["blue"], fg="white",
                  font=("Segoe UI", 9, "bold")).pack(side="right", padx=(0, 8))
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.bind("<Return>", lambda _event: self._save_record(dialog, controls, record))

    def _save_record(self, dialog, controls, record):
        values = {}
        try:
            for name, label, kind, required, _reference in self.entities[self.current_table]["fields"]:
                control, control_kind, mapping = controls[name]
                raw = control.get().strip()
                if not raw:
                    if required:
                        raise ValueError(f"Заполните поле «{label}».")
                    values[name] = None
                    continue
                if control_kind == "reference":
                    if raw not in mapping:
                        raise ValueError(f"Выберите значение поля «{label}» из списка.")
                    value = mapping[raw]
                elif control_kind == "employee":
                    value = record["employee_id"] if record else self.employee["id"]
                elif kind == "number":
                    value = int(raw)
                elif kind == "decimal":
                    value = float(raw.replace(",", "."))
                else:
                    value = raw
                values[name] = value

            if record:
                columns = list(values)
                assignments = ", ".join(f"{column} = ?" for column in columns)
                with self.connect() as db:
                    cursor = db.execute(
                        f"UPDATE {self.current_table} SET {assignments} "
                        "WHERE id = ? AND owner_id = ?",
                        [*(values[column] for column in columns), record["id"], self.employee["id"]],
                    )
                    if cursor.rowcount == 0:
                        raise ValueError("Запись недоступна для изменения.")
                message = "Изменения сохранены."
            else:
                columns = list(values)
                values["owner_id"] = self.employee["id"]
                columns.append("owner_id")
                placeholders = ", ".join("?" for _ in columns)
                with self.connect() as db:
                    db.execute(
                        f"INSERT INTO {self.current_table} ({', '.join(columns)}) VALUES ({placeholders})",
                        [values[column] for column in columns],
                    )
                message = "Запись добавлена."
        except ValueError as error:
            messagebox.showerror("Проверьте данные", str(error), parent=dialog)
            return
        except sqlite3.IntegrityError as error:
            messagebox.showerror("Не удалось сохранить", self._integrity_message(error), parent=dialog)
            return

        dialog.destroy()
        self._refresh_records()
        self.statusbar.configure(text=message)
        self.root.bell()

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Удаление", "Выберите запись в таблице.", parent=self.root)
            return
        record_id = int(selected[0])
        record = next(item for item in self.records if item["id"] == record_id)
        label = record.get(self.entities[self.current_table]["label_field"], f"№ {record_id}")
        if not messagebox.askyesno("Подтверждение удаления",
                                   f"Удалить запись «{label}»?", parent=self.root):
            return
        try:
            with self.connect() as db:
                cursor = db.execute(
                    f"DELETE FROM {self.current_table} WHERE id = ? AND owner_id = ?",
                    (record_id, self.employee["id"]),
                )
                if cursor.rowcount == 0:
                    messagebox.showerror("Удаление", "Запись недоступна для удаления.", parent=self.root)
                    return
        except sqlite3.IntegrityError as error:
            messagebox.showerror("Нельзя удалить запись", self._integrity_message(error), parent=self.root)
            return
        self._refresh_records()
        self.statusbar.configure(text="Запись удалена")

    @staticmethod
    def _integrity_message(error):
        message = str(error)
        if "UNIQUE constraint failed" in message:
            return "Такая запись уже существует. Проверьте номер договора, MAC- или IP-адрес."
        if "FOREIGN KEY constraint failed" in message:
            return "Нельзя удалить запись, пока с ней связаны другие данные."
        if "CHECK constraint failed" in message:
            return "Проверьте значение: скорость должна быть больше нуля, сумма — неотрицательной."
        return "Не удалось сохранить запись. Проверьте введённые данные."

    @staticmethod
    def _money(value):
        return f"{float(value):,.2f} ₽".replace(",", " ").replace(".", ",")

    @staticmethod
    def _date(value):
        if not value:
            return "—"
        try:
            parsed = datetime.fromisoformat(str(value).replace(" ", "T"))
            return parsed.strftime("%d.%m.%Y %H:%M" if len(str(value)) > 10 else "%d.%m.%Y")
        except ValueError:
            return str(value)


class AuthScreen:
    def __init__(self, root, authenticate, register, on_login):
        self.root = root
        self.authenticate = authenticate
        self.register = register
        self.on_login = on_login
        root.title("Вход — СЕТЬ")
        root.geometry("480x540")
        root.minsize(420, 500)
        root.configure(bg=COLORS["background"])

        card = tk.Frame(root, bg="white", padx=34, pady=32,
                        highlightbackground=COLORS["line"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=35, pady=35)
        tk.Label(card, text="⌁", bg=COLORS["blue"], fg="white",
                 font=("Segoe UI", 26, "bold"), padx=12, pady=2).pack(pady=(4, 12))
        tk.Label(card, text="СЕТЬ", bg="white", fg=COLORS["navy"],
                 font=("Segoe UI", 20, "bold")).pack()
        tk.Label(card, text="Информационная система интернет-провайдера",
                 bg="white", fg=COLORS["muted"], font=("Segoe UI", 9)).pack(pady=(5, 23))

        form = tk.Frame(card, bg="white")
        form.pack(fill="x")
        tk.Label(form, text="Логин", bg="white", fg=COLORS["text"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
        self.username = ttk.Entry(form, font=("Segoe UI", 11))
        self.username.pack(fill="x", ipady=5, pady=(0, 14))
        tk.Label(form, text="Пароль", bg="white", fg=COLORS["text"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
        self.password = ttk.Entry(form, show="•", font=("Segoe UI", 11))
        self.password.pack(fill="x", ipady=5)
        self.password.bind("<Return>", lambda _event: self._login())

        tk.Button(card, text="Войти", command=self._login, relief="flat", borderwidth=0,
                  bg=COLORS["blue"], fg="white", activebackground="#3453d1",
                  activeforeground="white", font=("Segoe UI", 10, "bold"),
                  cursor="hand2").pack(fill="x", pady=(23, 10), ipady=8)
        tk.Button(card, text="Создать аккаунт сотрудника", command=self._open_registration,
                  relief="flat", borderwidth=0, bg="white", fg=COLORS["blue"],
                  activeforeground="#3453d1", font=("Segoe UI", 9),
                  cursor="hand2").pack()
        self.username.focus_set()

    def _login(self):
        username = self.username.get().strip()
        password = self.password.get()
        if not username or not password:
            messagebox.showerror("Вход", "Введите логин и пароль.", parent=self.root)
            return
        employee = self.authenticate(username, password)
        if employee is None:
            messagebox.showerror("Вход", "Неверный логин или пароль.", parent=self.root)
            self.password.delete(0, "end")
            self.password.focus_set()
            return
        self.on_login(employee)

    def _open_registration(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Регистрация сотрудника")
        dialog.geometry("440x440")
        dialog.resizable(False, False)
        dialog.configure(bg="white")
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="Создание аккаунта", bg="white", fg=COLORS["navy"],
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=28, pady=(24, 5))
        tk.Label(dialog, text="Новый сотрудник получит отдельные данные и статистику.",
                 bg="white", fg=COLORS["muted"], font=("Segoe UI", 9)).pack(
                     anchor="w", padx=28, pady=(0, 14))
        form = tk.Frame(dialog, bg="white")
        form.pack(fill="x", padx=28)
        fields = {}
        for key, label, hidden in (
            ("display_name", "Имя сотрудника", False),
            ("username", "Логин (3–40 символов)", False),
            ("password", "Пароль (не менее 8 символов)", True),
            ("confirm", "Повторите пароль", True),
        ):
            tk.Label(form, text=label, bg="white", fg=COLORS["text"],
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(7, 4))
            entry = ttk.Entry(form, show="•" if hidden else "", font=("Segoe UI", 10))
            entry.pack(fill="x", ipady=4)
            fields[key] = entry

        def submit():
            password = fields["password"].get()
            if password != fields["confirm"].get():
                messagebox.showerror("Регистрация", "Пароли не совпадают.", parent=dialog)
                return
            try:
                employee = self.register(
                    fields["username"].get(), fields["display_name"].get(), password
                )
            except ValueError as error:
                messagebox.showerror("Регистрация", str(error), parent=dialog)
                return
            except sqlite3.IntegrityError:
                messagebox.showerror("Регистрация", "Такой логин уже зарегистрирован.", parent=dialog)
                return
            dialog.destroy()
            self.on_login(employee)

        buttons = tk.Frame(dialog, bg="white")
        buttons.pack(fill="x", padx=28, pady=20)
        tk.Button(buttons, text="Отмена", command=dialog.destroy, relief="flat",
                  padx=14, pady=8, bg="#eef1f6", fg=COLORS["text"],
                  font=("Segoe UI", 9)).pack(side="right")
        tk.Button(buttons, text="Создать аккаунт", command=submit, relief="flat",
                  padx=14, pady=8, bg=COLORS["blue"], fg="white",
                  font=("Segoe UI", 9, "bold")).pack(side="right", padx=(0, 8))
        fields["display_name"].focus_set()


def run_application(entities, connect, initialize_database, create_employee, authenticate_employee):
    initialize_database()
    root = tk.Tk()

    def show_login():
        for child in root.winfo_children():
            child.destroy()
        root.geometry("480x540")
        AuthScreen(root, authenticate_employee, create_employee, show_application)

    def show_application(employee):
        for child in root.winfo_children():
            child.destroy()
        root.geometry("1280x790")
        InternetProviderApp(root, entities, connect, employee, show_login)

    show_login()
    root.mainloop()
