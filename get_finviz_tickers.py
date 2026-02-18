import pandas as pd
import os
from finvizfinance.screener.overview import Overview
from finvizfinance.screener.technical import Technical
from finvizfinance.screener.valuation import Valuation
from finvizfinance.screener.financial import Financial
from finvizfinance.screener.ownership import Ownership

def get_finviz_tickers_with_filters(use_cache=True):
    """
    Get tickers from FinViz with filters matching:
    https://finviz.com/screener.ashx?v=211&f=cap_midover%2Cipodate_more10%2Csh_avgvol_o300%2Csh_price_o7&ft=4
    
    Filters:
    - Market cap: Mid-cap and above (cap_midover)
    - IPO date: More than 10 years ago (ipodate_more10)
    - Average volume: Over 300K (sh_avgvol_o300)
    - Price: Over $7 (sh_price_o7)
    
    Returns data with Mark Minervini-style growth metrics including:
    - Earnings growth metrics
    - Sales growth
    - Institutional Ownership
    - Target Price
    - And other relevant technical/fundamental indicators
    
    Args:
        use_cache (bool): If True, uses cached data if available to avoid refetching
    """
    cache_file = "finviz_screener_cache_enhanced.csv"
    
    # Check if cache exists and use_cache is True
    if use_cache and os.path.exists(cache_file):
        print(f"Loading from cache file: {cache_file}")
        df = pd.read_csv(cache_file)
        print(f"Cache contains {len(df)} tickers with columns: {', '.join(df.columns)}")
        
        # Go straight to column selection
        filtered_df = select_desired_columns(df)
        
        # Save to CSV
        output_filename = "finviz_minervini_tickers.csv"
        filtered_df.to_csv(output_filename, index=False)
        print(f"✅ Filtered tickers saved to: {output_filename}")
        
        return filtered_df
    
    # Define filters matching your URL parameters
    filters_dict = {
        'Market Cap.': '+Mid (over $2bln)',     # cap_midover
        'IPO Date': 'More than 10 years ago',   # ipodate_more10
        'Average Volume': 'Over 300K',          # sh_avgvol_o300 (changed from 500K to 300K)
        'Price': 'Over $7'                      # sh_price_o7 (changed from $10 to $7)
    }
    
    # Try multiple screener types to get all the columns we need
    screeners_data = {}
    
    print("=" * 60)
    print("FETCHING DATA FROM MULTIPLE FINVIZ SCREENERS")
    print("=" * 60)
    
    # Technical screener - has Beta, RSI, Performance metrics
    print("1. Fetching data from Technical screener...")
    try:
        tech_screener = Technical()
        tech_screener.set_filter(filters_dict=filters_dict)
        screeners_data['technical'] = tech_screener.screener_view()
        print(f"   ✅ Technical screener: {len(screeners_data['technical'])} stocks")
        print(f"   Columns: {', '.join(screeners_data['technical'].columns)}")
    except Exception as e:
        print(f"   ❌ Technical screener failed: {e}")
    
    # Overview screener - has basic fundamental data
    print("\n2. Fetching data from Overview screener...")
    try:
        overview_screener = Overview()
        overview_screener.set_filter(filters_dict=filters_dict)
        screeners_data['overview'] = overview_screener.screener_view()
        print(f"   ✅ Overview screener: {len(screeners_data['overview'])} stocks")
        print(f"   Columns: {', '.join(screeners_data['overview'].columns)}")
    except Exception as e:
        print(f"   ❌ Overview screener failed: {e}")
    
    # Valuation screener - has P/E, PEG, valuation metrics
    print("\n3. Fetching data from Valuation screener...")
    try:
        valuation_screener = Valuation()
        valuation_screener.set_filter(filters_dict=filters_dict)
        screeners_data['valuation'] = valuation_screener.screener_view()
        print(f"   ✅ Valuation screener: {len(screeners_data['valuation'])} stocks")
        print(f"   Columns: {', '.join(screeners_data['valuation'].columns)}")
    except Exception as e:
        print(f"   ❌ Valuation screener failed: {e}")
    
    # Financial screener - has earnings growth, sales growth, ROE, etc.
    print("\n4. Fetching data from Financial screener...")
    try:
        financial_screener = Financial()
        financial_screener.set_filter(filters_dict=filters_dict)
        screeners_data['financial'] = financial_screener.screener_view()
        print(f"   ✅ Financial screener: {len(screeners_data['financial'])} stocks")
        print(f"   Columns: {', '.join(screeners_data['financial'].columns)}")
    except Exception as e:
        print(f"   ❌ Financial screener failed: {e}")
    
    # Ownership screener - has institutional ownership, insider ownership
    print("\n5. Fetching data from Ownership screener...")
    try:
        ownership_screener = Ownership()
        ownership_screener.set_filter(filters_dict=filters_dict)
        screeners_data['ownership'] = ownership_screener.screener_view()
        print(f"   ✅ Ownership screener: {len(screeners_data['ownership'])} stocks")
        print(f"   Columns: {', '.join(screeners_data['ownership'].columns)}")
    except Exception as e:
        print(f"   ❌ Ownership screener failed: {e}")
    
    if not screeners_data:
        print("❌ ERROR: No screener data was successfully fetched!")
        return pd.DataFrame()
    
    print("\n" + "=" * 60)
    print("COMBINING DATA FROM ALL SCREENERS")
    print("=" * 60)
    
    # Start with the first available dataframe as base
    base_df = None
    base_name = None
    for name, df in screeners_data.items():
        if df is not None and len(df) > 0:
            base_df = df.copy()
            base_name = name
            print(f"Using {name} screener as base with {len(base_df)} stocks")
            break
    
    if base_df is None:
        print("❌ ERROR: No valid base dataframe found!")
        return pd.DataFrame()
    
    # Merge with other dataframes one by one
    for name, df in screeners_data.items():
        if name == base_name or df is None or len(df) == 0:
            continue
        
        print(f"\nMerging {name} screener data...")
        
        # Get the common tickers
        base_tickers = set(base_df['Ticker'].tolist())
        merge_tickers = set(df['Ticker'].tolist())
        common_tickers = base_tickers.intersection(merge_tickers)
        
        print(f"   Base has {len(base_tickers)} tickers, {name} has {len(merge_tickers)} tickers")
        print(f"   Common tickers: {len(common_tickers)}")
        
        # Merge on Ticker
        try:
            base_df = pd.merge(base_df, df, on='Ticker', how='outer', suffixes=('', f'_{name}'))
            
            # Remove duplicate columns (keep the original, drop the suffixed ones)
            cols_to_drop = [col for col in base_df.columns if col.endswith(f'_{name}')]
            if cols_to_drop:
                base_df = base_df.drop(columns=cols_to_drop)
                print(f"   Dropped duplicate columns: {', '.join(cols_to_drop)}")
            
            print(f"   ✅ Merged successfully. Combined dataframe now has {len(base_df)} rows and {len(base_df.columns)} columns")
            
        except Exception as e:
            print(f"   ❌ Failed to merge {name} screener: {e}")
    
    # Now we have a combined dataframe with all available columns
    df = base_df
    print(f"\n🎉 FINAL COMBINED DATASET:")
    print(f"   Total stocks: {len(df)}")
    print(f"   Total columns: {len(df.columns)}")
    print(f"   All columns: {', '.join(sorted(df.columns))}")
    
    # Save full data to cache file to avoid refetching
    df.to_csv(cache_file, index=False)
    print(f"\n✅ Raw data saved to cache: {cache_file}")
    
    # Select desired columns with Minervini-style metrics
    filtered_df = select_desired_columns(df)
    
    # Save to CSV
    output_filename = "finviz_minervini_tickers.csv"
    filtered_df.to_csv(output_filename, index=False)
    print(f"✅ Filtered tickers saved to: {output_filename}")
    
    return filtered_df

