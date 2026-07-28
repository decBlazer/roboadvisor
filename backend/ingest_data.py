import yfinance as yf
import pandas as pd
import os

CACHE_DIR = "data_cache"

def get_historical_data(tickers: list, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetches historical adjusted close prices for a list of tickers.
    Caches the data locally as CSV files to avoid yfinance rate limits.
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    prices_dict = {}

    for ticker in tickers:
        cache_file = os.path.join(CACHE_DIR, f"{ticker}_{start_date}_{end_date}.csv")
        
        if os.path.exists(cache_file):
            print(f"Loading {ticker} from cache...")
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            prices_dict[ticker] = df['Adj Close']
        else:
            print(f"Downloading {ticker} from Yahoo Finance...")
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not data.empty:
                data.to_csv(cache_file)
                prices_dict[ticker] = data['Adj Close']
            else:
                print(f"Warning: No data found for {ticker}")

    if not prices_dict:
        return pd.DataFrame()

    prices_df = pd.DataFrame(prices_dict)
    prices_df.dropna(inplace=True)
    return prices_df

if __name__ == "__main__":
    # Example usage: fetching data for a standard diversified portfolio
    tickers = ["SPY", "TLT", "GLD", "QQQ"]
    start = "2015-01-01"
    end = "2024-01-01"
    
    df = get_historical_data(tickers, start, end)
    print("Data loaded successfully.")
    print(df.head())
