# Hybrid Strategy Backtesting Engine

A modular Python-based backtesting engine for evaluating systematic trading strategies across multiple equities.

The system combines vectorized indicator computation with Numba-optimized execution logic and parallel processing to support scalable simulations.

---

## Project Structure

### Data Layer (ETL & Storage)

- `dataHandler.py` – Handles runtime interaction with the SQLite database. Configured to load from `sample_stocks.db` by default.
- `sample_stocks.db` – Lightweight sample database (30 liquid equities) for immediate execution.
- `download_history.py` – Historical data download pipeline.
- `clean_database.py` – Data cleaning and deduplication utilities.
- `databuilder1.py` – Database construction pipeline.
- `get_finviz_tickers.py` – Stock universe construction.
- `getipo_date.py` – IPO and historical depth validation utility.

*Note: Production-scale databases are excluded from the repository.*

---

### Strategy Engine

- `strategy.py` – Base strategy abstraction.
- `rsi_sma_strategy.py` – RSI + SMA implementation using **Numba (@njit)** for efficient state-dependent execution.
- `indicators.py` – Vectorized technical indicator calculations.
- `strategyManager.py` – Orchestration layer connecting data to strategy logic.

---

### Performance & Reporting

- `performanceAnalyzer.py` – Trade-level and portfolio-level metrics (Win Rate, Expectancy, Risk-Reward).
- `reporter.py` – Visualization layer for performance inspection.
- `main.py` – Entry point utilizing `ProcessPoolExecutor` for parallel backtesting.

---

## Key Features

- Hybrid Execution Model: Vectorized indicators combined with JIT-compiled trade logic.
- Support for state-dependent strategies: (e.g., trailing stops, partial exits).
- Parallel execution: Scalable backtesting across multiple tickers using multiprocessing.
- Modular Architecture: Clear separation between Data, Execution, and Analytics layers.
- Zero-Configuration: Includes a ready-to-run sample database.

---

## Design Philosophy

The system follows a strict **Separation of Concerns**:

- Data preparation is decoupled from strategy execution.
- Strategy logic is isolated from performance analytics.
- Analytics operates on trade logs without influencing execution.

---

## Future Improvements

- Parameter optimization (Grid Search / evolutionary approaches).
- Portfolio-level risk modeling and correlation analysis.
- Optional live execution bridge (IBKR/Alpaca API integration).
## Installation & Usage

### Requirements

- Python 3.10+
- Dependencies: `pandas`, `numpy`, `matplotlib`, `numba`, `TA-Lib` (Optional for data fetching: `yfinance`, `finvizfinance`)

### Run Backtest

The engine is pre-configured to run on the included sample data:

```bash
python main.py