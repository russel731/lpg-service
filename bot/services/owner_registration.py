import httpx


BASE_URL = "http://backend:8000"


async def register_owner(payload: dict) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/owners/register",
                json=payload,
                timeout=10,
            )

        print("REGISTER OWNER RESPONSE:", response.status_code, response.text)

        return response.status_code == 200

    except Exception as e:
        print("REGISTER OWNER ERROR:", e)
        return False