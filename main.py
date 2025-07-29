from fastapi import FastAPI
from fastapi.responses import JSONResponse
import test_telegram

app = FastAPI()

@app.get("/test_telegram")
def test_telegram_handler():
    try:
        result = test_telegram.run_test()
        return JSONResponse(content={"message": result}, media_type="application/json; charset=utf-8")
    except Exception as e:
        return JSONResponse(content={"message": f"Erreur test Telegram : {e}"}, media_type="application/json; charset=utf-8")
        
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import analyseur
import volatilite
import position_ouverture
import cashflow
import breakout
import os
import uvicorn
import telegram

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
        TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        CHAT_ID = os.getenv("CHAT_ID")
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        message = "✅ Le test Telegram a fonctionné. Si tu vois ce message, tout est bien configuré."
        bot.send_message(chat_id=CHAT_ID, text=message)
        return JSONResponse(content={"message": "Message Telegram envoyé avec succès ✅"}, media_type="application/json; charset=utf-8")
    except Exception as e:
        return JSONResponse(content={"message": f"❌ Erreur Telegram : {e}"}, media_type="application/json; charset=utf-8")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
