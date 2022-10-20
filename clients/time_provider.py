import schedule
from time import sleep
from clients.SQL_client import SQLiteClient


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
    DELETE_TIME = """
        DELETE FROM alarm_table WHERE time = '%s';
    """

    @staticmethod
    def schedule_checker():
        while True:
            schedule.run_pending()
            sleep(1)

    def __init__(self, DB_client: SQLiteClient):
        self.DB_client = DB_client
        self.job_dict = {}

    def set_up(self):
        self.DB_client.create_conn()

    def get_chats_to_notify(self, curr_time: str):
        to_notify = self.DB_client.execute_select_query(self.SELECT_TIME % curr_time)
        if to_notify:
            set_of_chats = set(map(int, to_notify[0][1].split()))
            return set_of_chats
        return []

    def update_time(self, curr_time: str, chat_id: int, remove: bool = False):
        time_str = self.DB_client.execute_select_query(self.SELECT_TIME % curr_time)
        if not remove:
            if not time_str:
                self.DB_client.execute_query(self.ADD_TIME, (curr_time, str(chat_id) + " "))
                return 'add'
            else:
                all_chats = set(map(int, time_str[0][1].split()))
                if chat_id not in all_chats:
                    self.DB_client.execute_query(self.UPDATE_TIME, (time_str[0][1] + str(chat_id) + " ", curr_time))
                return False
        else:
            if time_str:
                all_chats = set(map(int, time_str[0][1].split()))
                if chat_id in all_chats:
                    all_chats.remove(chat_id)
                    if all_chats:
                        self.DB_client.execute_query(self.UPDATE_TIME,
                                                     (' '.join(str(chat) for chat in all_chats), curr_time))
                        return False
                    else:
                        self.DB_client.execute_query(self.DELETE_TIME % curr_time, ())
                        return 'remove'

    def schedule_work_update(self, curr_time: str, func_to_preform=None, update: str | None = None):
        if update is None:
            return
        if update == 'add':
            self.job_dict[curr_time] = schedule.every().day.at(curr_time).do(func_to_preform, curr_time)
        elif update == 'remove':
            schedule.cancel_job(self.job_dict[curr_time])
        print(self.job_dict)


time_provider = TimeProvider(
    SQLiteClient("C:\\Users\\Kate\\Desktop\\IRISKA\\Irirska-TelegramChatBot\\clients\\alarm_table.db"))
