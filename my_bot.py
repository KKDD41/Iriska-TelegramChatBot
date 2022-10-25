import telebot as tb
from envparse import Env
from threading import Thread
from providers import TimeProvider, UserProvider, TelegramClient

env = Env()
TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.int("ADMIN_CHAT_ID")


class MyBot(tb.TeleBot):
    def __init__(self,
                 client: TelegramClient,
                 provider_user: UserProvider,
                 provider_time: TimeProvider = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telegram_client = client
        self.user_provider = provider_user
        self.time_provider = provider_time

    def setup_res(self):
        self.user_provider.set_up()
        if self.time_provider is not None:
            self.time_provider.set_up()

    def start_polling(self, *args, **kwargs):
        if self.time_provider is not None:
            Thread(target=self.time_provider.schedule_checker).start()
        self.polling(non_stop=True, *args, **kwargs)

    def scheduled_alarm(self, curr_time: str):
        if bot.time_provider is None:
            raise ConnectionError("Alarm function is currently unavailable.")

        chats_to_notify = self.time_provider.get_chats_to_notify(curr_time)
        for chat, message in chats_to_notify:
            self.send_message(chat_id=chat, text=message)
            if message != "Как Ваши дела?":
                self.send_message(chat_id=chat, text="Все ли у Вас в порядке?")


user_provider = UserProvider("C:\\Users\\Kate\\Desktop\\IRISKA\\Irirska-TelegramChatBot\\databases\\users.db")
time_provider = TimeProvider("C:\\Users\\Kate\\Desktop\\IRISKA\\Irirska-TelegramChatBot\\databases\\alarm.db")
telegram_client = TelegramClient(TOKEN, base_url="https://api.telegram.org/")
bot = MyBot(token=TOKEN,
            client=telegram_client,
            provider_user=user_provider,
            provider_time=time_provider)
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
    bot.reply_to(message=message, text=f"Вы {'уже' if not create_user else ''} "
                                       f"зарегистрированы, {message.from_user.first_name}.")


@bot.message_handler(commands=["new_alarm"])
def add_alarm(message: tb.types.Message):
    if bot.time_provider is None:
        raise ConnectionError("Alarm function is currently unavailable.")

    curr_time = message.text[11: 16]
    curr_message = message.text[16:]
    if not curr_message:
        curr_message = "Как Ваши дела?"
    bot.time_provider.update_time(curr_time=curr_time,
                                  chat_id=message.chat.id,
                                  message=curr_message,
                                  bot=bot)
    bot.reply_to(message, text=f"Будильник установлен на {curr_time}.")


@bot.message_handler(commands=["delete_alarm"])
def delete_alarm(message: tb.types.Message):
    if bot.time_provider is None:
        raise ConnectionError("Alarm function is currently unavailable.")

    curr_time = message.text[14: 19]
    bot.time_provider.update_time(curr_time=curr_time,
                                  chat_id=message.chat.id,
                                  bot=bot,
                                  remove=True)
    bot.reply_to(message, text=f"Будильник на {curr_time} удален.")