def select_desired_columns(df):
    """
    Select and reorder the desired columns from the dataframe.
    Focus on Mark Minervini-style growth stock metrics.
    
    Args:
        df: pandas DataFrame with all the columns
        
    Returns:
        DataFrame with only the desired columns for growth stock analysis
    """
    print("\n" + "=" * 60)
    print("SELECTING MINERVINI-STYLE GROWTH STOCK COLUMNS")
    print("=" * 60)
    
    # Define the columns we want to keep in priority order
    columns_to_keep = []
    
    # 1. BASIC IDENTIFICATION
    essential_columns = ['Ticker', 'Company', 'Sector', 'Industry']
    for col in essential_columns:
        if col in df.columns:
            columns_to_keep.append(col)
            print(f"✅ {col}")
        else:
            print(f"❌ {col} - NOT FOUND")
    
    # 2. PRICE AND MARKET DATA
    price_columns = ['Price', 'Change', 'Market Cap']
    for col in price_columns:
        if col in df.columns:
            columns_to_keep.append(col)
            print(f"✅ {col}")
        else:
            print(f"❌ {col} - NOT FOUND")
    
    # 3. VOLUME DATA (Critical for Minervini)
    volume_variants = ['Avg Volume', 'AvgVolume', 'Avg. Volume', 'Average Volume', 'Avg Vol', 'Volume']
    found_volume = False
    for variant in volume_variants:
        if variant in df.columns and not found_volume:
            columns_to_keep.append(variant)
            print(f"✅ Average Volume (as '{variant}')")
            found_volume = True
    
    if not found_volume:
        print("❌ Average Volume - NOT FOUND with any variant")
    
    # 4. EARNINGS GROWTH METRICS (Core Minervini criteria)
    earnings_growth_variants = [
        'EPS growth this year', 'EPS Growth', 'EPS growth past 5 years', 
        'EPS Growth (ttm)', 'EPS Growth Y/Y', 'EPS growth next year',
        'EPS (ttm)', 'EPS growth next 5 years', 'EPS Q/Q', 'EPS Y/Y'
    ]
    print(f"\n📈 EARNINGS GROWTH METRICS:")
    for variant in earnings_growth_variants:
        if variant in df.columns:
            columns_to_keep.append(variant)
            print(f"✅ {variant}")
    
    # 5. SALES GROWTH (Also important for Minervini)
    sales_growth_variants = [
        'Sales growth past 5 years', 'Sales Growth', 'Sales Q/Q', 'Sales Y/Y',
        'Revenue Growth', 'Sales growth this year', 'Sales growth next year'
    ]
    print(f"\n📊 SALES GROWTH METRICS:")
    for variant in sales_growth_variants:
        if variant in df.columns:
            columns_to_keep.append(variant)
            print(f"✅ {variant}")
    
    # 6. PROFITABILITY METRICS
    profitability_variants = [
        'ROE', 'ROI', 'ROA', 'Gross Margin', 'Oper. Margin', 'Profit Margin',
        'Operating Margin', 'Net Margin'
    ]
    print(f"\n💰 PROFITABILITY METRICS:")
    for variant in profitability_variants:
        if variant in df.columns:
            columns_to_keep.append(variant)
            print(f"✅ {variant}")
    
    # 7. VALUATION METRICS
    valuation_variants = [
        'P/E', 'Forward P/E', 'PEG', 'P/S', 'P/B', 'P/C', 'P/FCF',
        'EPS (ttm)', 'EPS next Y', 'EPS next 5Y', 'Book/sh'
    ]
    print(f"\n💵 VALUATION METRICS:")
    for variant in valuation_variants:
        if variant in df.columns:
            columns_to_keep.append(variant)
            print(f"✅ {variant}")
    
    # 8. OWNERSHIP DATA (You specifically requested)
    ownership_variants = [
        'Institutional Ownership', 'Inst Own', 'Institutional Own', 'Inst. Own',
        'Insider Own', 'Insider Owner', 'Insider Ownership', 'Insider Own.'
    ]
    print(f"\n🏢 OWNERSHIP METRICS:")
    for variant in ownership_variants:
        if variant in df.columns:
            columns_to_keep.append(variant)
            print(f"✅ {variant}")
    
    # 9. TARGET PRICE (You specifically requested)
    target_price_variants = ['Target Price', 'Price Target', 'Analyst Target', 'Target']
    print(f"\n🎯 TARGET PRICE:")
    found_target = False
    for variant in target_price_variants:
        if variant in df.columns and not found_target:
            columns_to_keep.append(variant)
            print(f"✅ {variant}")
            found_target = True
    
    if not found_target:
        print("❌ Target Price - NOT FOUND with any variant")
    
    # 10. TECHNICAL INDICATORS (Important for Minervini's SEPA methodology)
    technical_variants = [
        'Beta', 'RSI (14)', 'RSI', 'Perf Week', 'Perf Month', 'Perf Quarter', 
        'Perf Half Y', 'Perf Year', 'Perf YTD', 'Volatility', 'Volatility (Month)',
        'SMA20', 'SMA50', 'SMA200', '50-Day Simple Moving Average', '200-Day Simple Moving Average',
        'Recom', 'Rel Volume'
    ]
    print(f"\n📈 TECHNICAL INDICATORS:")
    for variant in technical_variants:
        if variant in df.columns:
            columns_to_keep.append(variant)
            print(f"✅ {variant}")
    
    # 11. ADDITIONAL FUNDAMENTAL METRICS
    additional_variants = [
        'Debt/Eq', 'Current Ratio', 'Quick Ratio', 'LT Debt/Eq', 'Dividend %',
        'Payout', 'Income', 'Employees', 'Optionable', 'Shortable', 'Short Ratio',
        'Short Interest'
    ]
    print(f"\n📋 ADDITIONAL METRICS:")
    for variant in additional_variants:
        if variant in df.columns:
            columns_to_keep.append(variant)
            print(f"✅ {variant}")
    
    # Create a new dataframe with only the columns we want
    if columns_to_keep:
        # Remove duplicates while preserving order
        columns_to_keep = list(dict.fromkeys(columns_to_keep))
        filtered_df = df[columns_to_keep]
        
        print(f"\n🎯 FINAL SELECTED COLUMNS ({len(columns_to_keep)} total):")
        for i, col in enumerate(columns_to_keep, 1):
            print(f"   {i:2d}. {col}")
            
    else:
        filtered_df = df
        print("⚠️ Could not find any of the desired columns. Keeping all columns.")
    
    # Print summary info
    if 'Ticker' in filtered_df.columns:
        tickers = filtered_df['Ticker'].tolist()
        print(f"\n🎉 SUMMARY:")
        print(f"   Total stocks found: {len(tickers)}")
        print(f"   Total data columns: {len(filtered_df.columns)}")
        
        # Show a few example tickers
        if len(tickers) > 0:
            example_tickers = tickers[:10] if len(tickers) >= 10 else tickers
            print(f"   Example tickers: {', '.join(example_tickers)}")
            if len(tickers) > 10:
                print(f"   ... and {len(tickers) - 10} more")
    
    return filtered_df

