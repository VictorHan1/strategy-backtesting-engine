# Hybrid Strategy Backtesting Engine

A modular Python backtesting engine for evaluating systematic trading strategies across multiple equities.

The project combines vectorized indicator calculation with Numba-compiled execution logic and multiprocessing for running strategy simulations across a basket of stocks.

## Project Structure

### Data Layer

- `dataHandler.py` - Loads price and metadata from the included SQLite sample database.
- `sample_stocks.db` - Lightweight demo database with 30 liquid equities, ready for immediate execution.
- `get_finviz_tickers.py` - Optional utility for building a Finviz-based stock universe.
- `getipo_date.py` - Optional utility for checking whether a ticker has enough historical depth.
- `download_history.py` - Optional utility for downloading historical OHLCV data into SQLite.

Production-scale databases and generated CSV/cache files are excluded from the repository.

### Strategy Engine

- `strategy.py` - Base strategy abstraction.
- `rsi_sma_strategy.py` - RSI + SMA strategy implementation using Numba for state-dependent trade execution.
- `indicators.py` - Technical indicator calculations.
- `strategyManager.py` - Orchestration layer connecting data to strategy logic.

### Performance & Reporting

- `performanceAnalyzer.py` - Trade-level performance statistics.
- `reporter.py` - Visualization and reporting layer.
- `main.py` - Entry point for running the sample backtest with multiprocessing.

## Key Features

- Hybrid execution model: vectorized indicators with JIT-compiled trade logic.
- Support for state-dependent strategy behavior, including stop logic and partial exits.
- Parallel execution across multiple tickers.
- Included sample database for a zero-configuration demo run.
- Clear separation between data loading, strategy execution, and reporting.

## Installation

Python 3.10+ is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Backtest

The engine is preconfigured to run on the included `sample_stocks.db` file.

```bash
python3 main.py
```

## Optional Data Utilities

The repository includes utility scripts for rebuilding or validating data sources, but they are not required for the demo run:

- `get_finviz_tickers.py` creates Finviz screener CSV outputs.
- `download_history.py` downloads historical OHLCV prices into SQLite.
- `getipo_date.py` checks whether a ticker has approximately 10 years of Yahoo Finance history.

## Future Improvements

- Parameter optimization.
- Portfolio-level risk modeling and correlation analysis.
- Cleaner end-to-end data rebuild pipeline.
