from clients import SQLiteClient
from matplotlib import use
import matplotlib.pyplot as plt
from numpy import array
from PIL import Image
from io import BytesIO

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

    RELAPSE_POLL_OPTIONS = []
    DEPRESSION_POLL_OPTIONS = []

    def __init__(self, filepath: str):
        self.DB_client = SQLiteClient(filepath)

    def set_up(self, fp_relapse_criteria: str, fp_depression_criteria: str):
        self.DB_client.create_conn()
        use("Agg")
        with open(fp_relapse_criteria) as fr:
            lines = fr.readlines()
            self.RELAPSE_POLL_OPTIONS = [list(option_string.rsplit(maxsplit=1)) for option_string in lines]

        with open(fp_depression_criteria) as fr:
            lines = fr.readlines()
            self.DEPRESSION_POLL_OPTIONS = [list(option_string.rsplit(maxsplit=1)) for option_string in lines]

    def get_user(self, user_id: str):
        user = self.DB_client.execute_select_query(self.GET_USER % user_id)
        return user[0] if user else []

    def create_user(self, user_id: str, chat_id: int, username: str, dp_results: str = "", rl_results: str = ""):
        self.DB_client.execute_query(self.CREATE_USER, (user_id, chat_id, username, dp_results, rl_results))

    def update_test(self, user_id: str, dp_results=None, rl_results=None):
        rl_results = "" if rl_results is None else self.__answers_processing(rl_results, "relapse")
        dp_results = "" if dp_results is None else self.__answers_processing(dp_results, "depression")

        user = self.get_user(user_id)

        print(dp_results, " ", rl_results)
        if user is None:
            raise ValueError(f"The user {user_id} was not registered")

        self.DB_client.execute_query(self.UPDATE_TEST,
                                     (user[3] + " " + dp_results if dp_results else user[3],
                                      user[4] + " " + rl_results if rl_results else user[4],
                                      user_id))

    def create_statistics(self, user_id: str):
        users_data = self.get_user(user_id=user_id)
        figure, (axis1, axis2) = plt.subplots(2, 1)

        dp_points = []
        rl_points = []
        for test_result in users_data[3].split():
            dp_points.append(list(map(int, [c for c in test_result])))
        for test_result in users_data[4].split():
            rl_points.append(list(map(int, [c for c in test_result])))

        for i in range(3):
            axis1.plot(array(list(range(len(dp_points)))), array([point[i] for point in dp_points]))
            axis2.plot(array(list(range(len(rl_points)))), array([point[i] for point in rl_points]))

        bytes_io = BytesIO()
        plt.savefig(bytes_io)
        bytes_io.seek(0)
        image = Image.open(bytes_io)

        return image

        # TODO: 5. construct beautiful graphics

    def __answers_processing(self, answers, poll_type: str):
        groups_counter = [0, 0, 0]
        print(self.DEPRESSION_POLL_OPTIONS)
        print(answers)
        if poll_type == "depression":
            for ans in answers:
                groups_counter[int(self.DEPRESSION_POLL_OPTIONS[ans][1])] += 1
        elif poll_type == "relapse":
            for ans in answers:
                groups_counter[int(self.RELAPSE_POLL_OPTIONS[ans][1])] += 1
        return "".join([str(cntr) for cntr in groups_counter])



