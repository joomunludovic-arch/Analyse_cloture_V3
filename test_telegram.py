import os
import telegram

# ✅ Tu dois avoir ces variables définies sur Render (ou dans un .env en local)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def test_telegram():
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        message = "✅ Le test Telegram a fonctionné.\nSi tu vois ce message, tout est correctement configuré !"
        bot.send_message(chat_id=CHAT_ID, text=message)
        print("✅ Message envoyé avec succès sur Telegram.")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")

if __name__ == "__main__":
    test_telegram()
