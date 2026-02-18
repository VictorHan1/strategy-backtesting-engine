"""
stock_data_fetcher.py
=====================

Fetch 10 years of daily OHLCV data for every stock symbol in
`stock_metadata` (column `symbol`) and store it in
`historical_stock_data` within stocks.db.

• Adds/updates AdjClose
• Commits on each symbol
• 1.5-second polite pause between API calls
• Logs successes and failures

Author : Your Name
Date   : 2025-05-26
"""

import time
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import pandas as pd
import yfinance as yf

# ── LOGGING ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
# ───────────────────────────────────────────────────────────


class StockDataFetcher:
    """Fetch and persist historical prices for a list of tickers."""

    def __init__(self, db_path: str = "stocks.db"):
        self.db_path = db_path
        Path(db_path).touch(exist_ok=True)          # create file if absent
        self.conn = sqlite3.connect(db_path)
        self.create_historical_table()

    # ── DDL ────────────────────────────────────────────────
    def create_historical_table(self) -> None:
        """Create the destination table once."""
        ddl = """
        CREATE TABLE IF NOT EXISTS historical_stock_data (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol            TEXT NOT NULL,
            date              DATE NOT NULL,
            open_price        REAL,
            high_price        REAL,
            low_price         REAL,
            close_price       REAL,
            adj_close_price   REAL,
            volume            INTEGER,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date)
        );
        CREATE INDEX IF NOT EXISTS idx_symbol_date
            ON historical_stock_data(symbol, date);
        """
        self.conn.executescript(ddl)
        logger.info("✅ historical_stock_data table ready")

    # ── METADATA ───────────────────────────────────────────
    def get_stock_symbols(
        self,
        table_name: str = "stock_metadata",
        symbol_column: str = "symbol",
    ) -> List[str]:
        """Return distinct symbols from metadata table."""
        cur = self.conn.cursor()

        # verify table
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        if not cur.fetchone():
            logger.error(f"❌ table '{table_name}' not found in DB")
            return []

        # verify column
        cur.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cur.fetchall()]
        if symbol_column not in columns:
            logger.error(
                f"❌ column '{symbol_column}' not found – available: {columns}"
            )
            return []

        cur.execute(
            f"SELECT DISTINCT {symbol_column} "
            f"FROM {table_name} "
            f"WHERE {symbol_column} IS NOT NULL AND {symbol_column}!=''"
        )
        symbols = [row[0] for row in cur.fetchall()]
        logger.info(f"📦 {len(symbols)} unique symbols found")
        return symbols

    # ── FETCH ─────────────────────────────────────────────
    def fetch_stock_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[pd.DataFrame]:
        """Return cleaned OHLCV DataFrame (or None if empty/error)."""
        try:
            data = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                progress=False,
                threads=False,
            )
            if data.empty:
                logger.warning(f"⚠️  empty DataFrame for {symbol}")
                return None

            data.reset_index(inplace=True)
            data["Symbol"] = symbol

            # standardize column names
            data.columns = [
                "Date",
                "Open",
                "High",
                "Low",
                "Close",
                "AdjClose",
                "Volume",
                "Dividends",
                "StockSplits",
                "Symbol",
            ]
            data = data[
                ["Symbol", "Date", "Open", "High", "Low", "Close", "AdjClose", "Volume"]
            ]
            return data

        except Exception as ex:
            logger.error(f"🚫 fetch error for {symbol}: {ex}")
            return None

    # ── PERSIST ───────────────────────────────────────────
    def save_stock_data(self, df: pd.DataFrame) -> None:
        """Upsert DataFrame rows into SQLite."""
        cur = self.conn.cursor()
        for _, row in df.iterrows():
            cur.execute(
                """
                INSERT OR REPLACE INTO historical_stock_data
                (symbol, date, open_price, high_price, low_price,
                 close_price, adj_close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["Symbol"],
                    row["Date"].strftime("%Y-%m-%d"),
                    row["Open"],
                    row["High"],
                    row["Low"],
                    row["Close"],
                    row["AdjClose"],
                    row["Volume"],
                ),
            )
        self.conn.commit()
        logger.info(f"💾 saved {len(df)} rows for {df['Symbol'].iloc[0]}")

    # ── MAIN LOOP ─────────────────────────────────────────
    def fetch_all(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        table_name: str = "stock_metadata",
        symbol_column: str = "symbol",
        delay: float = 1.5,
    ) -> None:
        """Fetch and store data for every symbol in metadata."""
        end_date = end_date or datetime.now()
        start_date = start_date or end_date - timedelta(days=365 * 10)

        logger.info(
            f"🔄 fetching from {start_date.date()} to {end_date.date()} "
            f"(delay {delay}s)"
        )

        symbols = self.get_stock_symbols(table_name, symbol_column)
        if not symbols:
            return

        success = fail = 0
        for i, sym in enumerate(symbols, 1):
            logger.info(f"▶️  {sym} ({i}/{len(symbols)})")
            df = self.fetch_stock_data(sym, start_date, end_date)
            if df is not None and not df.empty:
                self.save_stock_data(df)
                success += 1
            else:
                fail += 1
            if i < len(symbols):
                time.sleep(delay)

        logger.info(f"🏁 done – success: {success} | fail: {fail}")

    # ── STATS ─────────────────────────────────────────────
    def get_statistics(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT symbol) FROM historical_stock_data")
        symbols = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM historical_stock_data")
        rows = cur.fetchone()[0]
        cur.execute("SELECT MIN(date), MAX(date) FROM historical_stock_data")
        dmin, dmax = cur.fetchone()
        logger.info(
            f"📊 stats – symbols: {symbols} | rows: {rows} | "
            f"date range: {dmin} ➜ {dmax}"
        )

    # ── CLEANUP ──────────────────────────────────────────
    def close(self):
        self.conn.close()


# ── USAGE EXAMPLE ────────────────────────────────────────
if __name__ == "__main__":
    fetcher = StockDataFetcher("stocks.db")
    try:
        fetcher.fetch_all(                # adjust if needed
            table_name="stock_metadata",
            symbol_column="symbol",
            delay=1.5,
        )
        fetcher.get_statistics()
    finally:
        fetcher.close()
