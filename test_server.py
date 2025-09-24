#!/usr/bin/env python3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HRM Test API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test basic routes first
@app.get("/")
def read_root():
    return {"message": "HRM System API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Add routers one by one
try:
    from app.routers import auth
    app.include_router(auth.router)
    print("Auth router added")
except Exception as e:
    print(f"Auth router failed: {e}")

try:
    from app.routers import reports
    app.include_router(reports.router)
    print("Reports router added")
except Exception as e:
    print(f"Reports router failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)