import os

import pandas as pd
from finvizfinance.screener.financial import Financial
from finvizfinance.screener.overview import Overview
from finvizfinance.screener.ownership import Ownership
from finvizfinance.screener.technical import Technical
from finvizfinance.screener.valuation import Valuation


CACHE_FILE = "finviz_screener_cache_enhanced.csv"
OUTPUT_FILE = "finviz_minervini_tickers.csv"

FINVIZ_FILTERS = {
    "Market Cap.": "+Mid (over $2bln)",    # cap_midover
    "IPO Date": "More than 10 years ago",  # ipodate_more10
    "Average Volume": "Over 300K",         # sh_avgvol_o300
    "Price": "Over $7",                    # sh_price_o7
}

SCREENER_CONFIGS = [
    ("technical", "Technical", Technical),
    ("overview", "Overview", Overview),
    ("valuation", "Valuation", Valuation),
    ("financial", "Financial", Financial),
    ("ownership", "Ownership", Ownership),
]

BASIC_COLUMNS = ["Ticker", "Company", "Sector", "Industry"]
PRICE_COLUMNS = ["Price", "Change", "Market Cap"]
VOLUME_VARIANTS = [
    "Avg Volume",
    "AvgVolume",
    "Avg. Volume",
    "Average Volume",
    "Avg Vol",
    "Volume",
]
EARNINGS_GROWTH_VARIANTS = [
    "EPS growth this year",
    "EPS Growth",
    "EPS growth past 5 years",
    "EPS Growth (ttm)",
    "EPS Growth Y/Y",
    "EPS growth next year",
    "EPS (ttm)",
    "EPS growth next 5 years",
    "EPS Q/Q",
    "EPS Y/Y",
]
SALES_GROWTH_VARIANTS = [
    "Sales growth past 5 years",
    "Sales Growth",
    "Sales Q/Q",
    "Sales Y/Y",
    "Revenue Growth",
    "Sales growth this year",
    "Sales growth next year",
]
PROFITABILITY_VARIANTS = [
    "ROE",
    "ROI",
    "ROA",
    "Gross Margin",
    "Oper. Margin",
    "Profit Margin",
    "Operating Margin",
    "Net Margin",
]
VALUATION_VARIANTS = [
    "P/E",
    "Forward P/E",
    "PEG",
    "P/S",
    "P/B",
    "P/C",
    "P/FCF",
    "EPS (ttm)",
    "EPS next Y",
    "EPS next 5Y",
    "Book/sh",
]
OWNERSHIP_VARIANTS = [
    "Institutional Ownership",
    "Inst Own",
    "Institutional Own",
    "Inst. Own",
    "Insider Own",
    "Insider Owner",
    "Insider Ownership",
    "Insider Own.",
]
TARGET_PRICE_VARIANTS = ["Target Price", "Price Target", "Analyst Target", "Target"]
TECHNICAL_VARIANTS = [
    "Beta",
    "RSI (14)",
    "RSI",
    "Perf Week",
    "Perf Month",
    "Perf Quarter",
    "Perf Half Y",
    "Perf Year",
    "Perf YTD",
    "Volatility",
    "Volatility (Month)",
    "SMA20",
    "SMA50",
    "SMA200",
    "50-Day Simple Moving Average",
    "200-Day Simple Moving Average",
    "Recom",
    "Rel Volume",
]
ADDITIONAL_VARIANTS = [
    "Debt/Eq",
    "Current Ratio",
    "Quick Ratio",
    "LT Debt/Eq",
    "Dividend %",
    "Payout",
    "Income",
    "Employees",
    "Optionable",
    "Shortable",
    "Short Ratio",
    "Short Interest",
]

COLUMN_GROUPS = [
    ("Earnings growth metrics", EARNINGS_GROWTH_VARIANTS),
    ("Sales growth metrics", SALES_GROWTH_VARIANTS),
    ("Profitability metrics", PROFITABILITY_VARIANTS),
    ("Valuation metrics", VALUATION_VARIANTS),
    ("Ownership metrics", OWNERSHIP_VARIANTS),
]

POST_TARGET_COLUMN_GROUPS = [
    ("Technical indicators", TECHNICAL_VARIANTS),
    ("Additional metrics", ADDITIONAL_VARIANTS),
]

