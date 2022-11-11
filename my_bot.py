import telebot as tb
from envparse import Env
from threading import Thread
from providers import TimeProvider, UserProvider, TelegramClient
from text_processing import ModelClient

env = Env()
TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.int("ADMIN_CHAT_ID")


class MyBot(tb.TeleBot):
    def __init__(self,
                 telegram_client: TelegramClient,
                 provider_user: UserProvider,
                 provider_time: TimeProvider = None,
                 model_client: ModelClient = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telegram_client = telegram_client
        self.user_provider = provider_user
        self.time_provider = provider_time
        self.nlp_model = model_client

    def setup_res(self):
        self.user_provider.set_up()
        if self.nlp_model is not None:
            self.nlp_model.set_up(fp_relapse_criteria="./text_processing/nlp_resources_files/relapse_poll_options.txt",
                                  fp_depression_criteria="./text_processing/nlp_resources_files"
                                                         "/depression_poll_options.txt")
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


user_provider = UserProvider("databases/users.db")
time_provider = TimeProvider("databases/alarm.db")
tg_client = TelegramClient(TOKEN, base_url="https://api.telegram.org/")
nlp_model_loader = ModelClient()
bot = MyBot(token=TOKEN,
            telegram_client=tg_client,
            provider_user=user_provider,
            provider_time=time_provider,
            model_client=nlp_model_loader)
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


@bot.poll_answer_handler()
def answers(pollAnswers: tb.types.PollAnswer):
    # TODO: Count positive answers and return a result
    print(pollAnswers.option_ids)
    return


@bot.message_handler(content_types=["text"])
def get_text_message(message: tb.types.Message):
    if bot.nlp_model is None:
        bot.send_message(chat_id=message.chat.id, text="Извините, на данном этапе обработка текстовых сообщений мне "
                                                       "не доступна.")
    else:
        response = bot.nlp_model.get_response(message.text)
        if response == "relapse test send":
            bot.send_poll(chat_id=message.chat.id,
                          question="Тест на возможные причины возникновения тяги:",
                          options=bot.nlp_model.RELAPSE_POLL_OPTIONS,
                          allows_multiple_answers=True,
                          is_anonymous=False)
            bot.poll_answer_handler(answers)
        elif response == "depression test send":
            bot.send_poll(chat_id=message.chat.id,
                          question="Тест на симптоматику депрессивного эпизода:",
                          options=bot.nlp_model.DEPRESSION_POLL_OPTIONS,
                          allows_multiple_answers=True,
                          is_anonymous=False)
            bot.poll_answer_handler(answers)
        else:
            bot.send_message(chat_id=message.chat.id, text=response)
