import schedule
from datetime import datetime
from threading import Thread
from time import sleep

from my_bot import bot, ADMIN_CHAT_ID


def scheduled_message():
    return bot.send_message(chat_id=ADMIN_CHAT_ID, text="Hello there")


def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(60)


if __name__ == "__main__":
    while True:
        try:
            schedule.every().tuesday.at("13:16").do(scheduled_message)
            Thread(target=schedule_checker).start()
            bot.start_polling()
        except Exception as error:
            bot.telegram_client.post(method="sendMessage", params={"chat_id": ADMIN_CHAT_ID,
                                                                   "text": f"{datetime.now()}: {error.__class__}"})
