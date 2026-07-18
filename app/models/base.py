"""Core database base class: connection handling, schema creation, hashing.

Method bodies moved verbatim from the original database.py.
"""
import sqlite3
import hashlib


class DatabaseBase:
    def __init__(self, db_name='project_tracking.db'):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create tbl_employee
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbl_employee (
                emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                gender TEXT NOT NULL,
                dob DATE NOT NULL,
                address TEXT NOT NULL,
                phone_no TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                emp_type TEXT DEFAULT 'emp',
                inserted_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create tbl_project
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbl_project (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                priority TEXT NOT NULL,
                project_desc TEXT,
                project_status TEXT DEFAULT 'active',
                start_date DATE NOT NULL,
                end_date DATE,
                inserted_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create tbl_task
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbl_task (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                emp_id INTEGER NOT NULL,
                task_desc TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                start_date DATE NOT NULL,
                end_date DATE,
                inserted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES tbl_project (project_id),
                FOREIGN KEY (emp_id) REFERENCES tbl_employee (emp_id)
            )
        ''')

        # Create tbl_task_details
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbl_task_details (
                detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                desc TEXT NOT NULL,
                inserted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'incomplete',
                FOREIGN KEY (task_id) REFERENCES tbl_task (task_id)
            )
        ''')

        # -- Leave types master -------------------------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbl_leave_type (
                leave_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                leave_type     TEXT NOT NULL UNIQUE CHECK (LENGTH(leave_type)<=50),
                inserted_date  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # -- Leave requests -----------------------------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbl_leave_request (
                request_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                leave_type_id   INTEGER NOT NULL,
                employee_id     INTEGER NOT NULL,
                start_date      DATE    NOT NULL,
                end_date        DATE    NOT NULL,
                leave_desc      TEXT    CHECK (LENGTH(leave_desc)<=500),
                manager_id      INTEGER,
                comments        TEXT    CHECK (LENGTH(comments)<=200),
                status          TEXT    DEFAULT 'pending',   -- pending/approved/rejected
                inserted_date   DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (leave_type_id) REFERENCES tbl_leave_type(leave_type_id),
                FOREIGN KEY (employee_id)  REFERENCES tbl_employee(emp_id),
                FOREIGN KEY (manager_id)   REFERENCES tbl_employee(emp_id)
            )
        ''')

        # ------------------ Expense types master --------------------------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbl_expense_type (
                expense_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_type    TEXT NOT NULL UNIQUE,            -- duplication guard
                inserted_date   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ------------------ Expenses --------------------------------------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbl_expenses (
                expense_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_type_id   INTEGER NOT NULL,
                employee_id       INTEGER NOT NULL,
                exp_description   TEXT CHECK (LENGTH(exp_description)<=500),
                manager_id        INTEGER,                      -- who will approve
                approver_comments TEXT CHECK (LENGTH(approver_comments)<=200),
                given_by_id       INTEGER,                      -- who reimbursed / paid
                final_comments    TEXT CHECK (LENGTH(final_comments)<=200),
                status            TEXT  DEFAULT 'pending',      -- pending/approved/rejected
                inserted_date     DATETIME DEFAULT CURRENT_TIMESTAMP,
                amount            REAL,

                FOREIGN KEY (expense_type_id) REFERENCES tbl_expense_type(expense_type_id),
                FOREIGN KEY (employee_id)     REFERENCES tbl_employee(emp_id),
                FOREIGN KEY (manager_id)      REFERENCES tbl_employee(emp_id),
                FOREIGN KEY (given_by_id)     REFERENCES tbl_employee(emp_id)
            )
        ''')

        # ------------------ Sub Expense types master --------------------------------
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tbl_sub_expense_type (
            sub_expense_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_type_id INTEGER NOT NULL,
            sub_expense_type TEXT NOT NULL,
            inserted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (expense_type_id) REFERENCES tbl_expense_type(expense_type_id) ON DELETE CASCADE,
            UNIQUE(expense_type_id, sub_expense_type)
        )
        ''')

        # Add new columns to tbl_expenses (wrapped in try-except to avoid errors if columns exist)
        try:
            cursor.execute('ALTER TABLE tbl_expenses ADD COLUMN sub_expense_type_id INTEGER REFERENCES tbl_sub_expense_type(sub_expense_type_id)')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('ALTER TABLE tbl_expenses ADD COLUMN po_no TEXT')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('ALTER TABLE tbl_expenses ADD COLUMN bill_status TEXT')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('ALTER TABLE tbl_expenses ADD COLUMN expense_by TEXT')
        except sqlite3.OperationalError:
            pass

                # ------------------ Wiki Category --------------------------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS TblWikiCategory (
                CategoryId INTEGER PRIMARY KEY AUTOINCREMENT,
                Category   TEXT    NOT NULL,
                CatImg     TEXT,
                inserted_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ------------------ Wiki Page ------------------------------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS TblWikiPage (
                WikiId       INTEGER PRIMARY KEY AUTOINCREMENT,
                CategoryId   INTEGER NOT NULL,
                Title        TEXT    NOT NULL,
                Descri       TEXT,
                InsertedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                RowStatus    INTEGER DEFAULT 0,
                FOREIGN KEY (CategoryId) REFERENCES TblWikiCategory(CategoryId)
            )
        ''')
            # ------------------ Wiki Views --------------------------------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS TblWikiViews (
                WikiViewId   INTEGER PRIMARY KEY AUTOINCREMENT,
                WikiId       INTEGER NOT NULL,
                EmployeeId   INTEGER NOT NULL,
                ViewDateTime DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (WikiId)     REFERENCES TblWikiPage(WikiId),
                FOREIGN KEY (EmployeeId) REFERENCES tbl_employee(emp_id)
            )
        ''')


        conn.commit()

        # Create default admin user if not exists
        cursor.execute('SELECT COUNT(*) FROM tbl_employee WHERE emp_type = "admin"')
        admin_count = cursor.fetchone()[0]

        if admin_count == 0:
            hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute('''
                INSERT INTO tbl_employee
                (first_name, last_name, gender, dob, address, phone_no, email, password, emp_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('Admin', 'User', 'Male', '1990-01-01', 'Admin Address', '1234567890',
                  'admin@company.com', hashed_password, 'admin'))
            conn.commit()

        cursor.execute('''
                CREATE TABLE IF NOT EXISTS TblEmployeeProfile (
                    ProfileId INTEGER PRIMARY KEY AUTOINCREMENT,
                    EmployeeId INTEGER NOT NULL UNIQUE,
                    UANNo TEXT,
                    PANNO TEXT,
                    AadharNo TEXT,
                    BankName TEXT,
                    BranchName TEXT,
                    ACNo TEXT,
                    IFSCode TEXT,
                    Designation TEXT,
                    EmgContact TEXT,
                    ReportingMng TEXT,
                    DOJ DATE,
                    PrgLng TEXT,
                    FrmWrk TEXT,
                    FOREIGN KEY(EmployeeId) REFERENCES tbl_employee(emp_id)
                )
            ''')

        # Create tbl_task_status_master
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbl_task_status_master (
                status_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                color_class TEXT,
                inserted_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create tbl_employee_status_master
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbl_employee_status_master (
                status_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                color_class TEXT,
                inserted_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Seed default task statuses
        cursor.execute("SELECT COUNT(*) FROM tbl_task_status_master")
        if cursor.fetchone()[0] == 0:
            default_task_statuses = [
                ("Pending", "Task has been created but not started", "#f59e0b"),
                ("Work In Progress", "Task is currently being worked on", "#3b82f6"),
                ("Completed", "Task has been successfully completed", "#10b981"),
                ("Blocked", "Task is blocked by dependency or issue", "#ef4444"),
                ("On Hold", "Task is temporarily suspended", "#8b5cf6")
            ]
            cursor.executemany('''
                INSERT INTO tbl_task_status_master (name, description, color_class)
                VALUES (?, ?, ?)
            ''', default_task_statuses)

        # Seed default employee statuses
        cursor.execute("SELECT COUNT(*) FROM tbl_employee_status_master")
        if cursor.fetchone()[0] == 0:
            default_employee_statuses = [
                ("active", "Employee is active and working", "#10b981"),
                ("inactive", "Employee has left or is inactive", "#ef4444"),
                ("On Leave", "Employee is currently on approved leave", "#f59e0b")
            ]
            cursor.executemany('''
                INSERT INTO tbl_employee_status_master (name, description, color_class)
                VALUES (?, ?, ?)
            ''', default_employee_statuses)

        conn.commit()
        # Create tbl_task_status_master
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbl_task_status_master (
                status_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                color_class TEXT,
                inserted_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create tbl_employee_status_master
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbl_employee_status_master (
                status_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                color_class TEXT,
                inserted_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Seed default task statuses
        cursor.execute("SELECT COUNT(*) FROM tbl_task_status_master")
        if cursor.fetchone()[0] == 0:
            default_task_statuses = [
                ("Pending", "Task has been created but not started", "#f59e0b"),
                ("Work In Progress", "Task is currently being worked on", "#3b82f6"),
                ("Completed", "Task has been successfully completed", "#10b981"),
                ("Blocked", "Task is blocked by dependency or issue", "#ef4444"),
                ("On Hold", "Task is temporarily suspended", "#8b5cf6")
            ]
            cursor.executemany('''
                INSERT INTO tbl_task_status_master (name, description, color_class)
                VALUES (?, ?, ?)
            ''', default_task_statuses)

        # Seed default employee statuses
        cursor.execute("SELECT COUNT(*) FROM tbl_employee_status_master")
        if cursor.fetchone()[0] == 0:
            default_employee_statuses = [
                ("active", "Employee is active and working", "#10b981"),
                ("inactive", "Employee has left or is inactive", "#ef4444"),
                ("On Leave", "Employee is currently on approved leave", "#f59e0b")
            ]
            cursor.executemany('''
                INSERT INTO tbl_employee_status_master (name, description, color_class)
                VALUES (?, ?, ?)
            ''', default_employee_statuses)

        # Create tbl_daily_task
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbl_daily_task (
                daily_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                task_title TEXT NOT NULL,
                task_desc TEXT NOT NULL,
                project_status TEXT NOT NULL,
                inserted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                admin_feedback TEXT,
                task_hours INTEGER DEFAULT 0,
                FOREIGN KEY (emp_id) REFERENCES tbl_employee (emp_id)
            )
        ''')

        try:
            cursor.execute('ALTER TABLE tbl_daily_task ADD COLUMN task_hours INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass

        conn.commit()
        conn.close()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
