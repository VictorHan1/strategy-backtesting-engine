from dataHandler import DataHandler
from strategyManager import StrategyManager
from performanceAnalyzer import PerformanceAnalyzer
from reporter import Reporter
from concurrent.futures import ProcessPoolExecutor, as_completed


SMA_PERIODS = [100, 200]
LARGE_CAP_MIN_MARKET_CAP = 10_000_000_000  # 10 Billion
MAX_WORKERS = 4
STRATEGY_NAME = "RSI_SMA"
RSI_PERIOD = 10


def execute_backtest_thread(ticker, df, strategy_name, params):
    manager = StrategyManager(df, strategy_name, params)
    trades = manager.run_backtest()
    analyzer = PerformanceAnalyzer(trades)
    return ticker, analyzer.stats, trades


def load_large_cap_data():
    stock_data = DataHandler()
    return stock_data.load_filtered_data(min_market_cap=LARGE_CAP_MIN_MARKET_CAP)


def build_strategy_params(sma_period):
    return {
        "rsi_period": RSI_PERIOD,
        "sma_period": sma_period,
    }


def run_backtests_for_sma_period(data_dict, sma_period):
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
    data_dict = load_large_cap_data()

    all_results = {}
    print("[INFO] Starting backtests...")

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
