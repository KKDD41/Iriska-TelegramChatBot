from datetime import datetime
from my_bot import bot, ADMIN_CHAT_ID


if __name__ == "__main__":
    while True:
        try:
            bot.start_polling()
        except Exception as error:
            bot.telegram_client.post(method="sendMessage", params={"chat_id": ADMIN_CHAT_ID,
                                                                   "text": f"{datetime.now()}: {error.__class__}"})
            pass
