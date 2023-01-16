import psycopg2


class PSQLClient:
    __slots__ = ("host", "user", "password", "database", "conn", "cursor")

    def __init__(self, host, user, password, database):
        self.conn = None
        self.cursor = None
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def create_conn(self):
        try:
            self.conn = psycopg2.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        except Exception as err:
            raise Exception("Connection to database was failed: ", err)
        finally:
            self.cursor = self.conn.cursor() if self.conn else None

    def execute_DML_command(self, command: str, params: tuple = None):
        if self.conn:
            try:
                self.cursor.execute(command, params)
                self.conn.commit()
            except Exception as error:
                raise error.__class__("Invalid SQL Command: ", command, ", params: ", params)
        else:
            raise Exception("No existing connection to: ", self.database)

    def execute_DQL_command(self, command: str, params: tuple = None):
        if self.conn:
            try:
                self.cursor.execute(command, params)
                return self.cursor.fetchall()
            except Exception as err:
                raise Exception("Invalid SQL command: ", command, ". ", err)
        else:
            raise Exception("No existing connection to: ", self.database)
