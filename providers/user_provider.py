from clients import SQLiteClient


class UserProvider:
    CREATE_USER = """
        INSERT INTO users(user_id, chat_id, username, dp_results, rl_results) VALUES (?, ?, ?, ?, ?);
    """

    GET_USER = """
        SELECT user_id, chat_id, username, dp_results, rl_results FROM users WHERE user_id = %s;
    """

    UPDATE_TEST = """
        UPDATE users SET dp_results = ?, rl_results = ? WHERE user_id = ?;
    """

    def __init__(self, filepath: str):
        self.DB_client = SQLiteClient(filepath)

    def set_up(self):
        self.DB_client.create_conn()

    def get_user(self, user_id: str):
        user = self.DB_client.execute_select_query(self.GET_USER % user_id)
        return user[0] if user else []

    def create_user(self, user_id: str, chat_id: int, username: str, dp_results: str = "", rl_results: str = ""):
        self.DB_client.execute_query(self.CREATE_USER, (user_id, chat_id, username, dp_results, rl_results))

    def update_test(self, user_id: str, dp_results: str = "", rl_results: str = ""):
        user = self.get_user(user_id)
        print(user)
        if user is None:
            raise ValueError(f"There is no user with id: {user_id}")

        self.DB_client.execute_query(self.UPDATE_TEST,
                                     (user[3] + " " + dp_results if dp_results else user[3],
                                      user[4] + " " + rl_results if rl_results else user[4],
                                      user_id))
