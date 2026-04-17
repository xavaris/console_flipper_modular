from __future__ import annotations

import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from playwright.async_api import Browser, BrowserContext, async_playwright
from telegram import Update
from telegram.ext import Application

from .bot_handlers import register_handlers, set_bot_commands
from .config import AppConfig
from .db import StateStore
from .logging_setup import setup_logging
from .services.flipper_service import ConsoleFlipperService
from .utils.filters import FilterEngine

logger = logging.getLogger("console_flipper.main")


@dataclass(slots=True)
class RuntimeState:
    config: AppConfig
    store: StateStore
    playwright: object | None = None
    browser: Browser | None = None
    browser_context: BrowserContext | None = None
    scrape_task: asyncio.Task | None = None
    check_lock: asyncio.Lock = asyncio.Lock()
    paused: bool = False
    last_check_started_at: float | None = None
    last_check_finished_at: float | None = None
    last_check_summary: str = "Jeszcze nie uruchomiono sprawdzenia."
    last_error: str | None = None

    async def init_browser(self) -> None:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.config.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        self.browser_context = await self.browser.new_context(
            locale=self.config.locale,
            user_agent=self.config.user_agent,
            viewport={"width": 1440, "height": 2200},
        )

    async def close_browser(self) -> None:
        if self.browser_context:
            await self.browser_context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


def create_application() -> FastAPI:
    config = AppConfig.from_env()
    setup_logging(config.log_level)

    store = StateStore(config.sqlite_path)
    runtime = RuntimeState(config=config, store=store)
    ptb_app = Application.builder().token(config.bot_token).updater(None).build()
    filters = FilterEngine(store, config)
    service = ConsoleFlipperService(ptb_app, runtime, filters)
    ptb_app.bot_data["service"] = service
    register_handlers(ptb_app)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info("Starting Console Flipper")
        await runtime.init_browser()
        await ptb_app.initialize()
        await ptb_app.start()
        await set_bot_commands(ptb_app)
        await ptb_app.bot.set_webhook(
            url=config.webhook_url,
            allowed_updates=Update.ALL_TYPES,
            secret_token=config.webhook_secret,
            drop_pending_updates=False,
        )
        runtime.scrape_task = asyncio.create_task(service.start_loop(), name="scrape-loop")
        try:
            yield
        finally:
            logger.info("Stopping Console Flipper")
            if runtime.scrape_task:
                runtime.scrape_task.cancel()
                try:
                    await runtime.scrape_task
                except asyncio.CancelledError:
                    pass
            try:
                await ptb_app.bot.delete_webhook(drop_pending_updates=False)
            except Exception:
                logger.exception("delete_webhook failed")
            await ptb_app.stop()
            await ptb_app.shutdown()
            await runtime.close_browser()
            await store.close()

    app = FastAPI(title="Console Flipper", lifespan=lifespan)
    app.state.config = config
    app.state.runtime = runtime
    app.state.ptb_app = ptb_app
    app.state.service = service

    @app.get("/")
    async def root() -> JSONResponse:
        return JSONResponse(
            {
                "name": "Console Flipper",
                "ok": True,
                "webhook_path": config.webhook_path,
                "health": config.health_path,
            }
        )

    @app.get(config.health_path)
    async def health() -> PlainTextResponse:
        return PlainTextResponse("ok")

    @app.post(config.webhook_path)
    async def telegram_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: str | None = Header(default=None),
    ) -> Response:
        if x_telegram_bot_api_secret_token != config.webhook_secret:
            raise HTTPException(status_code=403, detail="Forbidden")
        data = await request.json()
        await ptb_app.update_queue.put(Update.de_json(data=data, bot=ptb_app.bot))
        return Response(status_code=200)

    @app.post("/internal/force-check")
    async def internal_force_check(x_admin_secret: str | None = Header(default=None)) -> JSONResponse:
        if x_admin_secret != config.webhook_secret:
            raise HTTPException(status_code=403, detail="Forbidden")
        result = await service.run_single_check(reason="internal_endpoint")
        return JSONResponse(result)

    return app


app = create_application()


def main() -> None:
    import uvicorn

    config = app.state.config
    stop_signals = None
    if hasattr(signal, "SIGINT") and hasattr(signal, "SIGTERM"):
        stop_signals = [signal.SIGINT, signal.SIGTERM]

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.port,
        reload=False,
        log_level=config.log_level.lower(),
    )


if __name__ == "__main__":
    main()
