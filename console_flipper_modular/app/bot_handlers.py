from __future__ import annotations

import html
import logging
from functools import wraps

from telegram import BotCommand, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from .constants import TARGETS
from .services.flipper_service import ConsoleFlipperService
from .utils.misc import compact_spaces, format_ts

logger = logging.getLogger("console_flipper.handlers")


def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else None
        service: ConsoleFlipperService = context.application.bot_data["service"]
        if not service.is_admin(user_id):
            await update.effective_message.reply_text("Ta komenda jest tylko dla admina.")
            return
        return await func(update, context)

    return wrapper


async def set_bot_commands(app: Application) -> None:
    commands = [
        BotCommand("status", "Status bota"),
        BotCommand("lastcheck", "Status ostatniego sprawdzenia"),
        BotCommand("forcecheck", "Natychmiastowy check ofert"),
        BotCommand("filters", "Pokaż filtry"),
        BotCommand("addfilter", "Dodaj pozytywny filtr"),
        BotCommand("removefilter", "Usuń pozytywny filtr"),
        BotCommand("blacklist", "Pokaż blacklistę"),
        BotCommand("addblacklist", "Dodaj blacklistę"),
        BotCommand("removeblacklist", "Usuń z blacklisty"),
        BotCommand("marketplaces", "Pokaż marketplace'y"),
        BotCommand("togglemarketplace", "Włącz/wyłącz marketplace"),
        BotCommand("maxprices", "Pokaż limity cen"),
        BotCommand("setmaxprice", "Ustaw limit ceny"),
        BotCommand("pause", "Pauza"),
        BotCommand("resume", "Wznów"),
        BotCommand("help", "Pomoc"),
    ]
    await app.bot.set_my_commands(commands)


@admin_only
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    runtime = service.runtime
    flags = await service.filters.marketplace_flags()
    max_prices = await service.filters.max_prices()
    last_run = await runtime.store.get_last_run()

    lines = [
        "📊 <b>Console Flipper — status</b>",
        f"Paused: <b>{'TAK' if runtime.paused else 'NIE'}</b>",
        f"Last start: <code>{format_ts(runtime.last_check_started_at)}</code>",
        f"Last finish: <code>{format_ts(runtime.last_check_finished_at)}</code>",
        f"Last error: <code>{html.escape(runtime.last_error or '-')}</code>",
        "",
        "🏪 <b>Marketplace</b>",
        *(f"• {k}: {'ON' if v else 'OFF'}" for k, v in flags.items()),
        "",
        "💸 <b>Max prices</b>",
        *(f"• {k}: {v} zł" for k, v in max_prices.items()),
    ]
    if last_run:
        lines.extend([
            "",
            "🧾 <b>Last DB run</b>",
            f"• status: {last_run['status']}",
            f"• found: {last_run['discovered_count']}",
            f"• posted: {last_run['posted_count']}",
        ])
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


