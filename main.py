from dataHandler import DataHandler
from strategyManager import StrategyManager
from performanceAnalyzer import PerformanceAnalyzer
from reporter import Reporter
from concurrent.futures import ProcessPoolExecutor, as_completed
SMA_PERIODS = [100, 200]
def execute_backtest_thread	(ticker, df, strategy_name, params):
    manager = StrategyManager(df, strategy_name, params)
    trades = manager.run_backtest()
    analyzer = PerformanceAnalyzer(trades)
    return ticker, analyzer.stats, trades


def main():
    stock_data = DataHandler()

    # Define 10 Billion as the threshold for Large Cap
    MIN_MCAP = 10_000_000_000
    data_dict = stock_data.load_filtered_data(min_market_cap=MIN_MCAP)
    #data_dict = stock_data.load_data()

    all_results = {} 
    print("[INFO] Starting backtests...")

    for sma_period in SMA_PERIODS:
        print(f"\n[INFO] Running backtest for SMA period = {sma_period}")

        results = {}
        trades_dict = {}

        with ProcessPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(
                    execute_backtest_thread,
                    ticker,
                    df,
                    "RSI_SMA",
                    {
                        "rsi_period": 10,
                        "sma_period": sma_period
                    }
                )
                for ticker, df in data_dict.items()
            ]

            for future in as_completed(futures):
                ticker, stats, trades = future.result()
                results[ticker] = stats
                trades_dict[ticker] = trades
                print(f"[DONE] {ticker} done")

        print(f"[✅] Backtest completed for SMA {sma_period}")
        print("Example (DIS):", results.get("DIS"))

        all_results[sma_period] = results

    reporter = Reporter(all_results)
    reporter.print_summary()
    reporter.plot_interactive_dashboard()


if __name__ == "__main__":
    main()