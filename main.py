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
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # par défaut 10000
    uvicorn.run(app, host="0.0.0.0", port=port)
