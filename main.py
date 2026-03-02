from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.ocr_router import router as ocr_router
from routers.ocr_router2 import router as ocr_router_multi
from routers.chat_router import router as chat_router
import uvicorn


app = FastAPI(
    title="My API",
    description="UMT PROJECT 2026",
    version="1.0.0"
)

# ✅ CORS Middleware (required for Flutter / external access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include Routers
app.include_router(ocr_router)
app.include_router(ocr_router_multi)
app.include_router(chat_router)


@app.get("/")
async def root():
    return {"message": "Welcome to the UMT Project API!"}


if __name__ == "__main__":
    # Run on 0.0.0.0 so it works properly with ngrok and external devices
    uvicorn.run(app, host="127.0.0.1", port=8000)