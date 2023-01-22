import os
from providers import AlarmsManager, PSQLClient, TelegramClient, DBAccessManager
from text_processing import ModelClient


host = "127.0.0.1"
user = "postgres"
password = "kate2003"
db_name = "iriska_database"

TOKEN = os.environ["TELEGRAM_TOKEN"]
ADMIN_CHAT_ID = os.environ["ADMIN_CHAT_ID"]

bot_commands = """hello - register to get access to main functions
new_alarm - create custom text reminder, format "hh:mm NOTIFICATION MESSAGE"
delete_alarm - delete alarm set on hh:mm
take_test - take test 
poll_statistics - get poll statistics
day_dose - update today's ethanol dose 
dose_statistics - get dose statistics"""

db_client = PSQLClient(host=host,
                       user=user,
                       password=password,
                       database=db_name)
db_client.create_conn()
dba_manager = DBAccessManager(fp_relapse_criteria="stat_resources_files/relapse_poll_options.txt",
                              fp_depression_criteria="stat_resources_files/depression_poll_options.txt",
                              fp_drinks_percentage="stat_resources_files/ethanol_doses.json",
                              db_client=db_client)
tg_client = TelegramClient(TOKEN,
                           base_url="https://api.telegram.org/")
nlp_model_loader = ModelClient("nlp_resources_files/data.pth",
                               "nlp_resources_files/intents.json")
time_provider = AlarmsManager(db_client, tg_client)

