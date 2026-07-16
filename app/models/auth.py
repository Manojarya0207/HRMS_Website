"""Authentication data-access methods (moved verbatim from database.py)."""


class AuthMixin:
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
