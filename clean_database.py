"""
merge_csv_to_sqlite.py
======================

Merge two (or more) CSV files containing the same stock symbols but
different columns into a single table without duplicates, then save
the result into an SQLite database.

Author: Your Name
Date: 2025-05-26
"""

import pandas as pd
import sqlite3
from pathlib import Path

# ----- CONFIGURATION -----
CSV_FILES = ["finviz_minervini_tickers.csv", "finviz_screener_cache_enhanced.csv"]  # add more files if needed
UNIQUE_KEY = "Ticker"                                 # primary identifier
DB_NAME = "stocks.db"
TABLE_NAME = "stock_metadata"
# --------------------------

def load_csvs(file_list):
    """Load all CSV files into a list of DataFrames."""
    dfs = []
    for f in file_list:
        if not Path(f).is_file():
            raise FileNotFoundError(f"CSV file not found: {f}")
        df = pd.read_csv(f)
        dfs.append(df)
    return dfs

def merge_dataframes(dfs, key):
    """
    Perform an outer merge of multiple DataFrames on *key* so that
    every column from every file is preserved.
    """
    merged = dfs[0]
    for nxt in dfs[1:]:
        merged = pd.merge(
            merged,
            nxt,
            on=key,
            how="outer",
            suffixes=("", "_dup")  # handle duplicate column names
        )
    # Optionally, remove exact duplicate rows
    merged = merged.drop_duplicates()
    # If columns with _dup suffix were created, resolve them here (keep first non-null)
    for col in merged.columns:
        if col.endswith("_dup"):
            base_col = col.replace("_dup", "")
            merged[base_col] = merged[base_col].combine_first(merged[col])
            merged.drop(columns=col, inplace=True)
    return merged

def save_to_sqlite(df, db_name, table_name):
    """Save DataFrame to SQLite table (replace if exists)."""
    with sqlite3.connect(db_name) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)

def clean_illiquid_stocks(db_name: str,
                          table_name: str = "stock_metadata",
                          turnover_limit: float = 5_000_000):
    """
    Remove stocks whose 200-day turnover (SMA200 * Avg Volume) is below
    *turnover_limit* USD. 1️⃣ show list ➜ 2️⃣ ask confirmation ➜ 3️⃣ delete.
    """

    with sqlite3.connect(db_name) as conn:
        # Load only the needed columns
        query = f"""
            SELECT Ticker, SMA200, "Avg Volume", price,
                   (Price / (1 + SMA200) * "Avg Volume") AS Turnover
            FROM {table_name}
        """
        df = pd.read_sql(query, conn)

        # Find rows below the limit
        to_drop = df[df["Turnover"] < turnover_limit]

        if to_drop.empty:
            print("✅ No illiquid stocks found (all above the limit).")
            return

        # Show a compact preview
        print("\n⚠️  The following Tickers will be removed "
              f"(Turnover < {turnover_limit:,}):")
        print(to_drop[["Ticker", "Turnover"]]
              .sort_values("Turnover")
              .to_string(index=False, formatters={"Turnover": "{:,.0f}".format}))

        # Ask for confirmation
        ans = input("\nProceed with deletion? [y/N]: ").strip().lower()
        if ans != "y":
            print("❌ Deletion aborted — no changes made.")
            return

        # Execute deletion
        symbols_tuple = tuple(to_drop["Ticker"])
        delete_sql = f"""
            DELETE FROM {table_name}
            WHERE Ticker IN {symbols_tuple}
        """
        conn.execute(delete_sql)
        conn.commit()
        print(f"🗑️  Deleted {len(symbols_tuple)} rows from {table_name}.")

def main():
    clean_illiquid_stocks(DB_NAME, TABLE_NAME, turnover_limit=7_000_000)

if __name__ == "__main__":
    main()
