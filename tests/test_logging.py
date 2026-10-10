import logging

from vie_bot.__main__ import _setup_logging


def test_httpx_urls_not_logged_at_info():
    _setup_logging()
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
