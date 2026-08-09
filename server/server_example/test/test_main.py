from server.server_example.src.server_example.main import health_check


def test_health_check() -> None:
    assert health_check() == {"service": "server-example", "status": "ok"}
