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

    RELAPSE_POLL_OPTIONS = []
    DEPRESSION_POLL_OPTIONS = []

    def __init__(self, filepath: str):
        self.DB_client = SQLiteClient(filepath)

    def set_up(self, fp_relapse_criteria: str, fp_depression_criteria: str):
        self.DB_client.create_conn()
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
        print("fantastic")

    def create_statistics(self, user_id: str):
        users_data = self.get_user(user_id=user_id)

        # TODO: 3. Create statistics provider
        pass

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
        print("great")
        return "".join([str(cntr) for cntr in groups_counter])


