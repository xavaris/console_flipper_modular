# Console Flipper

Modularny Telegram bot do monitorowania lokalnych ofert konsol z:
- Vinted.pl
- OLX.pl
- Allegro.pl (`Kup teraz` + lokalnie / odbiór osobisty)

## Struktura

```text
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── constants.py
│   ├── logging_setup.py
│   ├── bot_handlers.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── olx.py
│   │   ├── allegro_lokalnie.py
│   │   └── vinted.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── flipper_service.py
│   │   ├── market_baseline_service.py
│   │   └── translator_service.py
│   └── utils/
│       ├── __init__.py
│       ├── misc.py
│       ├── filters.py
│       ├── formatting.py
│       └── console_parser.py
├── data/
├── requirements.txt
├── Dockerfile
├── .gitignore
├── .env.example
└── README.md
```

## Funkcje

- webhook Telegram + FastAPI + Uvicorn
- background scraping loop
- SQLite deduplikacja
- admin komendy
- positive filters + blacklist
- max ceny per konsola
- on/off dla każdego marketplace
- publikacja `photo + caption`
- healthcheck pod Railway

## Komendy admina

- `/status`
- `/lastcheck`
- `/forcecheck`
- `/filters`
- `/addfilter OLED`
- `/removefilter OLED`
- `/blacklist`
- `/addblacklist uszkodzony`
- `/removeblacklist uszkodzony`
- `/marketplaces`
- `/togglemarketplace olx on`
- `/maxprices`
- `/setmaxprice ps5 2400`
- `/pause`
- `/resume`
- `/help`

## Railway

1. Wrzuć repo na GitHub.
2. Podłącz repo do Railway.
3. Ustaw zmienne z `.env.example`.
4. Upewnij się, że domena z Railway jest wpisana w `WEBHOOK_BASE_URL`.
5. Deploy.

## Lokalnie

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
python -m app.main
```

## Ważna uwaga

Selektory marketplace'ów potrafią się zmieniać. Architektura i logika deploymentu są gotowe, ale przy realnym ruchu może być potrzebne dostrojenie selektorów pod aktualny frontend Vinted / OLX / Allegro.
