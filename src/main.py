from app import app
from config.config import Settings
from config.logger import configure_logging, logger


def main() -> None:
    """Ejecuta el servidor local de Dash."""
    settings = Settings()
    configure_logging(settings.log_level)
    logger.info(
        "starting dash app",
        extra={
            "host": settings.app_host,
            "port": settings.app_port,
            "debug": settings.app_debug,
        },
    )
    app.run(host=settings.app_host, port=settings.app_port, debug=settings.app_debug)


if __name__ == "__main__":
    main()
