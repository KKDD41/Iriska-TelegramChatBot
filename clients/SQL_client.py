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



# time_provider = TimeProvider(SQLiteClient("alarm_table.db"))
# time_provider.set_up()
# #
# cn = sqlite3.connect("alarm_table.db")
# cur = cn.cursor()
# cur.execute("""
#     CREATE TABLE IF NOT EXISTS alarm_table(time TEXT PRIMARY KEY, chats_to_notify TEXT);
# """)
#
# cn.commit()
# cn.close()
