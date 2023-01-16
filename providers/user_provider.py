import datetime
from clients import PSQLClient
from matplotlib import use
import matplotlib.pyplot as plt
from numpy import array
from PIL import Image
from io import BytesIO


# class UserProvider:
#     __slots__ = (
#         "DB_client", "fp_relapse_criteria", "fp_depression_criteria", "RELAPSE_POLL_OPTIONS", "DEPRESSION_POLL_OPTIONS")
#
#     CREATE_USER = """
#         INSERT INTO users(user_id, chat_id, username, dp_results, rl_results, number_of_day, data)
#         VALUES (?, ?, ?, ?, ?, ?, ?);
#     """
#
#     GET_USER = """
#         SELECT user_id, chat_id, username, dp_results, rl_results, number_of_day, data FROM users WHERE user_id = %s;
#     """
#
#     UPDATE_TEST = """
#         UPDATE users SET dp_results = ?, rl_results = ? WHERE user_id = ?;
#     """
#
#     UPDATE_DAY = """
#         UPDATE users SET number_of_day = ?, data = ? WHERE user_id = ?;
#     """
#
#     CREATE_USERS_DB = """
#             CREATE TABLE IF NOT EXISTS users (
#                 user_id text PRIMARY KEY,
#                 chat_id integer,
#                 username text,
#                 dp_results text,
#                 rl_results text,
#                 number_of_day integer,
#                 data text
#             );
#         """
#
#     def __init__(self, filepath: str, fp_relapse_criteria: str, fp_depression_criteria: str):
#         self.DEPRESSION_POLL_OPTIONS = None
#         self.RELAPSE_POLL_OPTIONS = None
#         self.DB_client = None  # SQLiteClient(filepath)
#         self.fp_relapse_criteria = fp_relapse_criteria
#         self.fp_depression_criteria = fp_depression_criteria
#
#     def update_day(self, user_id: str, curr_day: int, curr_date):
#         self.DB_client.execute_DML_command(self.UPDATE_DAY, (curr_day, curr_date, user_id))
#
#     def return_day(self, user_id):
#         return self.get_user(user_id)[5:]


class DBAccessManager:
    __slots__ = ("db_client", "RELAPSE_POLL_OPTIONS", "DEPRESSION_POLL_OPTIONS")

    def __init__(self, fp_relapse_criteria: str, fp_depression_criteria: str, db_client: PSQLClient):
        self.db_client = db_client
        try:
            with open(fp_relapse_criteria) as fr:
                lines = fr.readlines()
                self.RELAPSE_POLL_OPTIONS = [list(option_string.rsplit(maxsplit=1)) for option_string in lines]
            with open(fp_depression_criteria) as fr:
                lines = fr.readlines()
                self.DEPRESSION_POLL_OPTIONS = [list(option_string.rsplit(maxsplit=1)) for option_string in lines]
        except Exception as err:
            raise Exception("Poll options files are unavailable")

    def get_user(self, id: int):
        users_info = self.db_client.execute_DQL_command(f"""
            SELECT * 
            FROM users
            WHERE id = %s;
        """, (id,))
        return users_info[0] if users_info else None

    def create_user(self, id: int, username: str):
        self.db_client.execute_DML_command("""
            INSERT INTO users (id, username)
            VALUES (%s, %s);
        """, (id, username))

    def update_test(self, id: int, date: datetime, dp_results=None, rl_results=None):
        rl_results = "" if rl_results is None else self.__answers_processing(rl_results, "relapse")
        dp_results = "" if dp_results is None else self.__answers_processing(dp_results, "depression")

        if dp_results:
            self.db_client.execute_DML_command("""
                INSERT INTO depression_poll
                VALUES (%s, %s, %s);
            """, (id, dp_results, date)
                                               )
        if rl_results:
            self.db_client.execute_DML_command("""
                INSERT INTO relapse_poll
                VALUES (%s, %s, %s);
            """, (id, rl_results, date)
                                               )

    def __answers_processing(self, answers, poll_type: str):
        groups_counter = [0, 0, 0]
        if poll_type == "depression":
            for ans in answers:
                groups_counter[int(self.DEPRESSION_POLL_OPTIONS[ans][1])] += 1
        elif poll_type == "relapse":
            for ans in answers:
                groups_counter[int(self.RELAPSE_POLL_OPTIONS[ans][1])] += 1
        return "".join([str(cntr) for cntr in groups_counter])

    def create_statistics(self, user_id: int):
        dp_answers = self.db_client.execute_DQL_command("""
                    SELECT answers
                    FROM depression_poll
                    WHERE user_id = %s;
                """, (user_id,))
        rl_answers = self.db_client.execute_DQL_command(f"""
                    SELECT answers
                    FROM relapse_poll
                    WHERE user_id = %s;
                """, (user_id,))
        dp_points = []
        rl_points = []
        for test_result in dp_answers:
            dp_points.append([c for c in test_result])
        for test_result in rl_answers:
            rl_points.append([c for c in test_result])

        use("Agg")
        figure, (axis1, axis2) = plt.subplots(2, 1)

        colors = ("c", "b", "r")
        labels = ("emotional state", "relationships and\nprofessional activity", "physical state")

        if dp_points:
            for i in range(3):
                axis1.plot(array(list(range(1, len(dp_points) + 1))),
                           array([int(point[0][i]) for point in dp_points]),
                           color=colors[i],
                           label=labels[i])
            axis1.plot(array(list(range(1, len(dp_points) + 1))),
                       array([sum(int(c) for c in point) for point in dp_points]),
                       color='k',
                       linestyle="-",
                       linewidth="4",
                       label="General")
        if rl_points:
            for i in range(3):
                axis2.plot(array(list(range(1, len(rl_points) + 1))),
                           array([int(point[0][i]) for point in rl_points]),
                           color=colors[i],
                           label=labels[i])
            axis2.plot(array(list(range(1, len(rl_points) + 1))),
                       array([sum(int(c) for c in point) for point in rl_points]),
                       color='k',
                       linestyle="-",
                       linewidth="4",
                       label="General")
        axis1.set_ylim([0, 10])
        axis2.set_ylim([0, 10])
        axis1.set_xticklabels([])
        axis2.set_xticklabels([])

        axis1.set_title(label="General emotional state tracker")
        axis1.legend(loc="upper right", fontsize=8)
        axis2.set_title(label="Relapse factors tracker")
        axis2.legend(loc="upper right", fontsize=8)
        figure.tight_layout()

        bytes_io = BytesIO()
        plt.savefig(bytes_io)
        bytes_io.seek(0)
        image = Image.open(bytes_io)

        return image
