import pandas as pd
from indicators import Indicators
import sqlite3
from typing import Dict
import sys

class DataHandler:
    def __init__(self):
        self.data_dict = {}

    def load_data(self) -> Dict[str, pd.DataFrame]:
        """
        Prepares the historical data for the given symbol within the specified date range.
        This method downloads the data, processes it, and stores it in the dataFrame attribute.
        :return: A dictionary containing the processed DataFrame."""

        try:
            conn = sqlite3.connect("sample_stocks.db")
        except sqlite3.Error as e:
            print(f"Failed to connect to database: {e}")
            sys.exit(1)
        print("Connection to database established successfully. Loading data...")

        df = pd.read_sql_query(
            "SELECT * FROM prices_data", conn, parse_dates=["date"]
        )
        conn.close()
        print("Data loaded successfully from database.")

        # Multi-index for fast grouping, then split to dict
        df.set_index(["ticker", "date"], inplace=True)
        df.columns = [str(c).capitalize() for c in df.columns]
        self.data_dict = {t: g.copy() for t, g in df.groupby(level="ticker")} # .copy() → each DF owns its memory
        del df
        return self.data_dict


    def get_data(self) -> pd.DataFrame:
        """
        Returns the prepared data with indicators.
        """
        if self.dataFrame is None:
            raise ValueError("Data not prepared.")
        return self.dataFrame
    
    ##############
    def _parse_market_cap(self, value):
        """
        Converts string market cap (e.g., '1.5B', '200M') to float.
        """
        if pd.isna(value) or value == '':
            return 0.0
        
        value = str(value).upper().strip()
        multiplier = 1.0
        
        if 'T' in value:
            multiplier = 1e12
            value = value.replace('T', '')
        elif 'B' in value:
            multiplier = 1e9
            value = value.replace('B', '')
        elif 'M' in value:
            multiplier = 1e6
            value = value.replace('M', '')
            
        try:
            return float(value) * multiplier
        except ValueError:
            return 0.0

    def load_filtered_data(self, min_market_cap: float = 10e9) -> Dict[str, pd.DataFrame]:
        """
        Loads price data only for stocks exceeding a specific Market Cap.
        """
        info_table = "stock_metadata" # Change this if your metadata table has a different name
        
        try:
            conn = sqlite3.connect("sample_stocks.db")
            
            # 1. Fetch metadata to identify relevant tickers
            # We use double quotes because "Market Cap" has a space
            info_df = pd.read_sql_query(f'SELECT Ticker, "Market Cap" FROM {info_table}', conn)
            
            # 2. Convert Market Cap strings to numeric values
            info_df['mcap_numeric'] = info_df['Market Cap'].apply(self._parse_market_cap)
            
            # 3. Filter tickers
            valid_tickers = info_df[info_df['mcap_numeric'] >= min_market_cap]['Ticker'].tolist()
            
            if not valid_tickers:
                print(f"[WARNING] No stocks found with Market Cap <= {min_market_cap}")
                return {}

            print(f"[INFO] Found {len(valid_tickers)} stocks matching criteria. Loading prices...")

            # 4. Load prices only for these tickers
            # Using placeholders for SQL safety
            placeholders = ','.join(['?'] * len(valid_tickers))
            query = f"SELECT * FROM prices_data WHERE ticker IN ({placeholders})"
            
            df = pd.read_sql_query(query, conn, params=valid_tickers, parse_dates=["date"])
            conn.close()

            # Process into dictionary
            df.set_index(["ticker", "date"], inplace=True)
            df.columns = [str(c).capitalize() for c in df.columns]
            self.data_dict = {t: g.copy() for t, g in df.groupby(level="ticker")}
            
            print(f"[SUCCESS] Loaded {len(self.data_dict)} stocks for backtesting.")
            return self.data_dict

        except sqlite3.Error as e:
            print(f"[ERROR] Database operation failed: {e}")
            sys.exit(1)
