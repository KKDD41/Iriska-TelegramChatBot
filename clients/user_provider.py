from SQL_client import SQLiteClient


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


user_provider = UserProvider(
    SQLiteClient("C:\\Users\\Kate\\Desktop\\IRISKA\\Irirska-TelegramChatBot\\clients\\users.db"))