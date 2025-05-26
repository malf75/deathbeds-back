import os
import uvicorn
from setup.settings import app
from fastapi.responses import RedirectResponse
from database.db import engine
from sqlmodel import SQLModel, Session
from auth.auth import router

app.include_router(router)
SQLModel.metadata.create_all(engine)

@app.get("/")
def redirect_index():
    return RedirectResponse("/docs")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)