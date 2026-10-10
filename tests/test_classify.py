import pytest

from vie_bot.classify import classify_offer


@pytest.mark.parametrize(
    ("title", "country", "expected"),
    [
        ("DevOps Engineer", "US", "it"),
        ("DevOps Engineer", "BE", None),
        ("Business Developer", "US", None),
        ("Ingénieur HSE", "US", None),
        ("Talent Acquisition Specialist", "BE", "hr"),
        ("Comptable Junior", "US", None),
        ("Analyste CyberSOC", "CA", "it"),
    ],
)
def test_classify(title, country, expected):
    assert classify_offer({"missionTitle": title, "countryId": country}) == expected
