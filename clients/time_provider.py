from SQL_client import SQLiteClient


class TimeProvider:
    SELECT_TIME = """
        SELECT time, chats_to_notify FROM alarm_table WHERE time = '%s';
    """
    ADD_TIME = """
        INSERT INTO alarm_table(time, chats_to_notify) VALUES(?, ?);
    """

    UPDATE_TIME = """
        UPDATE alarm_table SET chats_to_notify = ? WHERE time = ?;
    """

    def __init__(self, DB_client: SQLiteClient):
        self.DB_client = DB_client

    def set_up(self):
        self.DB_client.create_conn()

    def get_chats_to_notify(self, curr_time: str):
        # TODO: modify a result
        to_notify = self.DB_client.execute_select_query(self.SELECT_TIME % curr_time)
        return to_notify[0][1] if to_notify else []

    def update_time(self, curr_time: str, chat_id: int, remove: bool = False):
        time_str = self.DB_client.execute_select_query(self.SELECT_TIME % curr_time)
        if not remove:
            if not time_str:
                self.DB_client.execute_query(self.ADD_TIME, (curr_time, str(chat_id) + " "))
            else:
                all_chats = set(map(int, time_str[0][1].split()))
                if chat_id not in all_chats:
                    self.DB_client.execute_query(self.UPDATE_TIME, (time_str[0][1] + str(chat_id) + " ", curr_time))
        else:
            if time_str:
                all_chats = set(map(int, time_str[0][1].split()))
                if chat_id in all_chats:
                    all_chats.remove(chat_id)
                    self.DB_client.execute_query(self.UPDATE_TIME,
                                                 (' '.join(str(chat) for chat in all_chats), curr_time))


time_provider = TimeProvider(
    SQLiteClient("C:\\Users\\Kate\\Desktop\\IRISKA\\Irirska-TelegramChatBot\\clients\\alarm_table.db"))