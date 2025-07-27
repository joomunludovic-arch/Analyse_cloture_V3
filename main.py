from fastapi import FastAPI
import analyseur
import os

app = FastAPI()

@app.get("/")
def run_analysis():
    result = analyseur.run()
    return {"message": result}
