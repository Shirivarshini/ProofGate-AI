from fastapi import FastAPI

app = FastAPI(title="ProofGate AI", version="0.1.0-stage0")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": "ProofGate AI",
        "message": "It works! My backend server is live."
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}