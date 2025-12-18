import flet as ft
import sqlite3
from datetime import date


# ===================== DATABASE =====================

class TaskDatabase:
    def __init__(self, db_name="tasks.db"):
        self.db_name = db_name
        self.create_table()

    def connect(self):
        return sqlite3.connect(self.db_name)

    def create_table(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    is_completed INTEGER DEFAULT 0,
                    task_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def add_task(self, title, priority, task_date):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO tasks (title, priority, task_date) VALUES (?, ?, ?)",
                (title, priority, task_date),
            )

    def get_tasks(self, task_date, filter_type="ALL"):
        query = "SELECT id, title, priority, is_completed FROM tasks WHERE task_date = ?"
        params = [task_date]

        if filter_type == "COMPLETED":
            query += " AND is_completed = 1"
        elif filter_type == "PENDING":
            query += " AND is_completed = 0"

        with self.connect() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def update_task(self, task_id, is_completed):
        with self.connect() as conn:
            conn.execute(
                "UPDATE tasks SET is_completed = ? WHERE id = ?",
                (int(is_completed), task_id),
            )

    def delete_task(self, task_id):
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM tasks WHERE id = ?",
                (task_id,),
            )


# ===================== TASK ITEM =====================

class TaskItem(ft.Row):
    PRIORITY_COLORS = {
        "Low": "green",
        "Medium": "orange",
        "High": "red",
    }

    def __init__(self, task_id, title, priority, is_completed, db, refresh):
        super().__init__()
        self.task_id = task_id
        self.db = db
        self.refresh = refresh

        self.checkbox = ft.Checkbox(
            label=f"[{priority}] {title}",
            value=bool(is_completed),
            expand=True,
            on_change=self.toggle,
        )

        self.delete_btn = ft.IconButton(
            icon=ft.Icons.DELETE,
            icon_color="red",
            on_click=self.delete,
        )

        self.controls = [self.checkbox, self.delete_btn]
        self.alignment = ft.MainAxisAlignment.SPACE_BETWEEN

        self.checkbox.label_style = ft.TextStyle(
            color=self.PRIORITY_COLORS.get(priority),
            decoration=ft.TextDecoration.LINE_THROUGH
            if is_completed else None,
        )

    def toggle(self, e):
        self.db.update_task(self.task_id, self.checkbox.value)
        self.refresh()

    def delete(self, e):
        self.db.delete_task(self.task_id)
        self.refresh()


# ===================== MAIN APP =====================

class TaskManagerApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.db = TaskDatabase()
        self.selected_date = date.today().isoformat()
        self.current_filter = "ALL"

        self.page.title = "Advanced Task Manager"
        self.page.window_width = 420
        self.page.window_height = 650

        # Inputs
        self.task_input = ft.TextField(
            hint_text="Task description",
            expand=True,
        )

        self.priority_dropdown = ft.Dropdown(
            width=120,
            value="Medium",
            options=[
                ft.dropdown.Option("Low"),
                ft.dropdown.Option("Medium"),
                ft.dropdown.Option("High"),
            ],
        )

        self.add_btn = ft.IconButton(
            icon=ft.Icons.ADD,
            icon_color="green",
            on_click=self.add_task,
        )

        # Date picker
        self.date_text = ft.Text(self.selected_date)
        self.date_picker = ft.DatePicker(
            on_change=self.change_date,
        )
        self.page.overlay.append(self.date_picker)

        # Filters
        self.filter_tabs = ft.Tabs(
            selected_index=0,
            on_change=self.change_filter,
            tabs=[
                ft.Tab(text="All"),
                ft.Tab(text="Completed"),
                ft.Tab(text="Pending"),
            ],
        )

        self.tasks_column = ft.Column(expand=True, spacing=5)

        self.build_ui()
        self.load_tasks()

    def build_ui(self):
        self.page.add(
            ft.Column(
                [
                    ft.Text("📝 Task Manager", size=24, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.TextButton(
                                "📅 Select Date",
                                on_click=lambda e: self.date_picker.pick_date(),
                            ),
                            self.date_text,
                        ]
                    ),
                    ft.Row([self.task_input, self.priority_dropdown, self.add_btn]),
                    self.filter_tabs,
                    ft.Divider(),
                    self.tasks_column,
                ],
                expand=True,
            )
        )

    # ===================== LOGIC =====================

    def load_tasks(self):
        self.tasks_column.controls.clear()

        tasks = self.db.get_tasks(self.selected_date, self.current_filter)
        for task_id, title, priority, is_completed in tasks:
            self.tasks_column.controls.append(
                TaskItem(
                    task_id,
                    title,
                    priority,
                    is_completed,
                    self.db,
                    self.load_tasks,
                )
            )

        self.page.update()

    def add_task(self, e):
        title = self.task_input.value.strip()
        if not title:
            return

        self.db.add_task(title, self.priority_dropdown.value, self.selected_date)
        self.task_input.value = ""
        self.load_tasks()

    def change_date(self, e):
        self.selected_date = e.control.value.strftime("%Y-%m-%d")
        self.date_text.value = self.selected_date
        self.load_tasks()

    def change_filter(self, e):
        index = e.control.selected_index
        self.current_filter = ["ALL", "COMPLETED", "PENDING"][index]
        self.load_tasks()


# ===================== ENTRY =====================

def main(page: ft.Page):
    TaskManagerApp(page)


ft.app(target=main)
