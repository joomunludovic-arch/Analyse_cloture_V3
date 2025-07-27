from fastapi import FastAPI
from fastapi.responses import JSONResponse
import analyseur
import volatilite_analyseur  # <== assure-toi que ce fichier existe
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
def analyse_volatilite():
    try:
        result = volatilite_analyseur.run()
        return JSONResponse(
            content={"message": str(result)},
            media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Erreur dans l'analyse volatilité : {e}"},
            media_type="application/json; charset=utf-8"
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
