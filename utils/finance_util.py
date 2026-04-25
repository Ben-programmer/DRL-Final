import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker_symbol, start_date, end_date):
    """
    根據股票代號與時間區間抓取歷史資料
    """
    print(f"正在抓取 {ticker_symbol} 從 {start_date} 到 {end_date} 的資料...")
    
    try:
        # 建立 Ticker 物件
        stock = yf.Ticker(ticker_symbol)
        
        # 抓取歷史資料
        # yfinance 預設就會抓取 Open, High, Low, Close, Volume
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            return "查無資料，請確認股票代號或日期區間是否正確。"
            
        # 清理一下資料，讓它看起來更直覺 (移除不必要的欄位如 Dividends, Stock Splits)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        return df
        
    except Exception as e:
        return f"發生錯誤: {e}"

# --- 參考輸入 ---
# user_ticker = "2330.TW"  #(美股則直接輸入如 "AAPL"; 台股則加上 .TW ex: "2330.TW")
# user_start = "2025-05-01"
# user_end = "2026-4-25"

# result = fetch_stock_data(user_ticker, user_start, user_end)
# print(result)