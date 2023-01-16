import telebot as tb
import os
from threading import Thread
from providers import AlarmsManager, PSQLClient, TelegramClient, DBAccessManager
from text_processing import ModelClient
from datetime import datetime, timedelta
from config import host, user, db_name, password

TOKEN = os.environ["TELEGRAM_TOKEN"]
ADMIN_CHAT_ID = os.environ["ADMIN_CHAT_ID"]


class MyBot(tb.TeleBot):
    __slots__ = "telegram_client", "user_provider", "time_provider", "nlp_model"

    def __init__(self,
                 telegram_client: TelegramClient,
                 provider_user: DBAccessManager = None,
                 provider_time: AlarmsManager = None,
                 model_client: ModelClient = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telegram_client = telegram_client
        self.user_provider = provider_user
        self.time_provider = provider_time
        self.nlp_model = model_client

    def setup_resources(self):
        pass

    def start_polling(self, *args, **kwargs):
        if self.time_provider is not None:
            Thread(target=self.time_provider.schedule_checker).start()
        self.polling(non_stop=True, *args, **kwargs)

    def set_poll_handler_type(self, poll_type: str, message_date: datetime.date):
        self.poll_answer_handlers.clear()

        @tb.TeleBot.poll_answer_handler(self)
        def answers_handler(poll_answers: tb.types.PollAnswer):
            if poll_type == "relapse":
                self.user_provider.update_test(poll_answers.user.id, message_date,
                                               rl_results=poll_answers.option_ids)
            elif poll_type == "depression":
                bot.user_provider.update_test(poll_answers.user.id, message_date,
                                              dp_results=poll_answers.option_ids)

        return answers_handler


db_client = PSQLClient(host=host, user=user, password=password, database=db_name)
db_client.create_conn()
dba_manager = DBAccessManager(fp_relapse_criteria="poll_options/relapse_poll_options.txt",
                              fp_depression_criteria="poll_options/depression_poll_options.txt",
                              db_client=db_client)
tg_client = TelegramClient(TOKEN, base_url="https://api.telegram.org/")
nlp_model_loader = ModelClient("nlp_resources_files/data.pth",
                               "nlp_resources_files/intents.json")
time_provider = AlarmsManager(db_client, tg_client)
bot = MyBot(token=TOKEN,
            telegram_client=tg_client,
            provider_user=dba_manager,
            provider_time=time_provider,
            model_client=nlp_model_loader)
bot.setup_resources()


@bot.message_handler(commands=["hello"])
def registration(message: tb.types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    user_info = bot.user_provider.get_user(user_id)

    create_user = False
    if not user_info:
        bot.user_provider.create_user(id=user_id, username=username)
        create_user = True
    bot.reply_to(message=message, text=f"Вы {'уже' if not create_user else ''} "
                                       f"зарегистрированы, {message.from_user.first_name}.")


@bot.message_handler(commands=["new_alarm"])
def add_alarm(message: tb.types.Message):
    alarm_id = message.id
    curr_time = datetime.strptime(message.text[11: 16], "%H:%M").time()
    curr_message = message.text[16:]

    if not curr_message:
        curr_message = "Как Ваши дела?"

    bot.time_provider.add_alarm(alarm_id=alarm_id,
                                user_id=message.from_user.id,
                                time_to_notify=curr_time,
                                notification_message=curr_message
                                )
    bot.reply_to(message, text=f"Будильник установлен на {curr_time}.")


@bot.message_handler(commands=["delete_alarm"])
def delete_alarm(message: tb.types.Message):
    curr_time = datetime.strptime(message.text[14: 19], "%H:%M").time()
    bot.time_provider.remove_alarm(user_id=message.from_user.id,
                                   time_to_notify=curr_time
                                   )
    bot.reply_to(message, text=f"Будильник на {curr_time} удален.")


@bot.callback_query_handler(func=lambda call: True)
def reply(call: tb.types.CallbackQuery):
    message_date = datetime.fromtimestamp(call.message.date).date()
    if call.data == "relapse":
        bot.send_poll(chat_id=call.from_user.id,
                      question="Тест на возможные причины возникновения тяги:",
                      options=[option[0] for option in bot.user_provider.RELAPSE_POLL_OPTIONS],
                      allows_multiple_answers=True,
                      open_period=120,
                      is_anonymous=False)
        bot.set_poll_handler_type("relapse", message_date)
    elif call.data == "depression":
        bot.send_poll(chat_id=call.from_user.id,
                      question="Тест на симптоматику депрессивной фазы:",
                      options=[option[0] for option in bot.user_provider.DEPRESSION_POLL_OPTIONS],
                      allows_multiple_answers=True,
                      open_period=120,
                      is_anonymous=False)
        bot.set_poll_handler_type("depression", message_date)


@bot.message_handler(commands=["take_test"])
def choose_test(message: tb.types.Message):
    markup = tb.types.InlineKeyboardMarkup()
    markup.add(tb.types.InlineKeyboardButton(text="Тест на настроение", callback_data="depression"),
               tb.types.InlineKeyboardButton(text="Вероятность рецидива", callback_data="relapse"))
    bot.send_message(chat_id=message.chat.id, text="Что Вас беспокоит?", reply_markup=markup, timeout=30)


@bot.message_handler(commands=["statistics"])
def provide_statistics(message: tb.types.Message):
    stat_image = bot.user_provider.create_statistics(message.from_user.id)
    bot.send_photo(chat_id=message.chat.id, photo=stat_image)


# @bot.message_handler(commands=["update_day"])
# def update_days_sober(message: tb.types.Message):
#     curr_day = int(message.text[12:])
#     date_of_update = datetime.fromtimestamp(message.date).date()
#     bot.user_provider.update_day(str(message.from_user.id), curr_day, message.date)
#
#     bot.reply_to(message,
#                  text=f"Текущий день трезвости {curr_day}. Счетчик идет от {date_of_update - timedelta(curr_day)}.")
#     if curr_day < 10:
#         bot.send_message(message.chat.id, text="Сейчас Вам может будет тяжело, но это того стоит :)")
#     elif curr_day < 30:
#         bot.send_message(message.chat.id, text="Вы отлично справляетесь, так держать!")
#     else:
#         bot.send_message(message.chat.id, text="Вы уже больше месяца чистый, поздравляю!")


# @bot.message_handler(commands=["get_day"])
# def get_day_sober(message: tb.types.Message):
#     day, date_of_update = bot.user_provider.return_day(message.from_user.id)
#     date_of_update = datetime.fromtimestamp(date_of_update)
#     curr_date = datetime.fromtimestamp(message.date)
#
#     bot.reply_to(message, text=f"На момент {date_of_update} у Вас был {day}-й день трезвости.")
#     if date_of_update != curr_date:
#         bot.send_message(chat_id=message.chat.id,
#                          text=f"Сегодня {curr_date}. Пожалуйста, обновите сегодня день трезвости.")


# @bot.message_handler(content_types=["text"])
# def get_text_message(message: tb.types.Message):
#     if bot.nlp_model is None:
#         bot.send_message(chat_id=message.chat.id, text="Извините, на данном этапе обработка текстовых сообщений мне "
#                                                        "не доступна.")
#     else:
#         responses = list(bot.nlp_model.get_response(message.text).split(sep="\n\n"))
#         for response in responses:
#             bot.send_message(chat_id=message.chat.id, text=response)
