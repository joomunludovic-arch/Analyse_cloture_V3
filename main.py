from telegram import Bot

@app.get("/test_telegram")
async def test_telegram():
    try:
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("CHAT_ID")
        if not token or not chat_id:
            return {"message": "❌ TELEGRAM_TOKEN ou CHAT_ID non défini."}

        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text="✅ Test réussi ! Ton bot Telegram fonctionne bien 🔥")
        return {"message": "✅ Message Telegram envoyé avec succès."}
    except Exception as e:
        return {"message": f"❌ Erreur : {e}"}
