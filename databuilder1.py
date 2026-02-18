"""
fetch_single_ticker.py
======================

Pull daily OHLCV data **plus indicators** (RSI-10, SMA-200) for a
single ticker—*only if the DB does not already contain records
back to 27-May-2015*—and append it to an SQLite table.

• Table is created with indicator columns if absent
• Names are stored in snake_case for consistency
• Primary-key (ticker, date) prevents duplicates

Author : Your Name
Date   : 2025-05-26
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd
import yfinance as yf

from indicators import Indicators  # your module with add_rsi / add_sma

# ── CONFIG ───────────────────────────────────────────────────────────
DB_PATH      = "stocks.db"
PRICE_TABLE  = "prices_data"
START_DATE   = "2015-05-23"        # earliest date that must exist
END_DATE     = "2025-05-23"        # change if needed
# ─────────────────────────────────────────────────────────────────────


# ── DDL ──────────────────────────────────────────────────────────────
def ensure_price_table(conn: sqlite3.Connection) -> None:
    """Create the destination table (incl. indicators) if it is missing."""
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {PRICE_TABLE} (
        ticker       TEXT NOT NULL,
        date         DATE NOT NULL,
        open         REAL,
        high         REAL,
        low          REAL,
        close        REAL,
        adj_close    REAL,
        volume       INTEGER,
        rsi_10       REAL,
        sma_200      REAL,
        PRIMARY KEY (ticker, date)
    );
    """
    conn.execute(ddl)
    conn.commit()


# ── EXISTENCE CHECK ─────────────────────────────────────────────────
def has_data_since(conn: sqlite3.Connection, ticker: str, start: str) -> bool:
    """
    Return True if *any* row for *ticker* exists on or before *start* date.
    This means historical data from that date back is already present.
    """
    q = f"""
    SELECT 1 FROM {PRICE_TABLE}
    WHERE ticker = ?
      AND date <= ?
    LIMIT 1
    """
    return conn.execute(q, (ticker, start)).fetchone() is not None


# ── FETCH + PREPARE ─────────────────────────────────────────────────
def fetch_one_stock_data(symbol: str,
                         start_date: str,
                         end_date: str) -> pd.DataFrame:
    """Download OHLCV + indicators, return clean DataFrame ready for DB."""
    df = yf.download(symbol, start=start_date, end=end_date,
                     actions=True, progress=False, threads=False, auto_adjust=False, timeout=300)

    if df.empty:
        raise ValueError(f"No data returned for {symbol}")

    df.sort_index(inplace=True)
    df = Indicators.add_rsi(df, period=10)
    df = Indicators.add_sma(df, period=200)

    # bring index to column, standardise names
    df.reset_index(inplace=True)
    df["ticker"] = symbol
    df.rename(columns={
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
        "RSI_10": "rsi_10",
        "SMA_200": "sma_200",
    }, inplace=True)

    # keep only defined columns
    df = df[["ticker", "date", "open", "high", "low",
             "close", "adj_close", "volume",
             "rsi_10", "sma_200"]]
    return df


# ── MAIN ────────────────────────────────────────────────────────────
def main() -> None:
    ticker = "AAL"
    flag = False

    Path(DB_PATH).touch(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        ensure_price_table(conn)
        query = f"SELECT DISTINCT Ticker FROM stock_metadata"
        rows = cursor.execute(query).fetchall()

        for i, (ticker,) in enumerate(rows, 1):
            if ticker == "ZTS":
                flag = True

            if flag and ticker != "ZTS" and ticker != "ZWS":
                df = fetch_one_stock_data(ticker, START_DATE, END_DATE)
                # manual preview
                print("\n📋 Preview:")
                print(df.head(), f"\nRows: {len(df)}")
                # save
                df.to_sql(PRICE_TABLE, conn, if_exists="append",
                        index=False, method="multi")
                conn.commit()
                print(f"✅ saved {len(df)} rows for {ticker} into '{PRICE_TABLE}'")
            else:
                print(f"❌ Skipping {ticker} (alredy exists or is excluded)")


if __name__ == "__main__":
    main()
