from vie_bot.resilience import should_alert


def test_alert_cadence():
    assert [n for n in range(1, 25) if should_alert(n)] == [1, 10, 20]
