
import sqlite3
import math
import tkinter as tk

from pathlib import Path
from datetime import date, datetime
from tkinter import ttk, messagebox

 
# 1. CONFIGURATION

DATABASE_PATH = Path(__file__).resolve().parent / "finance.db"

COLORS = {
    "navy": "#172554",
    "sidebar": "#172554",
    "blue": "#2563EB",
    "blue_light": "#DBEAFE",
    "background": "#F4F6FA",
    "white": "#FFFFFF",
    "text": "#0D0D0D",
    "muted": "#64748B",
    "green": "#16A34A",
    "red": "#DC2626",
    "border": "#E2E8F0",
    "orange": "#D97706"
}

INCOME_CATEGORIES = [
    "Salary",
    "Freelance",
    "Business",
    "Teaching",
    "Investments",
    "Gifts",
    "Other"
]

EXPENSE_CATEGORIES = [
    "Food",
    "Transport",
    "Rent",
    "Shopping",
    "Health",
    "Education",
    "Entertainment",
    "Bills",
    "Other"
]


# 2. DATABASE CLASS

class FinanceDatabase:

    def __init__(self, database_path):

        self.connection = sqlite3.connect(database_path)

        self.create_table()


    def create_table(self):

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL
            )
        """)

        self.connection.commit()

    # ADD TRANSACTION

    def add_transaction(
        self,
        transaction_type,
        description,
        category,
        amount,
        transaction_date
    ):

        self.connection.execute("""
            INSERT INTO transactions
            (type, description, category, amount, date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            transaction_type,
            description,
            category,
            amount,
            transaction_date
        ))

        self.connection.commit()

    # UPDATE TRANSACTION

    def update_transaction(
        self,
        transaction_id,
        transaction_type,
        description,
        category,
        amount,
        transaction_date
    ):

        self.connection.execute("""
            UPDATE transactions
            SET
                type = ?,
                description = ?,
                category = ?,
                amount = ?,
                date = ?
            WHERE id = ?
        """, (
            transaction_type,
            description,
            category,
            amount,
            transaction_date,
            transaction_id
        ))

        self.connection.commit()

    # DELETE TRANSACTION

    def delete_transaction(self, transaction_id):

        self.connection.execute("""
            DELETE FROM transactions
            WHERE id = ?
        """, (transaction_id,))

        self.connection.commit()

    # GET ONE TRANSACTION

    def get_transaction(self, transaction_id):

        cursor = self.connection.execute("""
            SELECT *
            FROM transactions
            WHERE id = ?
        """, (transaction_id,))

        return cursor.fetchone()

    # GET ALL TRANSACTIONS

    def get_transactions(self, limit=None):

        if limit is None:

            cursor = self.connection.execute("""
                SELECT *
                FROM transactions
                ORDER BY id DESC
            """)

        else:

            cursor = self.connection.execute("""
                SELECT *
                FROM transactions
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))

        return cursor.fetchall()

    # GET FINANCIAL SUMMARY

    def get_summary(self):

        cursor = self.connection.execute("""
            SELECT

                COALESCE(
                    SUM(
                        CASE
                            WHEN type = 'Income'
                            THEN amount
                            ELSE 0
                        END
                    ), 0
                ),

                COALESCE(
                    SUM(
                        CASE
                            WHEN type = 'Expense'
                            THEN amount
                            ELSE 0
                        END
                    ), 0
                )

            FROM transactions
        """)

        total_income, total_expenses = cursor.fetchone()

        balance = total_income - total_expenses

        return total_income, total_expenses, balance

    # GET MONTHLY FINANCIAL SUMMARIES

    def get_monthly_summaries(self):

        cursor = self.connection.execute("""
            SELECT

                strftime('%Y-%m', date) AS month,

                COALESCE(
                    SUM(
                        CASE
                            WHEN type = 'Income'
                            THEN amount
                            ELSE 0
                        END
                    ), 0
                ),

                COALESCE(
                    SUM(
                        CASE
                            WHEN type = 'Expense'
                            THEN amount
                            ELSE 0
                        END
                    ), 0
                )

            FROM transactions

            GROUP BY strftime('%Y-%m', date)

            ORDER BY month DESC
        """)

        return cursor.fetchall()

    # CLOSE DATABASE

    def close(self):

        self.connection.close()


# 3. MAIN APPLICATION CLASS

class PersonalFinanceApp:


    def __init__(self, root, database):

        self.root = root
        self.db = database

        self.current_page = "dashboard"

        self.setup_window()
        self.setup_styles()
        self.build_sidebar()
        self.build_pages()

        self.refresh_all()
        self.show_page("dashboard")

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close_application
        )


    # ========================================================
    # WINDOW CONFIGURATION
    # ========================================================

    def setup_window(self):

        self.root.title("Personal Finance Tracker")
        self.root.geometry("1180x760")
        self.root.minsize(1000, 650)
        self.root.configure(bg=COLORS["background"])


    # TTK STYLES

    def setup_styles(self):

        style = ttk.Style()

        style.theme_use("clam")

        style.configure(
            "Finance.Treeview",
            background=COLORS["white"],
            foreground=COLORS["text"],
            rowheight=38,
            fieldbackground=COLORS["white"],
            font=("Inter", 10)
        )

        style.configure(
            "Finance.Treeview.Heading",
            background="#E9EEF6",
            foreground=COLORS["text"],
            font=("Inter", 10, "bold"),
            padding=10
        )

        style.map(
            "Finance.Treeview",
            background=[("selected", COLORS["blue_light"])],
            foreground=[("selected", COLORS["text"])]
        )

        style.configure(
            "Finance.TButton",
            font=("Inter", 10),
            padding=8
        )


    # SIDEBAR

    def build_sidebar(self):

        self.sidebar = tk.Frame(
            self.root,
            bg=COLORS["sidebar"],
            width=230
        )

        self.sidebar.pack(side="left", fill="y")

        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="FINTRACK",
            font=("Inter", 20, "bold"),
            fg=COLORS["white"],
            bg=COLORS["sidebar"]
        ).pack(pady=(35, 5))

        tk.Label(
            self.sidebar,
            text="PERSONAL FINANCE TRACKER",
            font=("Inter", 8),
            fg="#93C5FD",
            bg=COLORS["sidebar"]
        ).pack(pady=(0, 40))


        # Navigation buttons

        self.create_navigation_button(
            "Dashboard",
            lambda: self.show_page("dashboard")
        )

        self.create_navigation_button(
                    "Add Income",
                    lambda: self.open_transaction_form("Income")
        )

        self.create_navigation_button(
                    "Add Expense",
                    lambda: self.open_transaction_form("Expense")
        )

        self.create_navigation_button(
            "View Transactions",
            lambda: self.show_page("transactions")
        )

        self.create_navigation_button(
            "Monthly Summary",
            lambda: self.show_page("monthly")
        )

        # Exit button

        tk.Frame(
            self.sidebar,
            bg=COLORS["sidebar"],
            height=30
        ).pack()

        self.create_navigation_button(
            "Exit Application",
            self.close_application
        )


    def create_navigation_button(self, text, command):

        button = tk.Button(
            self.sidebar,
            text=text,
            command=command,
            font=("Inter", 11),
            fg=COLORS["white"],
            bg=COLORS["sidebar"],
            activebackground="#263D70",
            activeforeground=COLORS["white"],
            relief="flat",
            anchor="w",
            padx=25,
            pady=13,
            cursor="hand2"
        )

        button.pack(fill="x", padx=8, pady=3)

    # PAGE CONTAINER

    def build_pages(self):

        self.content = tk.Frame(
            self.root,
            bg=COLORS["background"]
        )

        self.content.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.page_container = tk.Frame(
            self.content,
            bg=COLORS["background"]
        )

        self.page_container.pack(
            fill="both",
            expand=True
        )

        self.dashboard_page = tk.Frame(
            self.page_container,
            bg=COLORS["background"]
        )

        self.transactions_page = tk.Frame(
            self.page_container,
            bg=COLORS["background"]
        )

        self.monthly_page = tk.Frame(
            self.page_container,
            bg=COLORS["background"]
        )

        for page in (
            self.dashboard_page,
            self.transactions_page,
            self.monthly_page
        ):

            page.place(
                relx=0,
                rely=0,
                relwidth=1,
                relheight=1
            )

        self.build_dashboard_page()
        self.build_transactions_page()
        self.build_monthly_page()


    # PAGE HEADER

    def create_page_header(self, parent, title, subtitle):

        header = tk.Frame(
            parent,
            bg=COLORS["background"]
        )

        header.pack(
            fill="x",
            padx=30,
            pady=(25, 20)
        )

        tk.Label(
            header,
            text=title,
            font=("Manrope", 24, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        ).pack(anchor="w")

        tk.Label(
            header,
            text=subtitle,
            font=("Manrope", 10),
            fg=COLORS["muted"],
            bg=COLORS["background"]
        ).pack(anchor="w", pady=(5, 0))

    # REUSABLE SUMMARY CARD

    def create_summary_card(
        self,
        parent,
        title,
        color,
        column
    ):

        card = tk.Frame(
            parent,
            bg=COLORS["white"],
            padx=20,
            pady=20,
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )

        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=7,
            pady=5
        )

        tk.Label(
            card,
            text=title,
            font=("Inter", 10),
            fg=COLORS["muted"],
            bg=COLORS["white"]
        ).pack(anchor="w")

        value_label = tk.Label(
            card,
            text="GHS 0.00",
            font=("Inter", 19, "bold"),
            fg=color,
            bg=COLORS["white"]
        )

        value_label.pack(anchor="w", pady=(12, 0))

        return value_label


    # REUSABLE TREEVIEW

    def create_table(self, parent, columns, headings, widths):

        container = tk.Frame(parent, bg=COLORS["white"])

        container.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15)
        )

        tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            style="Finance.Treeview",
            selectmode="browse"
        )

        for column in columns:

            tree.heading(
                column,
                text=headings[column]
            )

            tree.column(
                column,
                width=widths[column],
                anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=tree.yview
        )

        tree.configure(
            yscrollcommand=scrollbar.set
        )

        tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        tree.tag_configure(
            "income",
            foreground=COLORS["green"]
        )

        tree.tag_configure(
            "expense",
            foreground=COLORS["red"]
        )

        tree.tag_configure(
            "positive",
            foreground=COLORS["green"]
        )

        tree.tag_configure(
            "negative",
            foreground=COLORS["red"]
        )

        return tree


    # DASHBOARD PAGE

    def build_dashboard_page(self):

        page = self.dashboard_page

        self.create_page_header(
            page,
            "Dashboard",
            "Welcome! Here's an overview of your finances."
        )

        # Summary cards

        cards_frame = tk.Frame(
            page,
            bg=COLORS["background"]
        )

        cards_frame.pack(
            fill="x",
            padx=30,
            pady=10
        )

        for column in range(3):

            cards_frame.grid_columnconfigure(
                column,
                weight=1
            )

        self.balance_label = self.create_summary_card(
            cards_frame,
            "Available Balance",
            COLORS["blue"],
            0
        )

        self.income_label = self.create_summary_card(
            cards_frame,
            "Total Income",
            COLORS["green"],
            1
        )

        self.expense_label = self.create_summary_card(
            cards_frame,
            "Total Expenses",
            COLORS["red"],
            2
        )

        # Recent transactions container

        table_panel = tk.Frame(
            page,
            bg=COLORS["white"],
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )

        table_panel.pack(
            fill="both",
            expand=True,
            padx=37,
            pady=(20, 25)
        )

        heading = tk.Frame(
            table_panel,
            bg=COLORS["white"]
        )

        heading.pack(
            fill="x",
            padx=20,
            pady=18
        )

        tk.Label(
            heading,
            text="Recent Transactions",
            font=("Inter", 15, "bold"),
            bg=COLORS["white"],
            fg=COLORS["text"]
        ).pack(side="left")

        ttk.Button(
            heading,
            text="View All",
            style="Finance.TButton",
            command=lambda: self.show_page("transactions")
        ).pack(side="right")

        columns = (
            "id",
            "type",
            "description",
            "category",
            "amount",
            "date"
        )

        headings = {
            "id": "ID",
            "type": "TYPE",
            "description": "DESCRIPTION",
            "category": "CATEGORY",
            "amount": "AMOUNT",
            "date": "DATE"
        }

        widths = {
            "id": 50,
            "type": 90,
            "description": 170,
            "category": 120,
            "amount": 120,
            "date": 120
        }

        self.recent_tree = self.create_table(
            table_panel,
            columns,
            headings,
            widths
        )


    # TRANSACTIONS PAGE

    def build_transactions_page(self):

        page = self.transactions_page

        self.create_page_header(
            page,
            "Transactions",
            "Your Activity."
        )

        # Action buttons

        toolbar = tk.Frame(
            page,
            bg=COLORS["background"]
        )

        toolbar.pack(
            fill="x",
            padx=30,
            pady=(0, 15)
        )

        ttk.Button(
            toolbar,
            text="Edit Selected",
            command=self.edit_selected_transaction
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            toolbar,
            text="Delete Selected",
            command=self.delete_selected_transaction
        ).pack(side="left", padx=8)

        ttk.Button(
            toolbar,
            text="Refresh",
            command=self.refresh_all
        ).pack(side="right")

        # Transaction table

        panel = tk.Frame(
            page,
            bg=COLORS["white"],
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )

        panel.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 25)
        )

        self.transactions_tree = self.create_table(
            panel,
            (
                "id",
                "type",
                "description",
                "category",
                "amount",
                "date"
            ),
            {
                "id": "ID",
                "type": "TYPE",
                "description": "DESCRIPTION",
                "category": "CATEGORY",
                "amount": "AMOUNT",
                "date": "DATE"
            },
            {
                "id": 50,
                "type": 100,
                "description": 190,
                "category": 130,
                "amount": 130,
                "date": 130
            }
        )

        self.transactions_tree.bind(
            "<Double-1>",
            lambda event: self.edit_selected_transaction()
        )

    # MONTHLY SUMMARY PAGE
    
    def build_monthly_page(self):

        page = self.monthly_page

        self.create_page_header(
            page,
            "Monthly Financial Summary",
            "View your monthly income, expenses and net savings."
        )

        panel = tk.Frame(
            page,
            bg=COLORS["white"],
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )

        panel.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(5, 25)
        )

        self.monthly_tree = self.create_table(
            panel,
            (
                "month",
                "income",
                "expenses",
                "net"
            ),
            {
                "month": "MONTH",
                "income": "TOTAL INCOME",
                "expenses": "TOTAL EXPENSES",
                "net": "NET SAVINGS"
            },
            {
                "month": 180,
                "income": 200,
                "expenses": 200,
                "net": 200
            }
        )

        self.monthly_tree.tag_configure(
            "positive",
            foreground=COLORS["green"]
        )

        self.monthly_tree.tag_configure(
            "negative",
            foreground=COLORS["red"]
        )

    # NAVIGATION

    def show_page(self, page_name):

        self.current_page = page_name

        pages = {
            "dashboard": self.dashboard_page,
            "transactions": self.transactions_page,
            "monthly": self.monthly_page
        }

        pages[page_name].tkraise()

        self.refresh_all()

    # REFRESH DASHBOARD CARDS

    def refresh_summary_cards(self):

        total_income, total_expenses, balance = (
            self.db.get_summary()
        )

        self.balance_label.config(
            text=f"GHS {balance:,.2f}"
        )

        self.income_label.config(
            text=f"GHS {total_income:,.2f}"
        )

        self.expense_label.config(
            text=f"GHS {total_expenses:,.2f}"
        )

    # POPULATE TRANSACTION TABLE

    def populate_transaction_table(self, tree, records):

        for item in tree.get_children():

            tree.delete(item)

        for record in records:

            transaction_id = record[0]
            transaction_type = record[1]

            tag = (
                "income"
                if transaction_type == "Income"
                else "expense"
            )

            tree.insert(
                "",
                "end",
                values=(
                    transaction_id,
                    transaction_type,
                    record[2],
                    record[3],
                    f"GHS {record[4]:,.2f}",
                    record[5]
                ),
                tags=(tag,)
            )


    # POPULATE MONTHLY SUMMARY TABLE

    def populate_monthly_table(self):

        for item in self.monthly_tree.get_children():

            self.monthly_tree.delete(item)

        records = self.db.get_monthly_summaries()

        for record in records:

            month_string = record[0]

            try:

                month_name = datetime.strptime(
                    month_string,
                    "%Y-%m"
                ).strftime("%B %Y")

            except ValueError:

                month_name = month_string

            income = record[1]
            expenses = record[2]

            net_savings = income - expenses

            tag = (
                "positive"
                if net_savings >= 0
                else "negative"
            )

            self.monthly_tree.insert(
                "",
                "end",
                values=(
                    month_name,
                    f"GHS {income:,.2f}",
                    f"GHS {expenses:,.2f}",
                    f"GHS {net_savings:,.2f}"
                ),
                tags=(tag,)
            )


    # REFRESH ALL APPLICATION DATA

    def refresh_all(self):

        self.refresh_summary_cards()

        recent_records = self.db.get_transactions(limit=8)

        self.populate_transaction_table(
            self.recent_tree,
            recent_records
        )

        all_records = self.db.get_transactions()

        self.populate_transaction_table(
            self.transactions_tree,
            all_records
        )

        self.populate_monthly_table()


    # ADD / EDIT TRANSACTION FORM

    def open_transaction_form(
        self,
        transaction_type="Income",
        existing_transaction=None
    ):

        is_editing = existing_transaction is not None

        form = tk.Toplevel(self.root)

        if is_editing:

            form.title("Edit Transaction")

        else:

            form.title(f"Add {transaction_type}")

        form.geometry("450x570")
        form.resizable(False, False)
        form.configure(bg=COLORS["background"])

        form.transient(self.root)
        form.grab_set()

        # Existing transaction details

        if is_editing:

            transaction_id = existing_transaction[0]
            transaction_type = existing_transaction[1]
            old_amount = existing_transaction[4]

            description = existing_transaction[2]
            category = existing_transaction[3]
            amount = existing_transaction[4]
            transaction_date = existing_transaction[5]

        else:

            transaction_id = None
            old_amount = 0

            description = ""
            category = ""

            amount = ""
            transaction_date = str(date.today())


        # Heading

        title = (
            "Edit Transaction"
            if is_editing
            else f"Add {transaction_type}"
        )

        tk.Label(
            form,
            text=title,
            font=("Inter", 20, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"]
        ).pack(pady=(25, 5))

        tk.Label(
            form,
            text="Enter the transaction details below.",
            font=("Inter", 9),
            fg=COLORS["muted"],
            bg=COLORS["background"]
        ).pack(pady=(0, 20))


        # Form body

        body = tk.Frame(
            form,
            bg=COLORS["background"]
        )

        body.pack(
            fill="x",
            padx=35
        )


        # Transaction type

        tk.Label(
            body,
            text="Transaction Type",
            bg=COLORS["background"],
            fg=COLORS["text"]
        ).pack(anchor="w")

        type_var = tk.StringVar(value=transaction_type)

        type_entry = ttk.Combobox(
            body,
            textvariable=type_var,
            values=("Income", "Expense"),
            state="readonly"
        )

        type_entry.pack(
            fill="x",
            pady=(5, 13)
        )


        # Amount

        tk.Label(
            body,
            text="Amount (GHS)",
            bg=COLORS["background"],
            fg=COLORS["text"]
        ).pack(anchor="w")

        amount_entry = ttk.Entry(body)

        amount_entry.pack(
            fill="x",
            pady=(5, 13)
        )

        amount_entry.insert(0, str(amount))


        # Description

        tk.Label(
            body,
            text="Description",
            bg=COLORS["background"],
            fg=COLORS["text"]
        ).pack(anchor="w")

        description_entry = ttk.Entry(body)

        description_entry.pack(
            fill="x",
            pady=(5, 13)
        )

        description_entry.insert(0, description)


        # Category

        tk.Label(
            body,
            text="Category",
            bg=COLORS["background"],
            fg=COLORS["text"]
        ).pack(anchor="w")

        all_categories = list(
            dict.fromkeys(
                INCOME_CATEGORIES + EXPENSE_CATEGORIES
            )
        )

        category_entry = ttk.Combobox(
            body,
            values=all_categories,
            state="normal"
        )

        category_entry.pack(
            fill="x",
            pady=(5, 13)
        )

        category_entry.set(category)


        # Date

        tk.Label(
            body,
            text="Transaction Date (YYYY-MM-DD)",
            bg=COLORS["background"],
            fg=COLORS["text"]
        ).pack(anchor="w")

        date_entry = ttk.Entry(body)

        date_entry.pack(
            fill="x",
            pady=(5, 20)
        )

        date_entry.insert(0, transaction_date)


        # SAVE / UPDATE TRANSACTION

        def submit_transaction():

            try:

                new_amount = float(
                    amount_entry.get().strip()
                )

            except ValueError:

                messagebox.showerror(
                    "Invalid Amount",
                    "Please enter a valid numerical amount.",
                    parent=form
                )

                return


            if not math.isfinite(new_amount) or new_amount <= 0:

                messagebox.showerror(
                    "Invalid Amount",
                    "Amount must be a positive number.",
                    parent=form
                )

                return


            new_type = type_var.get()

            new_description = (
                description_entry.get().strip()
            )

            new_category = (
                category_entry.get().strip()
            )

            new_date = date_entry.get().strip()


            if not new_description or not new_category:

                messagebox.showerror(
                    "Missing Information",
                    "Description and category are required.",
                    parent=form
                )

                return


            # Validate date

            try:

                parsed_date = date.fromisoformat(new_date)

                new_date = parsed_date.isoformat()

            except ValueError:

                messagebox.showerror(
                    "Invalid Date",
                    "Enter the date in YYYY-MM-DD format.",
                    parent=form
                )

                return


            # Check available balance for expenses.
            # When editing, exclude the original transaction
            # from the balance calculation.

            if new_type == "Expense":

                _, _, available_balance = self.db.get_summary()

                if is_editing:

                    if existing_transaction[1] == "Income":

                        available_balance -= old_amount

                    elif existing_transaction[1] == "Expense":

                        available_balance += old_amount


                if new_amount > available_balance:

                    messagebox.showwarning(
                        "Insufficient Balance",
                        (
                            "This expense exceeds your available "
                            "balance."
                        ),
                        parent=form
                    )

                    return


            # Save or update in SQLite

            try:

                if is_editing:

                    self.db.update_transaction(
                        transaction_id,
                        new_type,
                        new_description,
                        new_category,
                        new_amount,
                        new_date
                    )

                    success_message = (
                        "Transaction updated successfully!"
                    )

                else:

                    self.db.add_transaction(
                        new_type,
                        new_description,
                        new_category,
                        new_amount,
                        new_date
                    )

                    success_message = (
                        "Transaction added successfully!"
                    )


            except sqlite3.Error as error:

                messagebox.showerror(
                    "Database Error",
                    str(error),
                    parent=form
                )

                return


            # Refresh application data

            self.refresh_all()

            messagebox.showinfo(
                "Success",
                success_message,
                parent=form
            )

            form.destroy()


        # Buttons

        button_text = (
            "Update Transaction"
            if is_editing
            else "Save Transaction"
        )

        ttk.Button(
            form,
            text=button_text,
            command=submit_transaction
        ).pack(
            fill="x",
            padx=35,
            pady=(5, 25)
        )

        amount_entry.focus_set()

        form.bind(
            "<Return>",
            lambda event: submit_transaction()
        )

    # SELECTED TRANSACTION

    def get_selected_transaction_id(self):

        selected = self.transactions_tree.selection()

        if not selected:

            messagebox.showwarning(
                "No Selection",
                "Please select a transaction first."
            )

            return None

        values = self.transactions_tree.item(
            selected[0],
            "values"
        )

        return int(values[0])

    # EDIT SELECTED TRANSACTION

    def edit_selected_transaction(self):

        transaction_id = (
            self.get_selected_transaction_id()
        )

        if transaction_id is None:

            return

        transaction = self.db.get_transaction(
            transaction_id
        )

        if transaction is None:

            messagebox.showerror(
                "Not Found",
                "This transaction could not be found."
            )

            self.refresh_all()

            return

        self.open_transaction_form(
            existing_transaction=transaction
        )

    # DELETE SELECTED TRANSACTION

    def delete_selected_transaction(self):

        transaction_id = (
            self.get_selected_transaction_id()
        )

        if transaction_id is None:

            return

        confirmed = messagebox.askyesno(
            "Confirm Deletion",
            (
                f"Are you sure you want to delete "
                f"transaction #{transaction_id}?"
            )
        )

        if not confirmed:

            return

        try:

            self.db.delete_transaction(transaction_id)

        except sqlite3.Error as error:

            messagebox.showerror(
                "Database Error",
                str(error)
            )

            return

        self.refresh_all()

        messagebox.showinfo(
            "Deleted",
            "Transaction deleted successfully."
        )

    # CLOSE APPLICATION

    def close_application(self):

        confirmed = messagebox.askyesno(
            "Exit",
            "Are you sure you want to close the application?"
        )

        if not confirmed:

            return

        self.db.close()

        self.root.destroy()


# 4. APPLICATION ENTRY POINT

if __name__ == "__main__":

    database = FinanceDatabase(DATABASE_PATH)

    root = tk.Tk()

    app = PersonalFinanceApp(root, database)

    root.mainloop()
