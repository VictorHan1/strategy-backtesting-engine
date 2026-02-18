from rsi_sma_strategy import RsiSmaStrategy
import pandas as pd

class StrategyManager:
    """
    Manages and executes a vectorized backtest for a chosen strategy over a DataFrame.
    """
    def __init__(self, data_frame: pd.DataFrame, strategy_type: str, params: dict | None = None):
        """
        Initialize the StrategyManager with data and strategy identifier.

        :param data_frame: pandas DataFrame with price data and indicators
        :param strategy_type: string key of the strategy to run (e.g. "RSI_SMA")
        """
        self.data_frame = data_frame
        self.strategy_type = strategy_type
        StrategyClass = RsiSmaStrategy # Replace with a mapping of strategy types to classes in future
        self.params = params or {}
        self.strategy = StrategyClass(data_frame, self.params)

    def run_backtest(self) -> list[dict]:
        """
        Perform a vectorized backtest using entry and exit signals provided by the strategy.

        :return: DataFrame of trades, including entry_date, entry_price, exit_dates, exit_prices, take_profit, return_pct, etc.
        """
        return self.strategy.run_backtest()
