from fastapi import FastAPI
from fastapi.responses import JSONResponse
import analyseur
from volatilite_cashflow import analyse_volatilite_cashflow
import os
import uvicorn

app = FastAPI()

# Endpoint principal (analyse standard)
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

# Nouveau endpoint : détection de volatilité + potentiel de cash-flow
@app.get("/cashflow")
def run_cashflow():
    try:
        result = analyse_volatilite_cashflow()
        return JSONResponse(
            content={"message": str(result)},
            media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Erreur dans l’analyse cashflow : {e}"},
            media_type="application/json; charset=utf-8"
        )

# Lancement local (facultatif pour Render)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