MINERVINI_CRITERIA = {
    "Earnings Growth": lambda df: [
        col for col in df.columns if "EPS" in col and "growth" in col.lower()
    ],
    "Sales Growth": lambda df: [
        col for col in df.columns if "Sales" in col and "growth" in col.lower()
    ],
    "ROE": lambda df: ["ROE"] if "ROE" in df.columns else [],
    "Institutional Ownership": lambda df: [
        col
        for col in df.columns
        if "institutional" in col.lower() or "inst" in col.lower()
    ],
    "Price Performance": lambda df: [
        col
        for col in df.columns
        if "perf" in col.lower() or "performance" in col.lower()
    ],
}


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
    if use_cache and os.path.exists(CACHE_FILE):
        df = load_cached_screener_data(CACHE_FILE)
        return save_selected_columns(df, OUTPUT_FILE)

    screeners_data = fetch_all_screeners(FINVIZ_FILTERS)
    if not screeners_data:
        print("ERROR: No screener data was successfully fetched.")
        return pd.DataFrame()

    df = merge_screener_data(screeners_data)
    if df.empty:
        return pd.DataFrame()

    print_combined_dataset_summary(df)
    df.to_csv(CACHE_FILE, index=False)
    print(f"\nRaw data saved to cache: {CACHE_FILE}")

    return save_selected_columns(df, OUTPUT_FILE)


def load_cached_screener_data(cache_file):
    print(f"Loading from cache file: {cache_file}")
    df = pd.read_csv(cache_file)
    print(f"Cache contains {len(df)} tickers with columns: {', '.join(df.columns)}")
    return df


def save_selected_columns(df, output_file):
    filtered_df = select_desired_columns(df)
    filtered_df.to_csv(output_file, index=False)
    print(f"Filtered tickers saved to: {output_file}")
    return filtered_df


def fetch_all_screeners(filters_dict):
    print("=" * 60)
    print("Fetching data from Finviz screeners")
    print("=" * 60)

    screeners_data = {}
    for index, (name, display_name, screener_cls) in enumerate(SCREENER_CONFIGS, 1):
        df = fetch_screener_data(index, display_name, screener_cls, filters_dict)
        if df is not None:
            screeners_data[name] = df
    return screeners_data


def fetch_screener_data(index, display_name, screener_cls, filters_dict):
    print(f"{index}. Fetching {display_name} screener data...")
    try:
        screener = screener_cls()
        screener.set_filter(filters_dict=filters_dict)
        df = screener.screener_view()
        print(f"   {display_name} screener returned {len(df)} stocks")
        print(f"   Columns: {', '.join(df.columns)}")
        return df
    except Exception as e:
        print(f"   ERROR: {display_name} screener failed: {e}")
        return None


def merge_screener_data(screeners_data):
    print("\n" + "=" * 60)
    print("Combining screener data")
    print("=" * 60)

    base_name, base_df = find_base_screener(screeners_data)
    if base_df is None:
        print("ERROR: No valid base dataframe found.")
        return pd.DataFrame()

    for name, df in screeners_data.items():
        if name == base_name or df is None or len(df) == 0:
            continue
        base_df = merge_single_screener(base_df, name, df)

    return base_df


def find_base_screener(screeners_data):
    for name, df in screeners_data.items():
        if df is not None and len(df) > 0:
            print(f"Using {name} screener as base with {len(df)} stocks")
            return name, df.copy()
    return None, None


def merge_single_screener(base_df, name, df):
    print(f"\nMerging {name} screener data...")

    base_tickers = set(base_df["Ticker"].tolist())
    merge_tickers = set(df["Ticker"].tolist())
    common_tickers = base_tickers.intersection(merge_tickers)

    print(f"   Base has {len(base_tickers)} tickers, {name} has {len(merge_tickers)} tickers")
    print(f"   Common tickers: {len(common_tickers)}")

    try:
        merged_df = pd.merge(base_df, df, on="Ticker", how="outer", suffixes=("", f"_{name}"))
        duplicate_columns = [col for col in merged_df.columns if col.endswith(f"_{name}")]
        if duplicate_columns:
            merged_df = merged_df.drop(columns=duplicate_columns)
            print(f"   Dropped duplicate columns: {', '.join(duplicate_columns)}")

        print(
            "   Merge complete. Combined dataframe now has "
            f"{len(merged_df)} rows and {len(merged_df.columns)} columns"
        )
        return merged_df
    except Exception as e:
        print(f"   ERROR: Failed to merge {name} screener: {e}")
        return base_df


