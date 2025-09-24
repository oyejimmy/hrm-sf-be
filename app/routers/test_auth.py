from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
def test_login():
    return {"message": "Test login endpoint"}

@router.get("/me")
def test_me():
    return {"message": "Test me endpoint"}