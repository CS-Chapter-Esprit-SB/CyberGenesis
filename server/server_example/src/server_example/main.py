def health_check() -> dict[str, str]:
    return {"service": "server-example", "status": "ok"}


def main() -> None:
    print(health_check())
