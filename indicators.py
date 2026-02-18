import pandas as pd
import talib

class Indicators:
    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 10) -> pd.Series:
        """
        Calculates RSI (Relative Strength Index) and returns it as a Series.

        :param series: Series of price data (e.g., closing prices).
        :param period: RSI calculation period.
        :return: RSI values as a Series.
        """
        return talib.RSI(series, timeperiod=period)

    @staticmethod
    def add_rsi(dataFrame: pd.DataFrame, period: int = 10, column: str = 'Close') -> pd.DataFrame:
        """
        Adds RSI to the DataFrame using the specified column.

        :param dataFrame: DataFrame containing price data.
        :param period: RSI calculation period.
        :param column: Column used for RSI calculation.
        :return: DataFrame with RSI column added.
        """
        dataFrame = dataFrame.copy()
        if isinstance(dataFrame.columns, pd.MultiIndex):
            dataFrame.columns = dataFrame.columns.droplevel(1)

        rsi_values = Indicators.calculate_rsi(dataFrame[column], period)
        dataFrame[f'RSI_{period}'] = rsi_values
        return dataFrame

    @staticmethod
    def calculate_sma(series: pd.Series, period: int = 200) -> pd.Series:
        """
        Calculates Simple Moving Average (SMA) and returns it as a Series.

        :param series: Series of price data.
        :param period: SMA calculation period.
        :return: SMA values as a Series.
        """
        return talib.SMA(series, timeperiod=period)

    @staticmethod
    def add_sma(dataFrame: pd.DataFrame, period: int = 200, column: str = 'Close') -> pd.DataFrame:
        """
        Adds SMA to the DataFrame using the specified column.

        :param dataFrame: DataFrame containing price data.
        :param period: SMA calculation period.
        :param column: Column used for SMA calculation.
        :return: DataFrame with SMA column added.
        """
        dataFrame = dataFrame.copy()
        if isinstance(dataFrame.columns, pd.MultiIndex):
            dataFrame.columns = dataFrame.columns.droplevel(1)

        sma_values = Indicators.calculate_sma(dataFrame[column], period)
        dataFrame[f'SMA_{period}'] = sma_values
        return dataFrame

