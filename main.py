from fastapi import FastAPI
from fastapi.responses import JSONResponse
import analyseur
import volatilite
import position_ouverture
import cashflow
import breakout
import os
from telegram import Bot

app = FastAPI()

@app.get("/")
def run_analysis():
    try:
        result = analyseur.run()
        return JSONResponse(content={"message": str(result)}, media_type="application/json; charset=utf-8")
    except Exception as e:
        return JSONResponse(content={"message": f"Erreur dans l'analyseur : {e}"}, media_type="application/json; charset=utf-8")

@app.get("/volatilite")
def run_volatility():
    try:
        result = volatilite.run()
        return JSONResponse(content={"message": str(result)}, media_type="application/json; charset=utf-8")
    except Exception as e:
        return JSONResponse(content={"message": f"Erreur dans la volatilité : {e}"}, media_type="application/json; charset=utf-8")

@app.get("/ouverture")
def run_ouverture():
    try:
        result = position_ouverture.run()
        return JSONResponse(content={"message": str(result)}, media_type="application/json; charset=utf-8")
    except Exception as e:
        return JSONResponse(content={"message": f"Erreur dans l'analyse d'ouverture : {e}"}, media_type="application/json; charset=utf-8")

@app.get("/cashflow")
def run_cashflow():
    try:
        result = cashflow.run()
        return JSONResponse(content={"message": str(result)}, media_type="application/json; charset=utf-8")
    except Exception as e:
        return JSONResponse(content={"message": f"Erreur dans le cashflow : {e}"}, media_type="application/json; charset=utf-8")

@app.get("/breakout")
def run_breakout():
    try:
        result = breakout.run()
        return JSONResponse(content={"message": str(result)}, media_type="application/json; charset=utf-8")
    except Exception as e:
        return JSONResponse(content={"message": f"Erreur dans le breakout : {e}"}, media_type="application/json; charset=utf-8")

@app.get("/test_telegram")
def test_telegram():
    try:
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("CHAT_ID")
        if not token or not chat_id:
            return JSONResponse(content={"message": "❌ TELEGRAM_TOKEN ou CHAT_ID non défini."}, media_type="application/json; charset=utf-8")

        bot = Bot(token=token)
        bot.send_message(chat_id=chat_id, text="✅ Test réussi ! Ton bot Telegram fonctionne bien 🔥")
        return JSONResponse(content={"message": "✅ Message Telegram envoyé avec succès."}, media_type="application/json; charset=utf-8")
    except Exception as e:
        return JSONResponse(content={"message": f"❌ Erreur : {e}"}, media_type="application/json; charset=utf-8")

# Pour dev local si besoin
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
