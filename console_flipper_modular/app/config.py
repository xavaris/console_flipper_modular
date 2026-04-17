from __future__ import annotations

import os
from dataclasses import dataclass

from .utils.misc import csv_env, env_bool, env_int


@dataclass(slots=True)
class AppConfig:
    bot_token: str
    webhook_base_url: str
    webhook_secret: str
    port: int
    admin_ids: set[int]
    target_chat_id: str
    sqlite_path: str
    scrape_interval_seconds: int
    request_timeout_seconds: int
    max_posts_per_cycle: int
    enable_vinted: bool
    enable_olx: bool
    enable_allegro: bool
    headless: bool
    locale: str
    default_required_keywords: list[str]
    default_blacklist_keywords: list[str]
    user_agent: str
    log_level: str

    @property
    def webhook_path(self) -> str:
        return f"/telegram/{self.webhook_secret}"

    @property
    def health_path(self) -> str:
        return "/healthz"

    @property
    def webhook_url(self) -> str:
        return f"{self.webhook_base_url.rstrip('/')}{self.webhook_path}"

    @classmethod
    def from_env(cls) -> "AppConfig":
        token = os.getenv("BOT_TOKEN", "").strip()
        base_url = os.getenv("WEBHOOK_BASE_URL", "").strip()
        chat_id = os.getenv("TARGET_CHAT_ID", "").strip()
        secret = os.getenv("WEBHOOK_SECRET", "").strip() or os.getenv("TELEGRAM_SECRET_TOKEN", "").strip()

        if not token:
            raise RuntimeError("Missing BOT_TOKEN")
        if not base_url:
            raise RuntimeError("Missing WEBHOOK_BASE_URL")
        if not chat_id:
            raise RuntimeError("Missing TARGET_CHAT_ID")
        if not secret:
            raise RuntimeError("Missing WEBHOOK_SECRET or TELEGRAM_SECRET_TOKEN")

        admin_ids_raw = csv_env(os.getenv("ADMIN_IDS"))
        admin_ids = {int(x) for x in admin_ids_raw} if admin_ids_raw else set()

        return cls(
            bot_token=token,
            webhook_base_url=base_url,
            webhook_secret=secret,
            port=env_int(os.getenv("PORT"), 8080),
            admin_ids=admin_ids,
            target_chat_id=chat_id,
            sqlite_path=os.getenv("SQLITE_PATH", "data/console_flipper.db"),
            scrape_interval_seconds=env_int(os.getenv("SCRAPE_INTERVAL_SECONDS"), 180),
            request_timeout_seconds=env_int(os.getenv("REQUEST_TIMEOUT_SECONDS"), 30),
            max_posts_per_cycle=env_int(os.getenv("MAX_POSTS_PER_CYCLE"), 20),
            enable_vinted=env_bool(os.getenv("ENABLE_VINTED"), True),
            enable_olx=env_bool(os.getenv("ENABLE_OLX"), True),
            enable_allegro=env_bool(os.getenv("ENABLE_ALLEGRO"), True),
            headless=env_bool(os.getenv("PLAYWRIGHT_HEADLESS"), True),
            locale=os.getenv("BROWSER_LOCALE", "pl-PL"),
            default_required_keywords=csv_env(os.getenv("REQUIRED_KEYWORDS")),
            default_blacklist_keywords=csv_env(
                os.getenv("BLACKLIST_KEYWORDS"),
                "uszkodzony,do naprawy,na części,nie działa",
            ),
            user_agent=os.getenv(
                "BROWSER_USER_AGENT",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