def analyze_minervini_criteria(df):
    """
    Analyze the dataset for Mark Minervini's key criteria.
    This function helps identify which stocks meet his growth criteria.
    """
    print("\n" + "=" * 60)
    print("MARK MINERVINI CRITERIA ANALYSIS")
    print("=" * 60)
    
    if df.empty:
        print("❌ No data to analyze")
        return
    
    total_stocks = len(df)
    print(f"Total stocks in dataset: {total_stocks}")
    
    # Check for key Minervini criteria columns
    criteria_checks = []
    
    # 1. Earnings Growth
    earnings_cols = [col for col in df.columns if 'EPS' in col and 'growth' in col.lower()]
    if earnings_cols:
        print(f"✅ Earnings Growth data available: {', '.join(earnings_cols)}")
        criteria_checks.append("Earnings Growth")
    else:
        print("❌ No earnings growth data found")
    
    # 2. Sales Growth
    sales_cols = [col for col in df.columns if 'Sales' in col and 'growth' in col.lower()]
    if sales_cols:
        print(f"✅ Sales Growth data available: {', '.join(sales_cols)}")
        criteria_checks.append("Sales Growth")
    else:
        print("❌ No sales growth data found")
    
    # 3. ROE (Return on Equity)
    if 'ROE' in df.columns:
        print("✅ ROE (Return on Equity) data available")
        criteria_checks.append("ROE")
    else:
        print("❌ No ROE data found")
    
    # 4. Institutional Ownership
    inst_own_cols = [col for col in df.columns if 'institutional' in col.lower() or 'inst' in col.lower()]
    if inst_own_cols:
        print(f"✅ Institutional Ownership data available: {', '.join(inst_own_cols)}")
        criteria_checks.append("Institutional Ownership")
    else:
        print("❌ No institutional ownership data found")
    
    # 5. Price Performance
    perf_cols = [col for col in df.columns if 'perf' in col.lower() or 'performance' in col.lower()]
    if perf_cols:
        print(f"✅ Price Performance data available: {', '.join(perf_cols)}")
        criteria_checks.append("Price Performance")
    else:
        print("❌ No price performance data found")
    
    print(f"\n📊 MINERVINI CRITERIA COVERAGE: {len(criteria_checks)}/5")
    print("   ✅ Available:", ", ".join(criteria_checks))
    
    missing_criteria = set(["Earnings Growth", "Sales Growth", "ROE", "Institutional Ownership", "Price Performance"]) - set(criteria_checks)
    if missing_criteria:
        print("   ❌ Missing:", ", ".join(missing_criteria))
    
    return criteria_checks

if __name__ == "__main__":
    print("🚀 ENHANCED FINVIZ SCREENER FOR MARK MINERVINI GROWTH STOCKS")
    print("=" * 70)
    
    # Use True to load from cache if available, False to force refetch
    result_df = get_finviz_tickers_with_filters(use_cache=True)
    
    if not result_df.empty:
        # Analyze the results for Minervini criteria
        analyze_minervini_criteria(result_df)
        
        print(f"\n🎉 SUCCESS! Found {len(result_df)} stocks matching your criteria.")
        print("📁 Files created:")
        print("   • finviz_screener_cache_enhanced.csv (full raw data)")
        print("   • finviz_minervini_tickers.csv (filtered for growth analysis)")
    else:
        print("❌ No data was retrieved. Please check your internet connection and try again.")