"""Décide quand alerter Discord en cas d'échecs répétés du check cycle."""

ALERT_EVERY = 10  # ~10 min à intervalle 60s
# ponytail: cadence fixe, pas de backoff exponentiel — upgrade si trop de bruit


def should_alert(consecutive_failures: int) -> bool:
    """Alerte au 1er échec, puis tous les ALERT_EVERY échecs consécutifs."""
    return consecutive_failures == 1 or consecutive_failures % ALERT_EVERY == 0


def demo() -> None:
    assert should_alert(1) is True
    assert should_alert(2) is False
    assert should_alert(9) is False
    assert should_alert(10) is True
    assert should_alert(11) is False
    assert should_alert(20) is True
    print("resilience: OK")


if __name__ == "__main__":
    demo()
