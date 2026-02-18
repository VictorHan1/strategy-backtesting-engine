"""
Efficient script to check if stock data exists from exactly 10 years ago
Uses yfinance library to access Yahoo Finance data
"""

import yfinance as yf
import argparse
from datetime import datetime, timedelta
import pandas as pd

def check_ten_year_data(ticker):
    """
    Checks if data exists for a ticker from exactly 10 years ago
    
    Args:
        ticker (str): The stock ticker symbol
    
    Returns:
        str: Information about whether data exists from 10 years ago
    """
    ticker = ticker.strip().upper()
    
    try:
        # Calculate date exactly 10 years ago
        today = datetime.now().date()
        ten_years_ago = today.replace(year=today.year - 10)
        
        # Add a small window to account for weekends/holidays
        start_date = ten_years_ago - timedelta(days=5)  # 5 days before
        end_date = ten_years_ago + timedelta(days=5)    # 5 days after
        
        # Only request data for this specific window
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date)
        
        if data.empty:
            return f"❌ No data found for {ticker} around {ten_years_ago} (±5 days)"
        
        # Check if any data point is within our window
        result = f"Ticker: {ticker}\n"
        result += f"Checking for data around: {ten_years_ago}\n"
        
        # Get the available dates in our window
        available_dates = data.index.date
        
        # Show the dates found
        if len(available_dates) > 0:
            closest_date = min(available_dates, key=lambda d: abs((d - ten_years_ago).days))
            days_off = abs((closest_date - ten_years_ago).days)
            
            result += f"✅ Data found! Closest date to target: {closest_date}\n"
            result += f"   ({days_off} days from exact 10-year mark)"
        else:
            result += f"❌ No data found in the ±5 day window"
            
        return result
        
    except Exception as e:
        return f"Error checking data for {ticker}: {str(e)}"

if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Check if stock data exists from 10 years ago')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol')
    args = parser.parse_args()
    
    # Install required library if not present
    try:
        import yfinance
    except ImportError:
        print("Required library yfinance not found. Installing...")
        import subprocess
        subprocess.call(["pip", "install", "yfinance"])
        import yfinance as yf
    
    # Check if data exists from 10 years ago
    result = check_ten_year_data(args.ticker)
    print(result)