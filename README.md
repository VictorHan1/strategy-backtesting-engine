# Hybrid Strategy Backtesting Engine

A modular Python-based backtesting engine for evaluating systematic trading strategies across multiple equities.

The system combines vectorized indicator computation with Numba-optimized execution logic and parallel processing for scalable simulations.

---

## Project Structure

### Data Layer (ETL & Storage)

- `dataHandler.py` – Handles runtime interaction with the SQLite database.
- `download_history.py` – Batch script for downloading historical market data.
- `clean_database.py` – Data cleaning and deduplication utilities.
- `databuilder1.py` – Database construction pipeline.
- `get_finviz_tickers.py` – Stock universe construction.
- `getipo_date.py` – IPO and historical depth validation utility.

*Note: Database files are excluded from the repository.*

---

### Strategy Engine

- `strategy.py` – Base strategy abstraction.
- `rsi_sma_strategy.py` – RSI + SMA implementation using Numba (`@njit`) for efficient state-dependent execution.
- `indicators.py` – Vectorized technical indicator calculations.
- `strategyManager.py` – Orchestration layer connecting data to strategy logic.

---

### Performance & Reporting

- `performanceAnalyzer.py` – Trade-level and portfolio-level metrics (Win Rate, Expectancy, Risk-Reward).
- `reporter.py` – Visualization layer for performance inspection.
- `main.py` – Entry point utilizing `ProcessPoolExecutor` for parallel backtesting.

---

## Key Features

- Hybrid execution model (Vectorized indicators + JIT-compiled trade logic)
- Support for state-dependent strategies (e.g., trailing stops, partial exits)
- Parallel processing across multiple tickers
- Modular and extensible architecture
- SQLite-based local storage

---
## Design Philosophy

The system follows a strict **Separation of Concerns**:

- **Data preparation** is decoupled from strategy execution.
- **Strategy logic** is isolated from performance analytics.
- **Analytics** operates on trade logs without influencing execution.

This structure allows future extension with additional strategies, optimization layers, or risk models.

---

## Future Improvements

- Parameter optimization (Grid Search / evolutionary approaches)
- Portfolio-level risk modeling
- Configuration-driven strategy definitions
- Optional live execution bridge

## Installation & Usage

### Requirements

- Python 3.10+
- Local SQLite database (`stocks.db`) built using the provided data scripts

### Run Backtest

```bash
python main.py

