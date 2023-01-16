import datetime
import schedule
from time import sleep
from clients import PSQLClient, TelegramClient


class AlarmsManager:
    __slots__ = "db_client", "job_dict", "tg_client"

    @staticmethod
    def schedule_checker():
        while True:
            schedule.run_pending()
            sleep(10)

    def __init__(self, db_client: PSQLClient, tg_client: TelegramClient):
        self.db_client = db_client
        self.tg_client = tg_client
        self.job_dict = {}

    def get_chats_to_notify(self, curr_time: datetime.time):
        to_notify = self.db_client.execute_DQL_command("""
            SELECT user_id, notification_message
            FROM alarms
            WHERE time_to_notify = %s;
        """, (curr_time,))

        print(to_notify)

    def add_alarm(self, alarm_id: int, user_id: int, time_to_notify: datetime.time, notification_message: str):
        # TODO: check if this alarm already exists

        self.db_client.execute_DML_command("""
            INSERT INTO alarms (id, user_id, time_to_notify, notification_message) 
            VALUES (%s, %s, %s, %s);
        """, (alarm_id, user_id, time_to_notify, notification_message))

        self.__add_job(time_to_notify)

    def remove_alarm(self, user_id: int, time_to_notify: datetime.time):
        self.db_client.execute_DML_command("""
            DELETE FROM alarms
            WHERE user_id = %s AND time_to_notify = %s;
        """, (user_id, time_to_notify))

        if not self.db_client.execute_DQL_command("""SELECT id FROM alarms WHERE time_to_notify = %s;""",
                                                  (time_to_notify,)):
            self.__remove_job(time_to_notify)

    def notify_users(self, curr_time: datetime.time):
        def wrap_notification():
            users_to_notify = self.db_client.execute_DQL_command("""
                SELECT user_id, notification_message
                FROM alarms
                WHERE time_to_notify = %s;
            """, (curr_time,))
            for user_id, message in users_to_notify:
                self.tg_client.post(method="sendMessage", params={"chat_id": user_id, "text": message})

        return wrap_notification()

    def __add_job(self, time_to_notify: datetime.time):
        self.job_dict[time_to_notify] = schedule.every().day.at(time_to_notify.strftime("%H:%M")).do(self.notify_users,
                                                                                                     time_to_notify)

    def __remove_job(self, time_to_notify: datetime.time):
        self.job_dict.pop(time_to_notify)