@admin_only
async def cmd_lastcheck(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    await update.effective_message.reply_text(service.runtime.last_check_summary)


@admin_only
async def cmd_forcecheck(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    await update.effective_message.reply_text("Uruchamiam ręczny check…")
    result = await service.run_single_check(reason="manual_command")
    await update.effective_message.reply_text(
        f"Gotowe. Znaleziono: {result['discovered']}, opublikowano: {result['posted']}."
    )


@admin_only
async def cmd_filters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    required = await service.filters.required_keywords()
    blacklist = await service.filters.blacklist_keywords()
    req_lines = [f"• {html.escape(x)}" for x in required] or ["• (brak)"]
    bl_lines = [f"• {html.escape(x)}" for x in blacklist] or ["• (brak)"]
    text = "\n".join(["🔎 <b>Required keywords</b>", *req_lines, "", "⛔ <b>Blacklist keywords</b>", *bl_lines])
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@admin_only
async def cmd_addfilter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    value = compact_spaces(" ".join(context.args))
    if not value:
        await update.effective_message.reply_text("Użycie: /addfilter OLED")
        return
    data = await service.runtime.store.add_list_item("required_keywords", value)
    await update.effective_message.reply_text(f"Dodano filtr. Aktualnie: {', '.join(data) or '(brak)'}")


@admin_only
async def cmd_removefilter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    value = compact_spaces(" ".join(context.args))
    if not value:
        await update.effective_message.reply_text("Użycie: /removefilter OLED")
        return
    data = await service.runtime.store.remove_list_item("required_keywords", value)
    await update.effective_message.reply_text(f"Usunięto filtr. Aktualnie: {', '.join(data) or '(brak)'}")


@admin_only
async def cmd_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    blacklist = await service.filters.blacklist_keywords()
    await update.effective_message.reply_text(
        "⛔ Blacklista:\n" + ("\n".join(f"• {x}" for x in blacklist) if blacklist else "• (brak)")
    )


@admin_only
async def cmd_addblacklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    value = compact_spaces(" ".join(context.args))
    if not value:
        await update.effective_message.reply_text("Użycie: /addblacklist uszkodzony")
        return
    data = await service.runtime.store.add_list_item("blacklist_keywords", value)
    await update.effective_message.reply_text(f"Dodano. Aktualnie: {', '.join(data) or '(brak)'}")


@admin_only
async def cmd_removeblacklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    value = compact_spaces(" ".join(context.args))
    if not value:
        await update.effective_message.reply_text("Użycie: /removeblacklist uszkodzony")
        return
    data = await service.runtime.store.remove_list_item("blacklist_keywords", value)
    await update.effective_message.reply_text(f"Usunięto. Aktualnie: {', '.join(data) or '(brak)'}")


@admin_only
async def cmd_marketplaces(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    flags = await service.filters.marketplace_flags()
    await update.effective_message.reply_text(
        "🏪 Marketplace:\n" + "\n".join(f"• {k}: {'ON' if v else 'OFF'}" for k, v in flags.items())
    )


@admin_only
async def cmd_togglemarketplace(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    if len(context.args) != 2:
        await update.effective_message.reply_text("Użycie: /togglemarketplace olx on|off")
        return
    key = context.args[0].lower().strip()
    state = context.args[1].lower().strip()
    if state not in {"on", "off"}:
        await update.effective_message.reply_text("Drugi argument musi być on albo off.")
        return
    try:
        flags = await service.filters.set_marketplace_flag(key, state == "on")
    except KeyError:
        await update.effective_message.reply_text("Dostępne: vinted, olx, allegro")
        return
    await update.effective_message.reply_text(
        "Zapisano:\n" + "\n".join(f"• {k}: {'ON' if v else 'OFF'}" for k, v in flags.items())
    )


@admin_only
async def cmd_maxprices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    prices = await service.filters.max_prices()
    await update.effective_message.reply_text(
        "💸 Limity cen:\n" + "\n".join(f"• {k}: {v} zł" for k, v in prices.items())
    )


@admin_only
async def cmd_setmaxprice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    if len(context.args) != 2:
        await update.effective_message.reply_text(
            "Użycie: /setmaxprice ps5 2400\n"
            "Klucze: switch, steam_deck, ps5, xbox_series_x, xbox_series_s"
        )
        return
    key = context.args[0].lower().strip()
    if key not in {t.key for t in TARGETS}:
        await update.effective_message.reply_text(
            "Nieznana konsola. Klucze: switch, steam_deck, ps5, xbox_series_x, xbox_series_s"
        )
        return
    try:
        price = int(context.args[1])
    except ValueError:
        await update.effective_message.reply_text("Cena musi być liczbą.")
        return
    prices = await service.filters.set_max_price(key, price)
    await update.effective_message.reply_text(
        "Zapisano:\n" + "\n".join(f"• {k}: {v} zł" for k, v in prices.items())
    )


@admin_only
async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    service.runtime.paused = True
    await update.effective_message.reply_text("Bot został zatrzymany.")


@admin_only
async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: ConsoleFlipperService = context.application.bot_data["service"]
    service.runtime.paused = False
    await update.effective_message.reply_text("Bot został wznowiony.")


@admin_only
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = """
/status - pełny status
/lastcheck - wynik ostatniego checku
/forcecheck - natychmiastowe sprawdzenie
/filters - pokaż required + blacklist
/addfilter <fraza>
/removefilter <fraza>
/blacklist
/addblacklist <fraza>
/removeblacklist <fraza>
/marketplaces
/togglemarketplace <vinted|olx|allegro> <on|off>
/maxprices
/setmaxprice <switch|steam_deck|ps5|xbox_series_x|xbox_series_s> <cena>
/pause
/resume
/help
"""
    await update.effective_message.reply_text(text.strip())


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("Console Flipper działa. Komendy admina: /status /lastcheck /help")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Telegram handler error", exc_info=context.error)
    service: ConsoleFlipperService | None = context.application.bot_data.get("service")
    if service:
        service.runtime.last_error = str(context.error)
        if service.runtime.config.admin_ids:
            message = f"❌ Błąd handlera: <code>{html.escape(str(context.error)[:3500])}</code>"
            for admin_id in service.runtime.config.admin_ids:
                try:
                    await context.application.bot.send_message(admin_id, message, parse_mode=ParseMode.HTML)
                except Exception:
                    logger.exception("Failed to notify admin %s", admin_id)


def register_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("lastcheck", cmd_lastcheck))
    app.add_handler(CommandHandler("forcecheck", cmd_forcecheck))
    app.add_handler(CommandHandler("filters", cmd_filters))
    app.add_handler(CommandHandler("addfilter", cmd_addfilter))
    app.add_handler(CommandHandler("removefilter", cmd_removefilter))
    app.add_handler(CommandHandler("blacklist", cmd_blacklist))
    app.add_handler(CommandHandler("addblacklist", cmd_addblacklist))
    app.add_handler(CommandHandler("removeblacklist", cmd_removeblacklist))
    app.add_handler(CommandHandler("marketplaces", cmd_marketplaces))
    app.add_handler(CommandHandler("togglemarketplace", cmd_togglemarketplace))
    app.add_handler(CommandHandler("maxprices", cmd_maxprices))
    app.add_handler(CommandHandler("setmaxprice", cmd_setmaxprice))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_error_handler(error_handler)
