import yfinance as yf
import pandas as pd
import os

CACHE_DIR = "data_cache"

def get_historical_data(tickers: list, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetches historical close prices for a list of tickers.
    Caches the data locally as CSV files to avoid yfinance rate limits.
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    tickers = sorted(list(set(tickers)))
    cache_key = "_".join(tickers) + f"_{start_date}_{end_date}.csv"
    cache_file = os.path.join(CACHE_DIR, cache_key)
    
    if os.path.exists(cache_file):
        print(f"Loading cached data from {cache_file}...")
        prices_df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
        return prices_df

    print(f"Downloading {tickers} from Yahoo Finance...")
    try:
        data = yf.download(tickers, start=start_date, end=end_date, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            if 'Close' in data.columns.levels[0]:
                prices_df = data['Close']
            elif 'Adj Close' in data.columns.levels[0]:
                prices_df = data['Adj Close']
            else:
                prices_df = data.iloc[:, :len(tickers)]
        else:
            prices_df = data.get('Close', data.get('Adj Close', data))
            
        if not prices_df.empty:
            prices_df = prices_df[tickers].dropna()
            prices_df.to_csv(cache_file)
            return prices_df
    except Exception as e:
        print(f"Error downloading market data: {e}")

    return pd.DataFrame()

if __name__ == "__main__":
    # Example usage: fetching data for a standard diversified portfolio
    tickers = ["SPY", "TLT", "GLD", "QQQ"]
    start = "2015-01-01"
    end = "2024-01-01"
    
    df = get_historical_data(tickers, start, end)
    print("Data loaded successfully.")
    print(df.head())
