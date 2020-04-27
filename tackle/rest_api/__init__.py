from tackle import rest_api


def get_path() -> str:
    """Get the file path to the rest_api module."""
    return getattr(rest_api, '__path__')[0]
