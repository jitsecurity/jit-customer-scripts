import os

from src.shared.consts import JIT_DEFAULT_API_ENDPOINT


def get_jit_endpoint_base_url() -> str:
    return os.getenv('JIT_API_ENDPOINT', JIT_DEFAULT_API_ENDPOINT)
