from fastapi import FastAPI
app=FastAPI(title="Multi-Agent Customer Support API",
            version="0.1.0",
            )
@app.get("/health")
def health_check():
    return {"status":"healthy"}
