import telebot as tb
from envparse import Env
from clients.SQL_client import SQLiteClient
from clients.telegram_client import TelegramClient
from clients.time_provider import TimeProvider, time_provider
from clients.user_provider import UserProvider, user_provider


env = Env()
TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.int("ADMIN_CHAT_ID")


class MyBot(tb.TeleBot):
    def __init__(self, client: TelegramClient, provider_user: UserProvider, provider_time: TimeProvider, *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.telegram_client = client
        self.user_provider = provider_user
        self.time_provider = provider_time

    def setup_res(self):
        self.user_provider.set_up()
        self.time_provider.set_up()

    def start_polling(self, *args, **kwargs):
        self.polling(*args, **kwargs)


telegram_client = TelegramClient(TOKEN, base_url="https://api.telegram.org/")

bot = MyBot(token=TOKEN,
            client=telegram_client,
            provider_user=user_provider,
            provider_time=time_provider)
bot.setup_res()


@bot.message_handler(commands=["hello"])
def registration(message: tb.types.Message):
    print(message)

    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username

    user = bot.user_provider.get_user(user_id=str(user_id))
    create_user = False

    if not user:
        bot.user_provider.create_user(user_id=str(user_id), chat_id=chat_id, username=username)
        create_user = True
    bot.reply_to(message=message, text=f"Вы {'уже' if not create_user else ''} "
                                       f"зарегистрированы, {message.from_user.first_name}.")


@bot.message_handler(commands=["new_alarm"])
def add_alarm(message: tb.types.Message):
    bot.time_provider.update_time(curr_time=message.text[11: 16], chat_id=message.chat.id)
    bot.reply_to(message, text=f"Будильник установлен на {message.text[11: 16]}.")


@bot.message_handler(commands=["delete_alarm"])
def delete_alarm(message: tb.types.Message):
    bot.time_provider.update_time(curr_time=message.text[14: 19], chat_id=message.chat.id, remove=True)
    bot.reply_to(message, text=f"Будильник на {message.text[14: 19]} удален.")