def print_combined_dataset_summary(df):
    print("\nCombined dataset:")
    print(f"   Total stocks: {len(df)}")
    print(f"   Total columns: {len(df.columns)}")
    print(f"   All columns: {', '.join(sorted(df.columns))}")


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
    print("Selecting Minervini-style growth stock columns")
    print("=" * 60)

    columns_to_keep = []

    add_required_columns(columns_to_keep, df, BASIC_COLUMNS)
    add_required_columns(columns_to_keep, df, PRICE_COLUMNS)
    add_first_matching_column(columns_to_keep, df, VOLUME_VARIANTS, "Average Volume")
    add_column_groups(columns_to_keep, df)
    add_target_price_column(columns_to_keep, df)
    add_column_groups(columns_to_keep, df, POST_TARGET_COLUMN_GROUPS)

    filtered_df = build_filtered_dataframe(df, columns_to_keep)
    print_filtered_summary(filtered_df)
    return filtered_df


def add_required_columns(columns_to_keep, df, candidates):
    for column in candidates:
        if column in df.columns:
            columns_to_keep.append(column)
            print(f"Found: {column}")
        else:
            print(f"Missing: {column}")


def add_first_matching_column(columns_to_keep, df, candidates, label):
    for column in candidates:
        if column in df.columns:
            columns_to_keep.append(column)
            print(f"Found: {label} (as '{column}')")
            return
    print(f"Missing: {label}")


def add_column_groups(columns_to_keep, df, column_groups=COLUMN_GROUPS):
    for title, candidates in column_groups:
        print(f"\n{title}:")
        add_existing_columns(columns_to_keep, df, candidates)


def add_existing_columns(columns_to_keep, df, candidates):
    for column in candidates:
        if column in df.columns:
            columns_to_keep.append(column)
            print(f"Found: {column}")


def add_target_price_column(columns_to_keep, df):
    print("\nTarget price:")
    for column in TARGET_PRICE_VARIANTS:
        if column in df.columns:
            columns_to_keep.append(column)
            print(f"Found: {column}")
            return
    print("Missing: Target Price")


def build_filtered_dataframe(df, columns_to_keep):
    if not columns_to_keep:
        print("WARNING: Could not find any of the desired columns. Keeping all columns.")
        return df

    selected_columns = list(dict.fromkeys(columns_to_keep))
    filtered_df = df[selected_columns]

    print(f"\nSelected columns ({len(selected_columns)} total):")
    for index, column in enumerate(selected_columns, 1):
        print(f"   {index:2d}. {column}")

    return filtered_df


def print_filtered_summary(filtered_df):
    if "Ticker" not in filtered_df.columns:
        return

    tickers = filtered_df["Ticker"].tolist()
    print("\nSummary:")
    print(f"   Total stocks found: {len(tickers)}")
    print(f"   Total data columns: {len(filtered_df.columns)}")

    if tickers:
        example_tickers = tickers[:10] if len(tickers) >= 10 else tickers
        print(f"   Example tickers: {', '.join(example_tickers)}")
        if len(tickers) > 10:
            print(f"   ... and {len(tickers) - 10} more")


def analyze_minervini_criteria(df):
    """
    Analyze the dataset for Mark Minervini's key criteria.
    This function helps identify which stocks meet his growth criteria.
    """
    print("\n" + "=" * 60)
    print("Mark Minervini criteria analysis")
    print("=" * 60)

    if df.empty:
        print("No data to analyze")
        return

    print(f"Total stocks in dataset: {len(df)}")

    available_criteria = []
    for criterion, selector in MINERVINI_CRITERIA.items():
        matching_columns = selector(df)
        if matching_columns:
            print(f"Available: {criterion} data ({', '.join(matching_columns)})")
            available_criteria.append(criterion)
        else:
            print(f"Missing: {criterion} data")

    print_minervini_coverage(available_criteria)
    return available_criteria


def print_minervini_coverage(available_criteria):
    expected_criteria = set(MINERVINI_CRITERIA.keys())
    missing_criteria = expected_criteria - set(available_criteria)

    print(f"\nMinervini criteria coverage: {len(available_criteria)}/5")
    print("   Available:", ", ".join(available_criteria))
    if missing_criteria:
        print("   Missing:", ", ".join(missing_criteria))


if __name__ == "__main__":
    print("Enhanced Finviz screener for Mark Minervini growth stocks")
    print("=" * 70)

    result_df = get_finviz_tickers_with_filters(use_cache=True)

    if not result_df.empty:
        analyze_minervini_criteria(result_df)

        print(f"\nSUCCESS: Found {len(result_df)} stocks matching the configured criteria.")
        print("Files created:")
        print(f"   - {CACHE_FILE} (full raw data)")
        print(f"   - {OUTPUT_FILE} (filtered for growth analysis)")
    else:
        print("No data was retrieved. Please check your internet connection and try again.")
