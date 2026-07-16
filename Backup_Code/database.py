import sqlite3
import hashlib
from datetime import datetime
import pytz

class Database:
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
        
        conn.close()
        
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_user(self, email, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        hashed_password = self.hash_password(password)
        
        cursor.execute('''
            SELECT emp_id, first_name, last_name, emp_type, status 
            FROM tbl_employee 
            WHERE email = ? AND password = ? AND status = 'active'
        ''', (email, hashed_password))
        
        user = cursor.fetchone()
        conn.close()
        return user
    
    def add_employee(self, data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        hashed_password = self.hash_password(data['password'])
        cursor.execute('''
            INSERT INTO tbl_employee 
            (first_name, last_name, gender, dob, address, phone_no, email, password, status, emp_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['first_name'], data['last_name'], data['gender'], data['dob'],
              data['address'], data['phone_no'], data['email'], hashed_password,
              data['status'], data['emp_type']))    
        
        emmpp = cursor.lastrowid
        conn.commit()
        conn.close()
        return emmpp
    
    def update_employee(self, emp_id, data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if data['password']:
            hashed_password = self.hash_password(data['password'])
        else:
            cursor.execute('SELECT password FROM tbl_employee WHERE emp_id = ?', (emp_id,))
            hashed_password = cursor.fetchone()[0]
        
        cursor.execute('''
            UPDATE tbl_employee 
            SET first_name = ?, last_name = ?, gender = ?, dob = ?, address = ?, 
                phone_no = ?, email = ?, password = ?, status = ?, emp_type = ?
            WHERE emp_id = ?
        ''', (data['first_name'], data['last_name'], data['gender'], data['dob'],
              data['address'], data['phone_no'], data['email'], hashed_password,
              data['status'], data['emp_type'], emp_id))
        
        conn.commit()
        conn.close()
    
    def delete_employee(self, emp_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check for associated tasks
        cursor.execute('SELECT COUNT(*) FROM tbl_task WHERE emp_id = ?', (emp_id,))
        task_count = cursor.fetchone()[0]
        
        if task_count > 0:
            conn.close()
            raise Exception('Cannot delete employee with assigned tasks.')
        
        cursor.execute('DELETE FROM tbl_employee WHERE emp_id = ?', (emp_id,))
        conn.commit()
        conn.close()
    
    def get_employee(self, emp_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT emp_id, first_name, last_name, gender, dob, address, phone_no, email, status, emp_type
            FROM tbl_employee
            WHERE emp_id = ?
        ''', (emp_id,))
        
        employee = cursor.fetchone()
        conn.close()
        return employee
    
    def get_employees(self, status_filter='all'):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT emp_id, first_name, last_name, gender, dob, address, phone_no, email, status, emp_type, inserted_date, password
            FROM tbl_employee
        '''
        params = []
        
        if status_filter != 'all':
            query += ' WHERE status = ?'
            params.append(status_filter)
        
        query += ' ORDER BY inserted_date DESC'
        
        cursor.execute(query, params)
        employees = cursor.fetchall()
        conn.close()
        return employees
    
    def add_project(self, data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tbl_project 
            (project_name, priority, project_desc, project_status, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['project_name'], data['priority'], data['project_desc'],
              data['project_status'], data['start_date'], data['end_date']))
        
        conn.commit()
        conn.close()
    
    def update_project(self, project_id, data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tbl_project 
            SET project_name = ?, priority = ?, project_desc = ?, project_status = ?, 
                start_date = ?, end_date = ?
            WHERE project_id = ?
        ''', (data['project_name'], data['priority'], data['project_desc'],
              data['project_status'], data['start_date'], data['end_date'], project_id))
        
        conn.commit()
        conn.close()
    
    def delete_project(self, project_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check for associated tasks
        cursor.execute('SELECT COUNT(*) FROM tbl_task WHERE project_id = ?', (project_id,))
        task_count = cursor.fetchone()[0]
        
        if task_count > 0:
            conn.close()
            raise Exception('Cannot delete project with assigned tasks.')
        
        cursor.execute('DELETE FROM tbl_project WHERE project_id = ?', (project_id,))
        conn.commit()
        conn.close()
    
    def get_project(self, project_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT project_id, project_name, priority, project_desc, project_status, start_date, end_date
            FROM tbl_project
            WHERE project_id = ?
        ''', (project_id,))
        
        project = cursor.fetchone()
        conn.close()
        return project
    
    def get_projects(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT project_id, project_name, priority, project_desc, project_status, start_date, end_date, inserted_date
            FROM tbl_project
            ORDER BY inserted_date DESC
        ''')
        
        projects = cursor.fetchall()
        conn.close()
        return projects
    
    def get_tasks_by_project(self, project_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.task_id, t.task_desc, t.project_id, t.emp_id, t.priority, t.status, 
                   t.start_date, t.end_date, e.first_name, e.last_name
            FROM tbl_task t
            JOIN tbl_employee e ON t.emp_id = e.emp_id
            WHERE t.project_id = ?
            ORDER BY t.inserted_date DESC
        ''', (project_id,))
        
        tasks = cursor.fetchall()
        conn.close()
        return tasks
    
    def add_task(self, data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tbl_task 
            (project_id, emp_id, task_desc, priority, status, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['project_id'], data['emp_id'], data['task_desc'],
              data['priority'], data['status'], data['start_date'], data['end_date']))
        
        conn.commit()
        conn.close()
    
    def update_task(self, task_id, data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tbl_task 
            SET project_id = ?, emp_id = ?, task_desc = ?, priority = ?, 
                status = ?, start_date = ?, end_date = ?
            WHERE task_id = ?
        ''', (data['project_id'], data['emp_id'], data['task_desc'],
              data['priority'], data['status'], data['start_date'], data['end_date'], task_id))
        
        conn.commit()
        conn.close()
    
    def delete_task(self, task_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Delete associated task details
        cursor.execute('DELETE FROM tbl_task_details WHERE task_id = ?', (task_id,))
        cursor.execute('DELETE FROM tbl_task WHERE task_id = ?', (task_id,))
        
        conn.commit()
        conn.close()
    
    def get_task(self, task_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT task_id, task_desc, project_id, emp_id, priority, status, start_date, end_date
            FROM tbl_task
            WHERE task_id = ?
        ''', (task_id,))
        
        task = cursor.fetchone()
        conn.close()
        return task
    
    def get_tasks_by_employee(self, emp_id, status_filter='all', project_filter='', search_query=''):
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = '''
                SELECT t.task_id, t.task_desc, t.priority, t.status, t.start_date, t.end_date,
                    p.project_name
                FROM tbl_task t
                JOIN tbl_project p ON t.project_id = p.project_id
                WHERE t.emp_id = ?
            '''
            params = [emp_id]
            
            if status_filter != 'all' and status_filter:
                query += ' AND t.status = ?'
                params.append(status_filter)
            
            if project_filter:
                query += ' AND p.project_name = ?'
                params.append(project_filter)
                
            if search_query:
                query += ' AND (t.task_desc LIKE ? OR p.project_name LIKE ?)'
                search_term = f'%{search_query}%'
                params.extend([search_term, search_term])
            
            query += ' ORDER BY t.priority DESC, t.start_date'
            
            cursor.execute(query, params)
            tasks = cursor.fetchall()
            conn.close()
            return tasks
    
    def get_all_tasks_with_details_paginated(self, page, page_size, project_filter='', status_filter='', employee_filter='', search_query=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build the base query
        query = '''
            SELECT t.task_id, t.task_desc, t.priority, t.status, t.start_date, t.end_date,
                   p.project_name, e.first_name, e.last_name
            FROM tbl_task t
            JOIN tbl_project p ON t.project_id = p.project_id
            JOIN tbl_employee e ON t.emp_id = e.emp_id
        '''
        count_query = '''
            SELECT COUNT(*)
            FROM tbl_task t
            JOIN tbl_project p ON t.project_id = p.project_id
            JOIN tbl_employee e ON t.emp_id = e.emp_id
        '''
        params = []
        conditions = []

        # Apply filters
        if project_filter:
            conditions.append('p.project_name = ?')
            params.append(project_filter)
        if status_filter:
            conditions.append('t.status = ?')
            params.append(status_filter)
        if employee_filter:
            conditions.append("e.first_name || ' ' || e.last_name = ?")
            params.append(employee_filter)
        if search_query:
            conditions.append("(t.task_desc LIKE ? OR p.project_name LIKE ? OR (e.first_name || ' ' || e.last_name) LIKE ?)")
            search_term = f'%{search_query}%'
            params.extend([search_term, search_term, search_term])

        if conditions:
            condition_str = ' WHERE ' + ' AND '.join(conditions)
            query += condition_str
            count_query += condition_str

        # Add sorting and pagination
        query += ' ORDER BY t.inserted_date DESC LIMIT ? OFFSET ?'
        params.extend([page_size, (page - 1) * page_size])

        # Execute count query
        cursor.execute(count_query, params[:-2] if params[:-2] else [])
        total_tasks = cursor.fetchone()[0]

        # Execute paginated query
        cursor.execute(query, params)
        tasks = cursor.fetchall()
        
        conn.close()
        return tasks, total_tasks
    
    def has_task_detail_today(self, task_id, emp_id):
        # Jira-like tracking: Allow multiple task details/updates per day
        return False
    
    def add_task_detail(self, task_id, desc, status, emp_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verify task belongs to employee
        cursor.execute('SELECT emp_id FROM tbl_task WHERE task_id = ?', (task_id,))
        task = cursor.fetchone()
        if not task or task[0] != emp_id:
            conn.close()
            raise Exception('Task does not belong to this employee.')
        
        cursor.execute('''
            INSERT INTO tbl_task_details (task_id, desc, status)
            VALUES (?, ?, ?)
        ''', (task_id, desc, status))

        # Update task status based on the new detail
        if status == 'complete':
            # Check if all task details are now complete
            cursor.execute('''
                SELECT COUNT(*) FROM tbl_task_details 
                WHERE task_id = ? AND status != 'complete'
            ''', (task_id,))
            incomplete_count = cursor.fetchone()[0]
            if incomplete_count == 0:
                # All details are complete, set task to completed
                cursor.execute('''
                    UPDATE tbl_task 
                    SET status = ?, end_date = DATE('now')
                    WHERE task_id = ?
                ''', ('completed', task_id))
            else:
                # There are still incomplete details, set task to incomplete and clear end_date
                cursor.execute('''
                    UPDATE tbl_task 
                    SET status = ?, end_date = NULL
                    WHERE task_id = ?
                ''', ('incomplete', task_id))
        elif status == 'incomplete':
            # Detail is incomplete, set task to incomplete and clear end_date
            cursor.execute('''
                UPDATE tbl_task 
                SET status = ?, end_date = NULL
                WHERE task_id = ?
            ''', ('incomplete', task_id))
        else:
            # Unexpected status value, default to incomplete and clear end_date
            cursor.execute('''
                UPDATE tbl_task 
                SET status = ?, end_date = NULL
                WHERE task_id = ?
            ''', ('incomplete', task_id))
        
        conn.commit()
        conn.close()
    
    def get_task_details_by_employee(self, task_id, emp_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT td.detail_id, td.desc, td.inserted_date, td.status
            FROM tbl_task_details td
            JOIN tbl_task t ON td.task_id = t.task_id
            WHERE td.task_id = ? AND t.emp_id = ?
            ORDER BY td.inserted_date DESC
        ''', (task_id, emp_id))
        
        details = cursor.fetchall()
        conn.close()
        return details
    
    def get_task_detail(self, detail_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT td.detail_id, td.task_id, td.desc, td.inserted_date, td.status
            FROM tbl_task_details td
            WHERE td.detail_id = ?
        ''', (detail_id,))
        
        detail = cursor.fetchone()
        conn.close()
        return detail
    
    def get_task_details(self, task_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT detail_id, desc, inserted_date, status
            FROM tbl_task_details
            WHERE task_id = ?
            ORDER BY inserted_date DESC
        ''', (task_id,))
        
        details = cursor.fetchall()
        conn.close()
        return details
    
    
    def verify_task_detail_owner(self, detail_id, emp_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) 
            FROM tbl_task_details td
            JOIN tbl_task t ON td.task_id = t.task_id
            WHERE td.detail_id = ? AND t.emp_id = ?
        ''', (detail_id, emp_id))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def update_task_detail(self, detail_id, desc, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tbl_task_details 
            SET desc = ?, status = ?, inserted_date = CURRENT_TIMESTAMP
            WHERE detail_id = ?
        ''', (desc, status, detail_id))
        
        # Get the task_id for this detail
        cursor.execute('SELECT task_id FROM tbl_task_details WHERE detail_id = ?', (detail_id,))
        task_row = cursor.fetchone()
        if task_row:
            task_id = task_row[0]
            
            # Update task status based on all task details
            if status == 'complete':
                # Check if all task details are now complete
                cursor.execute('''
                    SELECT COUNT(*) FROM tbl_task_details 
                    WHERE task_id = ? AND status != 'complete'
                ''', (task_id,))
                incomplete_count = cursor.fetchone()[0]
                if incomplete_count == 0:
                    # All details are complete, set task to completed
                    cursor.execute('''
                        UPDATE tbl_task 
                        SET status = ?, end_date = DATE('now')
                        WHERE task_id = ?
                    ''', ('completed', task_id))
                else:
                    # There are still incomplete details, set task to incomplete and clear end_date
                    cursor.execute('''
                        UPDATE tbl_task 
                        SET status = ?, end_date = NULL
                        WHERE task_id = ?
                    ''', ('incomplete', task_id))
            else:
                # Detail is incomplete, set task to incomplete and clear end_date
                cursor.execute('''
                    UPDATE tbl_task 
                    SET status = ?, end_date = NULL
                    WHERE task_id = ?
                ''', ('incomplete', task_id))
        
        conn.commit()
        conn.close()
        
        # ---------- LEAVE TYPE ----------
    def add_leave_type(self, leave_type):
        try:
            with self.get_connection() as c:
                c.execute('INSERT INTO tbl_leave_type (leave_type) VALUES (?)', (leave_type,))
            return True, 'Leave type added successfully.'
        except sqlite3.IntegrityError:
            return False, 'This leave type already exists.'

    def get_leave_types(self):
        with self.get_connection() as c:
            return c.execute('SELECT leave_type_id, leave_type FROM tbl_leave_type ORDER BY leave_type').fetchall()
        
    def update_leave_type(self, lt_id, leave_type):
        with self.get_connection() as c:
            try:
                c.execute('''
                    UPDATE tbl_leave_type
                    SET leave_type = ?
                    WHERE leave_type_id = ?
                ''', (leave_type, lt_id))
                return c.total_changes > 0
            except sqlite3.IntegrityError:
                return False
    

    def delete_leave_type(self, lt_id):
        with self.get_connection() as c:
            c.execute('DELETE FROM tbl_leave_type WHERE leave_type_id=?', (lt_id,))

    # ---------- LEAVE REQUESTS --------
    def add_leave_request(self, data):
        with self.get_connection() as c:
            c.execute('''
                INSERT INTO tbl_leave_request
                (leave_type_id, employee_id, start_date, end_date,
                leave_desc, manager_id)
                VALUES (?,?,?,?,?,?)
            ''', (data['leave_type_id'], data['employee_id'], data['start_date'],
                data['end_date'], data['leave_desc'], data['manager_id']))

    def get_leave_requests(self, where='', params=()):
        with self.get_connection() as c:
            base = '''
                SELECT lr.request_id, lt.leave_type, e.first_name || ' ' || e.last_name,
                    lr.start_date, lr.end_date, lr.leave_desc,
                    lr.status, lr.comments, lr.inserted_date
                FROM tbl_leave_request lr
                JOIN tbl_leave_type lt ON lt.leave_type_id = lr.leave_type_id
                JOIN tbl_employee e ON e.emp_id = lr.employee_id
            '''

            # Remove any "ORDER" or "LIMIT" in `where` accidentally appended
            if "ORDER BY" in where.upper() or "LIMIT" in where.upper():
                raise ValueError("Do not include ORDER or LIMIT in 'where' argument")

            query = base + f' {where} ORDER BY lr.inserted_date DESC'
            return c.execute(query, params).fetchall()

    def update_leave_status(self, req_id, new_status, manager_id, comments=''):
        with self.get_connection() as c:
            c.execute('''
                UPDATE tbl_leave_request
                SET status=?, manager_id=?, comments=?, inserted_date=CURRENT_TIMESTAMP
                WHERE request_id=?
            ''', (new_status, manager_id, comments, req_id))
    def get_leave_status(self, req_id):
        with self.get_connection() as c:
            result = c.execute('SELECT status FROM tbl_leave_request WHERE request_id=?', (req_id,)).fetchone()
            return result[0] if result else None
    def count_leave_requests(self, where='', params=()):
        with self.get_connection() as c:
            q = f'''
                SELECT COUNT(*)
                FROM tbl_leave_request lr
                JOIN tbl_leave_type lt ON lt.leave_type_id = lr.leave_type_id
                JOIN tbl_employee e ON e.emp_id = lr.employee_id
                {where}
            '''
            return c.execute(q, params).fetchone()[0]
    def get_leave_requests_paginated(self, where='', params=(), limit=10, offset=0):
        with self.get_connection() as c:
            base = '''
                SELECT lr.request_id, lt.leave_type, e.first_name || ' ' || e.last_name,
                    lr.start_date, lr.end_date, lr.leave_desc,
                    lr.status, lr.comments, lr.inserted_date
                FROM tbl_leave_request lr
                JOIN tbl_leave_type lt ON lt.leave_type_id = lr.leave_type_id
                JOIN tbl_employee e ON e.emp_id = lr.employee_id
            '''

            query = base
            if where:
                query += f' {where}'

            query += ' ORDER BY lr.inserted_date DESC LIMIT ? OFFSET ?'
            return c.execute(query, (*params, limit, offset)).fetchall()
        # ========== EXPENSE TYPE ================================================
    def add_expense_type(self, etype):
        with self.get_connection() as c:
            c.execute('INSERT OR IGNORE INTO tbl_expense_type (expense_type) VALUES (?)', (etype,))

    def get_expense_types(self):
        with self.get_connection() as c:
            return c.execute('SELECT expense_type_id, expense_type FROM tbl_expense_type ORDER BY expense_type').fetchall()

    def delete_expense_type(self, et_id):
        with self.get_connection() as c:
            c.execute('DELETE FROM tbl_expense_type WHERE expense_type_id=?', (et_id,))
    
    def update_expense_type(self, et_id, new_type):
        with self.get_connection() as c:
            c.execute('UPDATE tbl_expense_type SET expense_type = ? WHERE expense_type_id = ?', (new_type, et_id))
    
    def expense_type_exists(self, etype, exclude_id=None):
        with self.get_connection() as c:
            if exclude_id:
                result = c.execute(
                    'SELECT 1 FROM tbl_expense_type WHERE expense_type = ? AND expense_type_id != ?',
                    (etype, exclude_id)
                ).fetchone()
            else:
                result = c.execute(
                    'SELECT 1 FROM tbl_expense_type WHERE expense_type = ?',
                    (etype,)
                ).fetchone()
            return result is not None



    # ========== EXPENSES ====================================================
    def add_expense(self, data):
        with self.get_connection() as c:
            c.execute('''
                INSERT INTO tbl_expenses
                (expense_type_id, sub_expense_type_id, employee_id, exp_description, 
                manager_id, approver_comments, given_by_id, final_comments, amount, 
                inserted_date, expense_date, invoice_path, po_no, bill_status, expense_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['expense_type_id'],
                data.get('sub_expense_type_id'),
                data['employee_id'],
                data['exp_description'],
                data.get('manager_id'),
                data.get('approver_comments', ''),
                data.get('given_by_id'),
                data.get('final_comments', ''),
                data['amount'],
                datetime.now(pytz.utc).isoformat(),
                data['expense_date'],
                data.get('invoice_path'),
                data.get('po_no', ''),
                data.get('bill_status', ''),
                data.get('expense_by', '')
            ))
    def get_expenses(self, where='', params=()):
        with self.get_connection() as c:
            q = f'''
                SELECT ex.expense_id, et.expense_type,
                    e.first_name||' '||e.last_name AS emp_name,
                    ex.exp_description, ex.status,
                    ex.approver_comments, ex.final_comments,
                    ex.inserted_date, ex.amount,
                    ex.employee_id,
                    ex.approved_date,
                    ex.approved_by,
                    ex.expense_date,
                    ex.invoice_path
                FROM   tbl_expenses ex
                JOIN   tbl_expense_type et ON et.expense_type_id = ex.expense_type_id
                JOIN   tbl_employee      e ON e.emp_id           = ex.employee_id
                {where}
                ORDER BY ex.inserted_date DESC
            '''
            return c.execute(q, params).fetchall()
    
    def get_expenses_paginated(self, where='', params=(), limit=15, offset=0):
        with self.get_connection() as c:
            q = f'''
                SELECT ex.expense_id, et.expense_type, st.sub_expense_type,
                    e.first_name||' '||e.last_name AS emp_name,
                    ex.exp_description, ex.status,
                    ex.approver_comments, ex.final_comments,
                    ex.inserted_date, ex.amount,
                    ex.employee_id,
                    ex.approved_date,
                    ex.expense_date,
                    ex.invoice_path,
                    ex.po_no,
                    ex.bill_status,
                    ex.expense_by
                FROM tbl_expenses ex
                JOIN tbl_expense_type et ON et.expense_type_id = ex.expense_type_id
                LEFT JOIN tbl_sub_expense_type st ON st.sub_expense_type_id = ex.sub_expense_type_id
                JOIN tbl_employee e ON e.emp_id = ex.employee_id
                {where}
                ORDER BY ex.inserted_date DESC
                LIMIT ? OFFSET ?
            '''
            return c.execute(q, (*params, limit, offset)).fetchall()
        
    def count_expenses(self, where='', params=()):
        with self.get_connection() as c:
            q = f'''
                SELECT COUNT(*)
                FROM tbl_expenses ex
                JOIN tbl_expense_type et ON et.expense_type_id = ex.expense_type_id
                JOIN tbl_employee e ON e.emp_id = ex.employee_id
                {where}
            '''
            return c.execute(q, params).fetchone()[0]
    
    def get_expense_by_id(self, exp_id):
        with self.get_connection() as c:
            q = '''
                SELECT ex.expense_id, et.expense_type, st.sub_expense_type,
                    e.first_name||' '||e.last_name AS emp_name,
                    ex.exp_description, ex.status,
                    ex.approver_comments, ex.final_comments,
                    ex.inserted_date, ex.amount,
                    ex.employee_id,
                    ex.approved_date,
                    ex.po_no,
                    ex.bill_status,
                    ex.expense_by
                FROM tbl_expenses ex
                JOIN tbl_expense_type et ON et.expense_type_id = ex.expense_type_id
                LEFT JOIN tbl_sub_expense_type st ON st.sub_expense_type_id = ex.sub_expense_type_id
                JOIN tbl_employee e ON e.emp_id = ex.employee_id
                WHERE ex.expense_id = ?
            '''
            return c.execute(q, (exp_id,)).fetchone()

    def update_expense_status(self, exp_id, status, approver_comments='', manager_id=None, approved_by=None):
        with self.get_connection() as c:
            if status == 'approved':
                utc_now = datetime.now(pytz.utc).isoformat()
                c.execute('''
                    UPDATE tbl_expenses
                    SET status=?, approver_comments=?, manager_id=?, approved_by=?, approved_date=?
                    WHERE expense_id=?
                ''', (status, approver_comments, manager_id, approved_by, utc_now, exp_id))
            else:
                c.execute('''
                    UPDATE tbl_expenses
                    SET status=?, approver_comments=?, manager_id=?, approved_by=?
                    WHERE expense_id=?
                ''', (status, approver_comments, manager_id, approved_by, exp_id))
                
        # ---------- LEAVE SUMMARY (per employee) --------------------------------
    def get_leave_summary(self, date_from=None, date_to=None, leave_type_id=None):
        """
        Returns (emp_id, emp_name, total_days) for ALL employees,
        even if total_days == 0 (LEFT JOIN).
        """
        where = []
        params = []

        if date_from:
            where.append("lr.start_date >= ?")
            params.append(date_from)
        if date_to:
            where.append("lr.end_date   <= ?")
            params.append(date_to)
        if leave_type_id:
            where.append("lr.leave_type_id = ?")
            params.append(leave_type_id)

        where_sql = " AND ".join(where)
        if where_sql:
            where_sql = "WHERE " + where_sql

        q = f"""
            SELECT  e.emp_id,
                    e.first_name || ' ' || e.last_name AS emp_name,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN lr.start_date IS NULL THEN 0
                                ELSE (JULIANDAY(lr.end_date) - JULIANDAY(lr.start_date) + 1)
                            END
                        ), 0
                    ) AS total_days
            FROM tbl_employee e
            LEFT JOIN tbl_leave_request lr ON lr.employee_id = e.emp_id
                                            { 'AND ' + where_sql[6:] if where_sql else '' }
            GROUP BY e.emp_id
            ORDER BY e.first_name, e.last_name
        """
        with self.get_connection() as c:
            return c.execute(q, params).fetchall()
        
    def get_employee_profile(self, emp_id):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row  # Add this
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM TblEmployeeProfile WHERE EmployeeId = ?", (emp_id,))
            row = cursor.fetchone()
            return dict(row) if row else None  # Return dict for safer access

    def add_employee_profile(self, data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO TblEmployeeProfile (
                    EmployeeId, UANNo, PANNO, AadharNo, BankName, BranchName, ACNo, IFSCode,
                    Designation, EmgContact, ReportingMng, DOJ, PrgLng, FrmWrk
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['EmployeeId'], data['UANNo'], data['PANNO'], data['AadharNo'],
                data['BankName'], data['BranchName'], data['ACNo'], data['IFSCode'],
                data['Designation'], data['EmgContact'], data['ReportingMng'],
                data['DOJ'], data['PrgLng'], data['FrmWrk']
            ))

    def update_employee_profile(self, emp_id, data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE TblEmployeeProfile SET
                    UANNo=?, PANNO=?, AadharNo=?, BankName=?, BranchName=?, ACNo=?, IFSCode=?,
                    Designation=?, EmgContact=?, ReportingMng=?, DOJ=?, PrgLng=?, FrmWrk=?
                WHERE EmployeeId=?
            ''', (
                data['UANNo'], data['PANNO'], data['AadharNo'], data['BankName'],
                data['BranchName'], data['ACNo'], data['IFSCode'], data['Designation'],
                data['EmgContact'], data['ReportingMng'], data['DOJ'], data['PrgLng'],
                data['FrmWrk'], emp_id
            ))
            
    def update_employee_password_and_emgcontact(self, emp_id, new_password, emg_contact): 
        if new_password or new_password is not None:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                hashed = self.hash_password(new_password)
                cursor.execute('UPDATE tbl_employee SET password = ? WHERE emp_id = ?', (hashed, emp_id))
            return "Password updated successfully."
        elif not new_password or new_password is None:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                hashed = self.hash_password(new_password)
                cursor.execute('UPDATE TblEmployeeProfile SET EmgContact = ? WHERE EmployeeID = ?', (emg_contact, emp_id))
            return "Emergency contact updated successfully."
        else:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                hashed = self.hash_password(new_password)
                cursor.execute('UPDATE tbl_employee SET password = ? WHERE emp_id = ?', (hashed, emp_id))
                cursor.execute('UPDATE TblEmployeeProfile SET EmgContact = ? WHERE EmployeeID = ?', (emg_contact, emp_id))
            return "Emergency contact and password updated successfully."

    def update_employee_emg_contact_once(self, emp_id, new_emg):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE TblEmployeeProfile
                SET EmgContact = ?, EmgUpdatedByEmp = 1
                WHERE EmployeeId = ? AND EmgUpdatedByEmp = 0
            ''', (new_emg, emp_id))
            return cursor.rowcount > 0
        
    def delete_all_employees(self):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM tbl_employee WHERE emp_type != "admin"')

    def delete_all_tasks(self):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM tbl_task_details')
            conn.execute('DELETE FROM tbl_task')

    def delete_all_leave_types(self):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM tbl_leave_type')

    def delete_all_expense_types(self):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM tbl_expense_type')

       # ---------- Wiki Category CRUD ----------
    def add_wiki_category(self, category, img_filename):
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO TblWikiCategory (Category, CatImg) VALUES (?, ?)',
                (category, img_filename)
            )

    def get_wiki_categories(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT CategoryId, Category, CatImg FROM TblWikiCategory ORDER BY inserted_date DESC'
        )
        cats = cursor.fetchall()
        conn.close()
        return cats

    def update_wiki_category(self, cat_id, category, img_filename=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if img_filename:
            cursor.execute(
                'UPDATE TblWikiCategory SET Category=?, CatImg=? WHERE CategoryId=?',
                (category, img_filename, cat_id)
            )
        else:
            cursor.execute(
                'UPDATE TblWikiCategory SET Category=? WHERE CategoryId=?',
                (category, cat_id)
            )
        conn.commit()
        conn.close()

    def delete_wiki_category(self, cat_id):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM TblWikiCategory WHERE CategoryId=?', (cat_id,))


    # ---------- Wiki Page CRUD ----------
    def add_wiki_page(self, category_id, title, descr):
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO TblWikiPage (CategoryId, Title, Descri) VALUES (?, ?, ?)',
                (category_id, title, descr)
            )

    def get_wiki_pages(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT wp.WikiId, wp.Title, wp.Descri, wp.InsertedDate, wc.Category, wc.CatImg
            FROM TblWikiPage wp
            JOIN TblWikiCategory wc ON wp.CategoryId = wc.CategoryId
            WHERE wp.RowStatus = 0
            ORDER BY wp.InsertedDate DESC
        ''')
        pages = cursor.fetchall()
        conn.close()
        return pages

    def get_wiki_page(self, wiki_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
            wp.WikiId,
            wp.CategoryId,
            wp.Title,
            wp.Descri,
            wc.CatImg
            FROM TblWikiPage wp
            JOIN TblWikiCategory wc ON wp.CategoryId = wc.CategoryId
            WHERE wp.WikiId = ?
        ''', (wiki_id,))
        page = cursor.fetchone()
        conn.close()
        return page

    def update_wiki_page(self, wiki_id, category_id, title, descr):
        with self.get_connection() as conn:
            conn.execute(
                'UPDATE TblWikiPage SET CategoryId=?, Title=?, Descri=? WHERE WikiId=?',
                (category_id, title, descr, wiki_id)
            )

    def soft_delete_wiki_page(self, wiki_id):
        with self.get_connection() as conn:
            conn.execute(
                'UPDATE TblWikiPage SET RowStatus=1 WHERE WikiId=?',
                (wiki_id,)
            )
        # ---------- Wiki Views CRUD ----------
    def add_wiki_view(self, wiki_id, emp_id):
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO TblWikiViews (WikiId, EmployeeId) VALUES (?, ?)',
                (wiki_id, emp_id)
            )

    def get_wiki_views(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT wv.WikiViewId,
                   wp.Title,
                   e.first_name || ' ' || e.last_name AS employee_name,
                   wv.ViewDateTime
            FROM TblWikiViews wv
            JOIN TblWikiPage  wp ON wv.WikiId     = wp.WikiId
            JOIN tbl_employee e  ON wv.EmployeeId = e.emp_id
            ORDER BY wv.ViewDateTime DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return rows
    def get_wiki_views_filtered(self, start_date=None, end_date=None, wiki_id=None):
        """
        Fetch individual view records, optionally filtering by date range and/or wiki page.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT wv.WikiViewId,
                   wp.Title,
                   e.first_name || ' ' || e.last_name AS employee_name,
                   wv.ViewDateTime
            FROM TblWikiViews wv
            JOIN TblWikiPage wp ON wv.WikiId = wp.WikiId
            JOIN tbl_employee e ON wv.EmployeeId = e.emp_id
        '''
        conditions = []
        params = []
        if start_date:
            conditions.append("date(wv.ViewDateTime) >= date(?)")
            params.append(start_date)
        if end_date:
            conditions.append("date(wv.ViewDateTime) <= date(?)")
            params.append(end_date)
        if wiki_id:
            conditions.append("wv.WikiId = ?")
            params.append(wiki_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY wv.ViewDateTime DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return rows


    def get_wiki_view_counts(self, start_date=None, end_date=None):
        """
        Return total view count per wiki page, optionally within a date range.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT wp.WikiId,
                   wp.Title,
                   COUNT(*) AS view_count
            FROM TblWikiViews wv
            JOIN TblWikiPage wp ON wv.WikiId = wp.WikiId
        '''
        conditions = []
        params = []
        if start_date:
            conditions.append("date(wv.ViewDateTime) >= date(?)")
            params.append(start_date)
        if end_date:
            conditions.append("date(wv.ViewDateTime) <= date(?)")
            params.append(end_date)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " GROUP BY wp.WikiId, wp.Title ORDER BY view_count DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return rows
    
    # ========== SUB EXPENSE TYPE ================================================
    def add_sub_expense_type(self, expense_type_id, sub_expense_type):
        with self.get_connection() as c:
            try:
                c.execute('INSERT INTO tbl_sub_expense_type (expense_type_id, sub_expense_type) VALUES (?, ?)', 
                        (expense_type_id, sub_expense_type))
                return True, 'Sub-expense type added successfully.'
            except sqlite3.IntegrityError:
                return False, 'This sub-expense type already exists for this expense type.'

    def get_sub_expense_types(self, expense_type_id=None):
        with self.get_connection() as c:
            if expense_type_id:
                return c.execute('''
                    SELECT st.sub_expense_type_id, st.sub_expense_type, st.expense_type_id, et.expense_type
                    FROM tbl_sub_expense_type st
                    JOIN tbl_expense_type et ON st.expense_type_id = et.expense_type_id
                    WHERE st.expense_type_id = ?
                    ORDER BY st.sub_expense_type
                ''', (expense_type_id,)).fetchall()
            else:
                return c.execute('''
                    SELECT st.sub_expense_type_id, st.sub_expense_type, st.expense_type_id, et.expense_type
                    FROM tbl_sub_expense_type st
                    JOIN tbl_expense_type et ON st.expense_type_id = et.expense_type_id
                    ORDER BY et.expense_type, st.sub_expense_type
                ''').fetchall()

    def update_sub_expense_type(self, sub_et_id, sub_expense_type):
        with self.get_connection() as c:
            try:
                c.execute('UPDATE tbl_sub_expense_type SET sub_expense_type = ? WHERE sub_expense_type_id = ?', 
                        (sub_expense_type, sub_et_id))
                return c.total_changes > 0
            except sqlite3.IntegrityError:
                return False

    def delete_sub_expense_type(self, sub_et_id):
        with self.get_connection() as c:
            c.execute('DELETE FROM tbl_sub_expense_type WHERE sub_expense_type_id = ?', (sub_et_id,))
            
    def delete_all_sub_expense_types(self):
        with self.get_connection() as c:
            c.execute('DELETE FROM tbl_sub_expense_type')

    # ========== JIRA-LIKE TRACKING & REPORTS ====================================

    def update_task_status_only(self, task_id, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tbl_task 
            SET status = ?
            WHERE task_id = ?
        ''', (status, task_id))
        if status == 'completed':
            cursor.execute('''
                UPDATE tbl_task 
                SET end_date = DATE('now')
                WHERE task_id = ?
            ''', (task_id,))
        conn.commit()
        conn.close()

    def get_recent_task_activities(self, limit=50, emp_id=None, project_filter='', status_filter='', employee_filter='', search_query=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT td.detail_id, td.task_id, td.desc, td.inserted_date, td.status,
                   t.task_desc, p.project_name, e.first_name, e.last_name
            FROM tbl_task_details td
            JOIN tbl_task t ON td.task_id = t.task_id
            JOIN tbl_project p ON t.project_id = p.project_id
            JOIN tbl_employee e ON t.emp_id = e.emp_id
        '''
        conditions = []
        params = []
        
        if emp_id:
            conditions.append('t.emp_id = ?')
            params.append(emp_id)
        if project_filter:
            conditions.append('p.project_name = ?')
            params.append(project_filter)
        if status_filter:
            # task status
            conditions.append('t.status = ?')
            params.append(status_filter)
        if employee_filter:
            conditions.append("e.first_name || ' ' || e.last_name = ?")
            params.append(employee_filter)
        if search_query:
            conditions.append("(td.desc LIKE ? OR t.task_desc LIKE ? OR p.project_name LIKE ? OR (e.first_name || ' ' || e.last_name) LIKE ?)")
            search_term = f'%{search_query}%'
            params.extend([search_term, search_term, search_term, search_term])
            
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
            
        query += ' ORDER BY td.inserted_date DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()
        return data

    def get_admin_task_status_counts(self, project_filter='', employee_filter='', search_query=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = '''
            SELECT t.status, COUNT(*) 
            FROM tbl_task t
            JOIN tbl_project p ON t.project_id = p.project_id
            JOIN tbl_employee e ON t.emp_id = e.emp_id
        '''
        conditions = []
        params = []
        if project_filter:
            conditions.append('p.project_name = ?')
            params.append(project_filter)
        if employee_filter:
            conditions.append("e.first_name || ' ' || e.last_name = ?")
            params.append(employee_filter)
        if search_query:
            conditions.append("(t.task_desc LIKE ? OR p.project_name LIKE ? OR (e.first_name || ' ' || e.last_name) LIKE ?)")
            search_term = f'%{search_query}%'
            params.extend([search_term, search_term, search_term])

        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)

        query += ' GROUP BY t.status'
        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()
        return data

    def get_admin_project_task_counts(self, status_filter='', employee_filter='', search_query=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = '''
            SELECT p.project_name, COUNT(t.task_id) 
            FROM tbl_project p
            LEFT JOIN tbl_task t ON p.project_id = t.project_id
            LEFT JOIN tbl_employee e ON t.emp_id = e.emp_id
        '''
        conditions = []
        params = []
        if status_filter:
            conditions.append('t.status = ?')
            params.append(status_filter)
        if employee_filter:
            conditions.append("e.first_name || ' ' || e.last_name = ?")
            params.append(employee_filter)
        if search_query:
            conditions.append("(t.task_desc LIKE ? OR p.project_name LIKE ? OR (e.first_name || ' ' || e.last_name) LIKE ?)")
            search_term = f'%{search_query}%'
            params.extend([search_term, search_term, search_term])

        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)

        query += ' GROUP BY p.project_id, p.project_name'
        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()
        return data

    def get_admin_employee_task_counts(self, project_filter='', status_filter='', search_query=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = '''
            SELECT e.first_name || ' ' || e.last_name as emp_name, COUNT(t.task_id) 
            FROM tbl_employee e
            LEFT JOIN tbl_task t ON e.emp_id = t.emp_id
            LEFT JOIN tbl_project p ON t.project_id = p.project_id
            WHERE e.emp_type = 'emp' AND e.status = 'active'
        '''
        params = []
        if project_filter:
            query += ' AND p.project_name = ?'
            params.append(project_filter)
        if status_filter:
            query += ' AND t.status = ?'
            params.append(status_filter)
        if search_query:
            query += " AND (t.task_desc LIKE ? OR p.project_name LIKE ? OR (e.first_name || ' ' || e.last_name) LIKE ?)"
            search_term = f'%{search_query}%'
            params.extend([search_term, search_term, search_term])

        query += ' GROUP BY e.emp_id, emp_name'
        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()
        return data
        
    def get_employee_task_status_counts(self, emp_id, project_filter='', search_query=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = '''
            SELECT t.status, COUNT(*) 
            FROM tbl_task t
            JOIN tbl_project p ON t.project_id = p.project_id
            WHERE t.emp_id = ?
        '''
        params = [emp_id]
        if project_filter:
            query += ' AND p.project_name = ?'
            params.append(project_filter)
        if search_query:
            query += ' AND (t.task_desc LIKE ? OR p.project_name LIKE ?)'
            search_term = f'%{search_query}%'
            params.extend([search_term, search_term])

        query += ' GROUP BY t.status'
        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()
        return data