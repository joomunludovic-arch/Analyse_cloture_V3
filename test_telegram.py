# test_telegram.py

import os
from telegram import Bot

def run_test():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token or not chat_id:
        return "Erreur : TELEGRAM_TOKEN ou CHAT_ID non défini dans les variables d’environnement."

    bot = Bot(token=token)
    bot.send_message(chat_id=chat_id, text="✅ Test réussi ! Ton bot Telegram fonctionne 🔥")
    return "Message Telegram envoyé avec succès ✅"
