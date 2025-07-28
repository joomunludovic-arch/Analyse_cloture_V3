from fastapi import FastAPI
from fastapi.responses import JSONResponse
import analyseur
import volatilite
import position_ouverture
import cashflow
import os
import uvicorn

app = FastAPI()

@app.get("/")
def run_analysis():
    try:
        result = analyseur.run()
        return JSONResponse(
            content={"message": str(result)},
            media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Erreur dans l'analyseur : {e}"},
            media_type="application/json; charset=utf-8"
        )

@app.get("/volatilite")
def run_volatility():
    try:
        result = volatilite.run()
        return JSONResponse(
            content={"message": str(result)},
            media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Erreur dans la volatilité : {e}"},
            media_type="application/json; charset=utf-8"
        )

@app.get("/ouverture")
def run_ouverture():
    try:
        result = position_ouverture.run()
        return JSONResponse(
            content={"message": str(result)},
            media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Erreur dans l'analyse d'ouverture : {e}"},
            media_type="application/json; charset=utf-8"
        )

@app.get("/cashflow")
def run_cashflow_analysis():
    try:
        result = cashflow.run()
        return JSONResponse(
            content={"message": str(result)},
            media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Erreur dans l'analyse cash-flow : {e}"},
            media_type="application/json; charset=utf-8"
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
