from fastapi import FastAPI

app = FastAPI(title="JP Resin Precalificador")


@app.get("/health")
def health():
    return {"status": "ok"}
