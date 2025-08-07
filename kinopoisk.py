import requests
from config import KINOPOISK_API_KEY

async def search_kinopoisk(title: str):
    url = f"https://api.kinopoisk.dev/v1.3/movie?name={title}"
    headers = {"X-API-KEY": KINOPOISK_API_KEY}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None