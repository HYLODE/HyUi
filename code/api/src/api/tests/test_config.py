from api.config import Settings


def test_settings():
    """
    Test settings can be initialised with no environment variables for mock
    testing.
    """
    Settings()
