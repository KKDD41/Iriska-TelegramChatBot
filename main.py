import telebot as tb
from datetime import datetime
from envparse import Env
from clients.telegram_client import TelegramClient
from clients.SQL_client import SQLiteClient, UserProvider

env = Env()
TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.int("ADMIN_CHAT_ID")


class MyBot(tb.TeleBot):
    def __init__(self, client: TelegramClient, provider: UserProvider, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telegram_client = client
        self.user_provider = provider

    def setup_res(self):
        self.user_provider.set_up()


telegram_client = TelegramClient(TOKEN, base_url="https://api.telegram.org/")
user_provider = UserProvider(SQLiteClient("C:\\Users\\Kate\\Desktop\\IRISKA\\Irirska-TelegramChatBot\\clients\\users.db"))
bot = MyBot(token=TOKEN, client=telegram_client, provider=user_provider)
bot.setup_res()


@bot.message_handler(commands=["hello"])
def registration(message: tb.types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username

    user = bot.user_provider.get_user(user_id=str(user_id))
    create_user = False

    if not user:
        bot.user_provider.create_user(user_id=str(user_id), chat_id=chat_id, username=username)
        create_user = True
    bot.reply_to(message=message, text=f"Вы {'уже' if not create_user else ''} зарегистрированы, {username}.")
    return


def reaction_processing(message: tb.types.Message):
    bot.reply_to(message, text="рад что тебе понравилось")


@bot.message_handler(content_types=["text"])
def auto_reply(message: tb.types.Message):
    bot.reply_to(message, text="Пока могу рассказать только анекдот. Штирлиц и Мюллер ездили по очереди на танке. "
                               "Очередь редела, но не расходилась...")
    bot.register_next_step_handler(message, callback=reaction_processing)


if __name__ == "__main__":
    while True:
        try:
            bot.polling()
        except Exception as error:
            bot.telegram_client.post(method="sendMessage", params={"chat_id": ADMIN_CHAT_ID,
                                                                   "text": f"{datetime.now()}: {error.__class__} :"
                                                                           f" {error}"})
