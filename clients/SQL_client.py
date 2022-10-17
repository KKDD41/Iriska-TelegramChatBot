import sqlite3


class SQLiteClient:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.conn = None

    def create_conn(self):
        self.conn = sqlite3.connect(self.filepath, check_same_thread=False)

    def execute_query(self, command: str, params: tuple):
        if self.conn is not None:
            # TODO: if commend and params are valid and if the user_id exists
            self.conn.execute(command, params)
            self.conn.commit()
        else:
            raise ConnectionError("There is no definition for field 'self.conn'.")

    def execute_select_query(self, command: str):
        if self.conn is not None:
            # TODO: if commend is valid
            cur = self.conn.cursor()
            cur.execute(command)
            return cur.fetchall()
        else:
            raise ConnectionError("There is no definition for field 'self.conn'.")


class UserProvider:
    CREATE_USER = """
        INSERT INTO users(user_id, chat_id, username) VALUES (?, ?, ?);
    """

    GET_USER = """
        SELECT user_id, chat_id, username FROM users WHERE user_id = %s;
    """

    def __init__(self, DB_client: SQLiteClient):
        self.DB_client = DB_client

    def set_up(self):
        self.DB_client.create_conn()

    def get_user(self, user_id: str):
        user = self.DB_client.execute_select_query(self.GET_USER % user_id)
        return user[0] if user else []

    def create_user(self, user_id: str, chat_id: int, username: str):
        self.DB_client.execute_query(self.CREATE_USER, (user_id, chat_id, username))

