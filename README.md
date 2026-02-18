# Strategy Backtesting Engine

A modular Python-based backtesting engine for evaluating systematic trading strategies across multiple equities.

The system is built around a SQLite data layer, a strategy abstraction framework, and a performance analytics module.

---

## Project Structure

### Data Layer

- `dataHandler.py` – Handles all runtime interactions with the SQLite database
- `databuilder1.py`, `download_history.py`, `clean_database.py` – One-time data pipeline scripts used to construct and clean the database
- `get_finviz_tickers.py` – Stock universe generation
- `getipo_date.py` – IPO enrichment utility

Note: Database files are excluded from the repository.

---

### Strategy Engine

- `strategy.py` – Base strategy abstraction
- `rsi_sma_strategy.py` – RSI + SMA implementation
- `indicators.py` – Vectorized technical indicator calculations
- `strategyManager.py` – Strategy orchestration and execution logic

---

### Performance & Reporting

- `performanceAnalyzer.py` – Trade and portfolio performance metrics
- `reporter.py` – Results presentation
- `main.py` – Execution entry point

---

## Features

- Modular strategy abstraction
- Vectorized indicator computation
- Multi-stock backtesting
- SQLite-based storage layer
- Separated data, execution, and analytics layers

---

## Running the Backtest

The database must exist locally.

Once data has been prepared: