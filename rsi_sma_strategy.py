from strategy import Strategy
from indicators import Indicators
from numba import njit
import numpy as np
import pandas as pd 

@njit    
def update_prices(i, entry_price, price, partial_exit_price, update_partial, update_exit, entry_prices, partial_exit_prices, exit_prices):
    entry_prices[i] = entry_price
    if update_partial:
        partial_exit_prices[i] = partial_exit_price
    if update_exit:
        exit_prices[i] = price
            
@njit
def execute_backtest(open_price, close, low, entry_signal, partial_exit_signal, exit_signal):
    in_position = False
    partial_is_done = False
    entry_price = 0.0
    stop_loss_price = 0.0
    partial_exit_price = 0.0

    # entry and exit signals
    entry_flags = np.zeros_like(close, dtype=np.bool_)
    partial_exit_flags = np.zeros_like(close, dtype=np.bool_)
    exit_flags = np.zeros_like(close, dtype=np.bool_)

    # price tracking
    entry_prices = np.full_like(close, np.nan, dtype=np.float64)
    partial_exit_prices = np.full_like(close, np.nan, dtype=np.float64)
    exit_prices = np.full_like(close, np.nan, dtype=np.float64)

    for i in range(len(close)):
        
        if entry_signal[i] and not in_position: # Entering a postion 
            in_position = True
            entry_price = open_price[i]

            stop_loss_price = low[i - 1] if i > 0 else low[i]
            entry_flags[i] = True
            partial_is_done = False
            update_prices(i, open_price[i], np.nan, partial_exit_price, 0, 0, entry_prices, partial_exit_prices, exit_prices)

            if low[i] < stop_loss_price: # stop loss hit on entry day 
                exit_flags[i] = True
                in_position = False
                update_prices(i, entry_price, stop_loss_price, partial_exit_price,int(partial_is_done), 1, entry_prices, partial_exit_prices, exit_prices) 

        elif in_position:
            if low[i] < stop_loss_price: # stop loss or normal exit (take profit)
                exit_flags[i] = True
                in_position = False
                update_prices(i, entry_price, stop_loss_price, partial_exit_price, int(partial_is_done), 1, entry_prices, partial_exit_prices, exit_prices)
                
            elif exit_signal[i]:
                exit_flags[i] = True
                in_position = False
                update_prices(i, entry_price, close[i], partial_exit_price, int(partial_is_done), 1, entry_prices, partial_exit_prices, exit_prices)
                
            elif partial_exit_signal[i] and not partial_is_done:
                partial_exit_flags[i] = True
                partial_is_done = True
                stop_loss_price = entry_price
                partial_exit_price = close[i]
                update_prices(i, entry_price, close[i], partial_exit_price, int(partial_is_done), 0, entry_prices, partial_exit_prices, exit_prices)
                
            else:
                update_prices(i, entry_price, close[i], partial_exit_price, int(partial_is_done), 0, entry_prices, partial_exit_prices, exit_prices)

    return entry_flags, partial_exit_flags, exit_flags, entry_prices, partial_exit_prices, exit_prices

class RsiSmaStrategy(Strategy):
    def __init__(self, dataFrame: pd.DataFrame, params: dict | None = None):
        super().__init__(dataFrame)

        self.params = params or {}
        # Default values
        self.rsi_p = self.params.get("rsi_period", 10)
        self.sma_p = self.params.get("sma_period", 200)

        print("\nPARAMETERS RECEIVED:", self.params, "\n")
        # Column names built from parameters
        self.col_rsi = f"RSI_{self.rsi_p}"
        self.col_sma = f"SMA_{self.sma_p}"

        # Calculate RSI and SMA if not already present
        dataFrame[self.col_rsi] = Indicators.calculate_rsi(dataFrame['Close'], period=self.rsi_p)
        dataFrame[self.col_sma] = Indicators.calculate_sma(dataFrame['Close'], period=self.sma_p)


    def generate_entry_signals(self) -> pd.Series:
        """
        Generate vectorized entry signals for RSI_SMA strategy.
        RSI < 30 and Close > SMA.
        :return: Boolean Series of entry signals.
        """
        df = self.dataFrame
        return (df[self.col_rsi].shift(1) < 30) & (df['Close'].shift(1) > df[self.col_sma].shift(1)) & (df['Open'] > df['Close'].shift(1)) # & (df['Close'].shift(1) <= df[self.col_sma].shift(1) * 1.03)# can be used to trade only when the price is close to the SMA

    def generate_partial_exit_signals(self) -> pd.Series:
        """
        Generate vectorized partial exit signals for RSI_SMA strategy.
        RSI_10 > 40.
        :return: Boolean Series of partial exit signals.
        """
        df = self.dataFrame
        return df[self.col_rsi] > 40

    def generate_exit_signals(self) -> pd.Series:
        """
        Generate vectorized exit signals for RSI_SMA strategy.
        RSI_10 > 60.
        :return: Boolean Series of exit signals.
        """
        df = self.dataFrame
        return df[self.col_rsi] > 60
    
    def run_backtest(self) -> pd.DataFrame:
        df = self.dataFrame.copy()
        # Generate signals
        df['entry_signal'] = self.generate_entry_signals()
        df['partial_exit_signal'] = self.generate_partial_exit_signals()
        df['exit_signal'] = self.generate_exit_signals()
        
        df['entry_flags'], df['partial_exit_flags'], df['exit_flags'], df['entry_price'], df['partial_exit_price'], df['exit_price'] = execute_backtest(df['Open'].values, df['Close'].values, df['Low'].values, df['entry_signal'].values, df['partial_exit_signal'].values, df['exit_signal'].values)

        # Clean up the dataframe by removing signal columns
        df.drop(['entry_signal', 'exit_signal', 'partial_exit_signal'], axis=1, inplace=True)

        df_exits = df[df['exit_flags']].copy()
        df_exits['entry_date'] = df.index[df['entry_flags']].values[:len(df_exits)]

        # Set exit date (current index) and clean up the df
        df_exits['exit_date'] = df_exits.index
        df_exits = df_exits.drop(['Open', 'Close', 'Low', 'entry_flags', 'partial_exit_flags', 'exit_flags', self.col_rsi, self.col_sma], axis=1)

        # Reindex with trade ID and reorganize columns
        df_exits = df_exits.reset_index(drop=True)
        df_exits.index = df_exits.index + 1  # Start from 1 instead of 0
        df_exits.index.name = 'Trade ID'

        # Reorder columns to put dates first
        cols = ['entry_date', 'exit_date'] + [col for col in df_exits.columns if col not in ['entry_date', 'exit_date']]
        df_exits = df_exits[cols]

        # Calculate returns for each trade
        df_exits['return_pct'] = np.where(
            df_exits['partial_exit_price'].notna(),# if partial_exit_price not nan
            0.5 * (df_exits['partial_exit_price'] - df_exits['entry_price']) / df_exits['entry_price'] * 100 +
            0.5 * (df_exits['exit_price'] - df_exits['entry_price']) / df_exits['entry_price'] * 100,
            (df_exits['exit_price'] - df_exits['entry_price']) / df_exits['entry_price'] * 100) # if partial_exit_price is nan
        
        return df_exits