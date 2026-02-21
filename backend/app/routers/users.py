from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

user_languages = {}


@router.post("/set-language")
async def set_language(telegram_id: int, language: str):
    user_languages[telegram_id] = language
    print("LANG SET:", telegram_id, language)
    return {"status": "ok"}


@router.get("/get-language")
async def get_language(telegram_id: int):
    return {"language": user_languages.get(telegram_id, "kz")}