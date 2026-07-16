"""Entry point for running the RSI/SMA backtest demo.

The script loads filtered stock data, runs the configured SMA variants in
parallel, and sends the nested results to the reporter.
"""

from dataHandler import DataHandler
from strategyManager import StrategyManager
from performanceAnalyzer import PerformanceAnalyzer
from reporter import Reporter
from concurrent.futures import ProcessPoolExecutor, as_completed


# Backtest configuration for the demo run.
SMA_PERIODS = [100, 200]
LARGE_CAP_MIN_MARKET_CAP = 10_000_000_000  # 10 Billion
MAX_WORKERS = 4
STRATEGY_NAME = "RSI_SMA"
RSI_PERIOD = 10


def execute_backtest_thread(ticker, df, strategy_name, params):
    """Run a single ticker backtest.

    Args:
        ticker: Stock symbol used as the result key.
        df: Historical price data for the ticker.
        strategy_name: Strategy identifier passed to StrategyManager.
        params: Strategy parameters for this run.

    Returns:
        A tuple containing the ticker, summary statistics, and generated trades.
    """
    manager = StrategyManager(df, strategy_name, params)
    trades = manager.run_backtest()
    analyzer = PerformanceAnalyzer(trades)
    return ticker, analyzer.stats, trades


def load_large_cap_data():
    """Load stock data using the configured market-cap filter.

    Returns:
        A dictionary of historical price data keyed by ticker.
    """
    stock_data = DataHandler()
    return stock_data.load_filtered_data(min_market_cap=LARGE_CAP_MIN_MARKET_CAP)


def build_strategy_params(sma_period):
    """Build the RSI/SMA strategy parameters for one configuration.

    Args:
        sma_period: Simple moving average lookback period.

    Returns:
        A parameter dictionary passed to StrategyManager.
    """
    return {
        "rsi_period": RSI_PERIOD,
        "sma_period": sma_period,
    }


def run_backtests_for_sma_period(data_dict, sma_period):
    """Run all ticker backtests for a single SMA period.

    Args:
        data_dict: Historical price data keyed by ticker.
        sma_period: Simple moving average lookback period to test.

    Returns:
        Two dictionaries keyed by ticker: summary statistics and raw trades.
    """
    results = {}
    trades_dict = {}

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(
                execute_backtest_thread,
                ticker,
                df,
                STRATEGY_NAME,
                build_strategy_params(sma_period),
            )
            for ticker, df in data_dict.items()
        ]

        for future in as_completed(futures):
            ticker, stats, trades = future.result()
            results[ticker] = stats
            trades_dict[ticker] = trades

    return results, trades_dict


def main():
    """Run the full backtest workflow and display the final report."""
    data_dict = load_large_cap_data()

    all_results = {}
    print("[INFO] Starting backtests...")

    # Keep each SMA period separate so the reporter can compare configurations.
    for sma_period in SMA_PERIODS:
        print(f"\n[INFO] Running backtest for SMA period = {sma_period}")

        results, _ = run_backtests_for_sma_period(data_dict, sma_period)

        print(f"Completed {len(results)}/{len(data_dict)} stocks for SMA {sma_period}")

        all_results[sma_period] = results

    reporter = Reporter(all_results)
    reporter.print_summary()
    reporter.plot_interactive_dashboard()


if __name__ == "__main__":
    main()
