import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import Config
from utils.data_utils import load_and_prepare_data


def draw_candlesticks(ax, df: pd.DataFrame):
    """Draws candlestick chart on the given matplotlib axes."""
    # 紅漲綠跌 (Red=Up, Green=Down)
    colors = np.where(df['close'] >= df['open'], 'red', 'green')
    
    x = np.arange(len(df))
    
    # Draw high/low shadows
    ax.vlines(x, df['low'], df['high'], color=colors, linewidth=1)
    
    # Draw open/close bodies
    # Use bar to draw bodies. Bottom is min(open, close), height is abs(close - open)
    bottoms = np.minimum(df['open'], df['close'])
    heights = np.abs(df['close'] - df['open'])
    # For doji (open == close), ensure a tiny height so it's visible
    heights = np.where(heights == 0, 0.5, heights)
    
    ax.bar(x, heights, bottom=bottoms, color=colors, width=0.6, align='center')
    return x


def overlay_pd_array(ax, x, df: pd.DataFrame):
    """Overlays PD Array boundaries and shading."""
    range_high = df['range_high'].values
    range_low = df['range_low'].values
    mid_price = (range_high + range_low) / 2.0
    
    # Plot the lines
    ax.plot(x, range_high, color='darkred', linestyle='--', alpha=0.6, label='Range High')
    ax.plot(x, range_low, color='darkgreen', linestyle='--', alpha=0.6, label='Range Low')
    ax.plot(x, mid_price, color='gray', linestyle=':', alpha=0.8, label='Equilibrium (0.5)')
    
    # Shade Premium (Reddish) and Discount (Greenish)
    ax.fill_between(x, mid_price, range_high, color='lightcoral', alpha=0.15, label='Premium Zone')
    ax.fill_between(x, range_low, mid_price, color='lightgreen', alpha=0.15, label='Discount Zone')


def overlay_actions(ax, x, df: pd.DataFrame, cfg: Config):
    """Loads action_log.json and overlays buy/sell markers."""
    action_log_path = cfg.outputs_dir / "action_log.json"
    if not action_log_path.exists():
        return
        
    try:
        with open(action_log_path, "r", encoding="utf-8") as f:
            actions = json.load(f)
    except Exception as e:
        print(f"Failed to load action_log.json: {e}")
        return
        
    # Create a mapping of date -> action
    # Actions: 0 = hold, 1 = buy, 2 = sell
    action_map = {item['date']: item['action'] for item in actions}
    
    buy_x, buy_y = [], []
    sell_x, sell_y = [], []
    
    for i, (_, row) in enumerate(df.iterrows()):
        date_str = str(row['date'])
        if date_str in action_map:
            action = action_map[date_str]
            if action == 1:
                buy_x.append(x[i])
                buy_y.append(row['low'] * 0.98) # slightly below low
            elif action == 2:
                sell_x.append(x[i])
                sell_y.append(row['high'] * 1.02) # slightly above high
                
    if buy_x:
        ax.scatter(buy_x, buy_y, marker='^', color='magenta', s=100, label='BUY Agent', zorder=5)
    if sell_x:
        ax.scatter(sell_x, sell_y, marker='v', color='blue', s=100, label='SELL Agent', zorder=5)


def main():
    cfg = Config()
    
    try:
        df = load_and_prepare_data(str(cfg.data_path), rolling_window=cfg.rolling_window)
    except Exception as e:
        print(f"Failed to load data: {e}")
        return
        
    # Get the last 150 days
    LOOKBACK = 150
    df_subset = df.tail(LOOKBACK).copy()
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # 1. Draw K-line
    x = draw_candlesticks(ax, df_subset)
    
    # 2. Overlay PD Array
    overlay_pd_array(ax, x, df_subset)
    
    # 3. Overlay Agent Actions
    overlay_actions(ax, x, df_subset, cfg)
    
    # 4. Format plot
    # Set x-ticks to display dates nicely (every 10 days)
    step = max(1, len(x) // 15)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(df_subset['date'].dt.strftime('%Y-%m-%d').iloc[::step], rotation=45, ha='right')
    
    ax.set_title(f"PD Array & K-line Chart (Last {LOOKBACK} Days)")
    ax.set_ylabel("Price")
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 5. Save the output
    out_path = cfg.outputs_dir / "kline_pd_array.png"
    plt.savefig(out_path, dpi=200)
    print(f"K-line chart successfully saved to: {out_path}")


if __name__ == "__main__":
    main()
