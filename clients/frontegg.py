import os
from typing import Optional

import requests
from dotenv import load_dotenv
from loguru import logger

from consts import FRONTEGG_DEFAULT_AUTH_URL

# Load environment variables from .env file. make sure it's before you import modules.
load_dotenv(".env")

FRONTEGG_AUTH_URL = os.getenv("FRONTEGG_AUTH_URL", FRONTEGG_DEFAULT_AUTH_URL)
JIT_CLIENT_SECRET = os.getenv("JIT_CLIENT_SECRET")
JIT_CLIENT_ID = os.getenv("JIT_CLIENT_ID")


def get_jwt_token() -> Optional[str]:
    payload = {
        "clientId": JIT_CLIENT_ID,
        "secret": JIT_CLIENT_SECRET
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.post(FRONTEGG_AUTH_URL, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json().get('accessToken')
    else:
        logger.error(f"Failed to retrieve JWT token. Status code: {response.status_code}")
        return None
