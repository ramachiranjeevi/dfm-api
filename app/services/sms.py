"""TextLocal SMS service."""
import httpx

from app.config import settings

TEXTLOCAL_URL = "https://api.textlocal.in/send/"


async def send_sms(mobile_no: str, message: str) -> dict:
    """
    Send an SMS via TextLocal API.
    Returns the API response dict.
    """
    params = {
        "apikey": settings.TEXTLOCAL_API_KEY,
        "numbers": mobile_no,
        "message": message,
        "sender": settings.TEXTLOCAL_SENDER,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(TEXTLOCAL_URL, params=params)
            return response.json()
        except Exception as exc:
            return {"status": "error", "errors": [str(exc)]}
