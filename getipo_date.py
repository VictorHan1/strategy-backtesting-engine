"""Check whether a ticker has Yahoo Finance price history around 10 years ago."""

import argparse
from datetime import datetime, timedelta

import yfinance as yf

WINDOW_DAYS = 5


def check_ten_year_data(ticker):
    """
    Check if Yahoo Finance has price data near the 10-year lookback date.
    
    Args:
        ticker (str): Stock ticker symbol.
    
    Returns:
        str: Human-readable summary of the available history.
    """
    ticker = ticker.strip().upper()
    
    try:
        today = datetime.now().date()
        ten_years_ago = today.replace(year=today.year - 10)
        
        # Use a small window to account for weekends and market holidays.
        start_date = ten_years_ago - timedelta(days=WINDOW_DAYS)
        end_date = ten_years_ago + timedelta(days=WINDOW_DAYS)
        
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date)
        
        if data.empty:
            return (
                f"No data found for {ticker} around {ten_years_ago} "
                f"(+/- {WINDOW_DAYS} days)"
            )
        
        result = f"Ticker: {ticker}\n"
        result += f"Checking for data around: {ten_years_ago}\n"
        
        available_dates = data.index.date
        
        if len(available_dates) > 0:
            closest_date = min(available_dates, key=lambda d: abs((d - ten_years_ago).days))
            days_off = abs((closest_date - ten_years_ago).days)
            
            result += f"Data found. Closest date to target: {closest_date}\n"
            result += f"   ({days_off} days from exact 10-year mark)"
        else:
            result += f"No data found in the +/- {WINDOW_DAYS}-day window"
            
        return result
        
    except Exception as e:
        return f"Error checking data for {ticker}: {str(e)}"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check whether a ticker has price data from around 10 years ago."
    )
    parser.add_argument("ticker", type=str, help="Stock ticker symbol")
    return parser.parse_args()


def main():
    args = parse_args()
    print(check_ten_year_data(args.ticker))


if __name__ == "__main__":
    main()
