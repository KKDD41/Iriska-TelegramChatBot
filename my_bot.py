import telebot as tb
from threading import Thread
from providers import AlarmsManager, TelegramClient, DBAccessManager
from text_processing import ModelClient
from datetime import datetime


class IriskaBot(tb.TeleBot):
    __slots__ = "telegram_client", "user_provider", "time_provider", "nlp_model"

    def __init__(self,
                 telegram_client: TelegramClient = None,
                 provider_user: DBAccessManager = None,
                 provider_time: AlarmsManager = None,
                 model_client: ModelClient = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telegram_client = telegram_client
        self.user_provider = provider_user
        self.time_provider = provider_time
        self.nlp_model = model_client

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
                self.user_provider.update_test(poll_answers.user.id, message_date,
                                               dp_results=poll_answers.option_ids)

        return answers_handler

