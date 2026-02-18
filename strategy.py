import pandas as pd
from abc import ABC, abstractmethod

class Strategy(ABC):
    def __init__(self, dataFrame: pd.DataFrame, params: dict | None = None):
        """
        Initializes the strategy with the given DataFrame.
        :param dataFrame: A pandas DataFrame containing the price data with indicators.
        """
        self.dataFrame = dataFrame
        self.inPosition = False
        self.params = params or {} 

    @abstractmethod
    def generate_entry_signals(self) -> pd.Series:
        pass

    @abstractmethod
    def generate_exit_signals(self) -> pd.Series:
        pass
    
    @abstractmethod
    def run_backtest(self) -> pd.DataFrame:
        pass

    def generate_signals(self) -> pd.DataFrame:
        df = self.dataFrame.copy()
        df['entry_signal'] = self.generate_entry_signals()
        df['exit_signal']  = self.generate_exit_signals()
        return df
