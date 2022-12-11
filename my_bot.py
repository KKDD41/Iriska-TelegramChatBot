import telebot as tb
import os
import sys
from threading import Thread
from providers import TimeProvider, UserProvider, TelegramClient
from text_processing import ModelClient
from datetime import datetime, timedelta


# here = os.path.dirname(os.path.realpath(__file__))
# sys.path.append(os.path.join(here, "./vendored"))

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")


class MyBot(tb.TeleBot):
    def __init__(self,
                 telegram_client: TelegramClient,
                 provider_user: UserProvider = None,
                 provider_time: TimeProvider = None,
                 model_client: ModelClient = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telegram_client = telegram_client
        self.user_provider = provider_user
        self.time_provider = provider_time
        self.nlp_model = model_client

    def setup_resources(self):
        for provider in (self.user_provider, self.time_provider, self.nlp_model):
            if provider is not None:
                provider.set_up()

    def start_polling(self, *args, **kwargs):
        if self.time_provider is not None:
            Thread(target=self.time_provider.schedule_checker).start()
        self.polling(non_stop=True, *args, **kwargs)

    def scheduled_alarm(self, curr_time: str):
        if self.time_provider is None:
            raise ConnectionError("Alarm function is currently unavailable.")

        chats_to_notify = self.time_provider.get_chats_to_notify(curr_time)
        for chat, message in chats_to_notify:
            self.send_message(chat_id=chat, text=message)
            if message != "Как Ваши дела?":
                self.send_message(chat_id=chat, text="Все ли у Вас в порядке?")

    def set_poll_handler_type(self, poll_type: str):
        self.poll_answer_handlers.clear()

        @tb.TeleBot.poll_answer_handler(self)
        def answers_handler(poll_answers: tb.types.PollAnswer):
            if poll_type == "relapse":
                self.user_provider.update_test(str(poll_answers.user.id), rl_results=poll_answers.option_ids)
            elif poll_type == "depression":
                bot.user_provider.update_test(str(poll_answers.user.id), dp_results=poll_answers.option_ids)

        return answers_handler


user_provider = UserProvider("databases/users.db",
                             fp_relapse_criteria="poll_options/relapse_poll_options.txt",
                             fp_depression_criteria="poll_options/depression_poll_options.txt")
time_provider = TimeProvider("databases/alarm.db")
tg_client = TelegramClient(TOKEN, base_url="https://api.telegram.org/")
nlp_model_loader = ModelClient("nlp_resources_files/data.pth",
                               "nlp_resources_files/intents.json")
bot = MyBot(token=TOKEN,
            telegram_client=tg_client,
            provider_user=user_provider,
            provider_time=time_provider,
            model_client=nlp_model_loader)
bot.setup_resources()


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
        raise ConnectionError("Извините, функция будильника для меня сейчас не доступна.")

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
        raise ConnectionError("Извините, функция будильника для меня сейчас не доступна.")

    curr_time = message.text[14: 19]
    bot.time_provider.update_time(curr_time=curr_time,
                                  chat_id=message.chat.id,
                                  bot=bot,
                                  remove=True)
    bot.reply_to(message, text=f"Будильник на {curr_time} удален.")


@bot.callback_query_handler(func=lambda call: True)
def reply(call: tb.types.CallbackQuery):
    if call.data == "relapse":
        bot.send_poll(chat_id=call.from_user.id,
                      question="Тест на возможные причины возникновения тяги:",
                      options=[option[0] for option in bot.user_provider.RELAPSE_POLL_OPTIONS],
                      allows_multiple_answers=True,
                      open_period=120,
                      is_anonymous=False)
        bot.set_poll_handler_type("relapse")
    elif call.data == "depression":
        bot.send_poll(chat_id=call.from_user.id,
                      question="Тест на симптоматику депрессивной фазы:",
                      options=[option[0] for option in bot.user_provider.DEPRESSION_POLL_OPTIONS],
                      allows_multiple_answers=True,
                      open_period=120,
                      is_anonymous=False)
        bot.set_poll_handler_type("depression")


@bot.message_handler(commands=["take_test"])
def choose_test(message: tb.types.Message):
    markup = tb.types.InlineKeyboardMarkup()
    markup.add(tb.types.InlineKeyboardButton(text="Тест на настроение", callback_data="depression"),
               tb.types.InlineKeyboardButton(text="Вероятность рецидива", callback_data="relapse"))
    bot.send_message(chat_id=message.chat.id, text="Что Вас беспокоит?", reply_markup=markup, timeout=30)


@bot.message_handler(commands=["statistics"])
def provide_statistics(message: tb.types.Message):
    stat_image = bot.user_provider.create_statistics(str(message.from_user.id))
    bot.send_photo(chat_id=message.chat.id, photo=stat_image)


@bot.message_handler(commands=["update_day"])
def update_days_sober(message: tb.types.Message):
    curr_day = int(message.text[12:])
    date_of_update = datetime.fromtimestamp(message.date).date()
    bot.user_provider.update_day(str(message.from_user.id), curr_day, message.date)

    bot.reply_to(message,
                 text=f"Текущий день трезвости {curr_day}. Счетчик идет от {date_of_update - timedelta(curr_day)}.")
    if curr_day < 10:
        bot.send_message(message.chat.id, text="Сейчас Вам может будет тяжело, но это того стоит :)")
    elif curr_day < 30:
        bot.send_message(message.chat.id, text="Вы отлично справляетесь, так держать!")
    else:
        bot.send_message(message.chat.id, text="Вы уже больше месяца чистый, поздравляю!")


@bot.message_handler(content_types=["text"])
def get_text_message(message: tb.types.Message):
    if bot.nlp_model is None:
        bot.send_message(chat_id=message.chat.id, text="Извините, на данном этапе обработка текстовых сообщений мне "
                                                       "не доступна.")
    else:
        responses = list(bot.nlp_model.get_response(message.text).split(sep="\n\n"))
        for response in responses:
            bot.send_message(chat_id=message.chat.id, text=response)
