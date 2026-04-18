# Console Flipper Bot

Telegram bot do wyszukiwania okazji na konsole z:
- Allegro Lokalnie
- OLX
- Vinted

Monitorowane konsole:
- Xbox Series X
- Xbox Series S
- Nintendo Switch
- Nintendo Switch 2
- PlayStation 5
- Steam Deck

## Funkcje
- async scraping przez Playwright
- scheduler przez APScheduler
- deduplikacja ofert w SQLite
- liczenie median cen i score okazji
- filtrowanie akcesoriów, gier, pudełek i części
- publikacja na Telegram z miniaturką, ceną i linkiem
- konfiguracja przez `.env`
- gotowy Dockerfile i Railway config

## Uruchomienie lokalne

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
python -m app.main
```

## Komendy Telegram
- `/start`
- `/health`
- `/scan_now`

## Uwagi
Selektory DOM na marketplace'ach potrafią się zmieniać, więc po wdrożeniu warto zrobić test live i ewentualnie podstroić scrapery.


## Uwaga po aktualizacji
Usuń stary plik `offers.db` albo wyczyść tabelę `market_baselines`, jeśli wcześniej bot przepuszczał błędne oferty.
