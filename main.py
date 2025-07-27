from fastapi import FastAPI
import analyseur
import os

app = FastAPI()

@app.get("/")
def run_analysis():
    try:
        result = analyseur.run()
        return {"message": str(result)}
    except Exception as e:
        return {"error": str(e)}
