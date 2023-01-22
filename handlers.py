from my_bot import IriskaBot
from telebot import types
from datetime import datetime
from config import TOKEN, dba_manager, nlp_model_loader, time_provider, tg_client


bot = IriskaBot(telegram_client=tg_client,
                provider_user=dba_manager,
                provider_time=time_provider,
                model_client=nlp_model_loader,
                token=TOKEN)


@bot.message_handler(commands=["hello"])
def registration(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    user_info = bot.user_provider.get_user(user_id)

    create_user = False
    if not user_info:
        bot.user_provider.create_user(id=user_id, username=username)
        create_user = True
    bot.reply_to(message=message, text=f"You have {'already' if not create_user else ''} "
                                       f" registered, {message.from_user.first_name}.")


@bot.message_handler(commands=["new_alarm"])
def add_alarm(message: types.Message):
    alarm_id = message.id
    curr_time = datetime.strptime(message.text[11: 16], "%H:%M").time()
    curr_message = message.text[16:]

    if not curr_message:
        curr_message = "How are you doing?"

    bot.time_provider.add_alarm(alarm_id=alarm_id,
                                user_id=message.from_user.id,
                                time_to_notify=curr_time,
                                notification_message=curr_message
                                )
    bot.reply_to(message, text=f"Alarm set to {curr_time}.")


@bot.message_handler(commands=["delete_alarm"])
def delete_alarm(message: types.Message):
    curr_time = datetime.strptime(message.text[14: 19], "%H:%M").time()
    bot.time_provider.remove_alarm(user_id=message.from_user.id,
                                   time_to_notify=curr_time)
    bot.reply_to(message, text=f"Alarm {curr_time} was successfully deleted.")


@bot.callback_query_handler(func=lambda call: True)
def reply(call: types.CallbackQuery):
    message_date = datetime.fromtimestamp(call.message.date).date()
    if call.data == "relapse":
        bot.send_poll(chat_id=call.from_user.id,
                      question="Test for possible causes of alcohol cravings:",
                      options=[option[0] for option in bot.user_provider.RELAPSE_POLL_OPTIONS],
                      allows_multiple_answers=True,
                      open_period=120,
                      is_anonymous=False)
        bot.set_poll_handler_type("relapse", message_date)
    elif call.data == "depression":
        bot.send_poll(chat_id=call.from_user.id,
                      question="Mood change test:",
                      options=[option[0] for option in bot.user_provider.DEPRESSION_POLL_OPTIONS],
                      allows_multiple_answers=True,
                      open_period=120,
                      is_anonymous=False)
        bot.set_poll_handler_type("depression", message_date)


@bot.message_handler(commands=["take_test"])
def choose_test(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Mood change", callback_data="depression"),
               types.InlineKeyboardButton(text="Relapse probability", callback_data="relapse"))
    bot.send_message(chat_id=message.chat.id,
                     text="What worries you?",
                     reply_markup=markup,
                     timeout=20)


@bot.message_handler(commands=["poll_statistics"])
def provide_poll_statistics(message: types.Message):
    stat_image = bot.user_provider.create_poll_statistics(message.from_user.id)
    if not stat_image:
        bot.send_message(chat_id=message.chat.id,
                         text="There is not data about your polls' results in this month.")
    bot.send_photo(chat_id=message.chat.id, photo=stat_image)


@bot.message_handler(commands=["dose_statistics"])
def provide_dose_statistics(message: types.Message):
    stat_image = bot.user_provider.create_dose_statistics(message.from_user.id)
    if not stat_image:
        bot.send_message(chat_id=message.chat.id,
                         text="There is not data about your ethanol consumption in this month.")
    bot.send_photo(chat_id=message.chat.id, photo=stat_image)


@bot.message_handler(commands=["day_dose"])
def update_day_dose(message: types.Message):
    dose_string = list(message.text.split(maxsplit=1))[1]
    date = datetime.fromtimestamp(message.date).date()

    bot.user_provider.update_month_calendar(user_id=message.from_user.id,
                                            dose_string=dose_string,
                                            day=date)
    bot.send_message(chat_id=message.from_user.id,
                     text="Today's dose was recorded.")


@bot.message_handler(content_types=["text"])
def get_text_message(message: types.Message):
    if bot.nlp_model is None:
        bot.send_message(chat_id=message.chat.id, text="Sorry, text messaging is not available to me at this stage.")
    else:
        responses = list(bot.nlp_model.get_response(message.text).split(sep="\n\n"))
        for response in responses:
            bot.send_message(chat_id=message.chat.id, text=response)



