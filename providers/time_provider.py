import schedule
from time import sleep
from clients import SQLiteClient


class TimeProvider:
    __slots__ = "DB_client", "job_dict"

    SELECT_TIME = """
        SELECT time, chats_to_notify, notification_messages FROM alarm WHERE time = '%s';
    """
    ADD_TIME = """
        INSERT INTO alarm(time, chats_to_notify, notification_messages) VALUES(?, ?, ?);
    """
    UPDATE_TIME = """
        UPDATE alarm SET chats_to_notify = ?, notification_messages = ? WHERE time = ?;
    """
    DELETE_TIME = """
        DELETE FROM alarm WHERE time = '%s';
    """
    CREATE_ALARM_DB = """
            CREATE TABLE IF NOT EXISTS alarm (
                time text,
                chats_to_notify text,
                notification_messages text
            );
        """

    @staticmethod
    def schedule_checker():
        while True:
            schedule.run_pending()
            sleep(1)

    def __init__(self, filepath: str):
        self.DB_client = SQLiteClient(filepath)
        self.job_dict = {}

    def set_up(self):
        self.DB_client.create_conn()
        self.DB_client.execute_query(self.CREATE_ALARM_DB)

    def get_chats_to_notify(self, curr_time: str):
        to_notify = self.DB_client.execute_select_query(self.SELECT_TIME % curr_time)
        if to_notify:
            list_of_chats = list(map(int, to_notify[0][1].split()))
            list_of_messages = list(to_notify[0][2].split("#"))
            return list(zip(list_of_chats, list_of_messages))
        return []

    def update_time(self,
                    curr_time: str,
                    chat_id: int,
                    message: str | None = None,
                    bot=None,
                    remove: bool = False):
        time_str = self.DB_client.execute_select_query(self.SELECT_TIME % curr_time)
        if not remove:
            if not time_str:
                self.DB_client.execute_query(self.ADD_TIME, (curr_time, str(chat_id) + " ", message + "#"))
                self.__schedule_work_update(curr_time, bot.scheduled_alarm, update='add')
            else:
                all_chats = list(map(int, time_str[0][1].split()))
                if chat_id not in all_chats:
                    self.DB_client.execute_query(self.UPDATE_TIME,
                                                 (time_str[0][1] + str(chat_id) + " ",
                                                  curr_time,
                                                  time_str[0][2] + message + " "))
        else:
            if time_str:
                all_chats = list(map(int, time_str[0][1].split()))
                all_messages = list(time_str[0][2].split("#"))

                if chat_id in all_chats:
                    ind = all_chats.index(chat_id)
                    all_chats.pop(ind)
                    all_messages.pop(ind)
                    if all_chats:
                        self.DB_client.execute_query(self.UPDATE_TIME,
                                                     (' '.join(str(chat) for chat in all_chats),
                                                      '#'.join(m for m in all_messages),
                                                      curr_time))
                    else:
                        self.DB_client.execute_query(self.DELETE_TIME % curr_time, ())
                        self.__schedule_work_update(curr_time, bot.scheduled_alarm, update='remove')

    def __schedule_work_update(self,
                               curr_time: str,
                               func_to_preform,
                               update: str):
        if update == 'add':
            self.job_dict[curr_time] = schedule.every().day.at(curr_time).do(func_to_preform, curr_time)
        elif update == 'remove' and curr_time in self.job_dict.keys():
            schedule.cancel_job(self.job_dict[curr_time])
