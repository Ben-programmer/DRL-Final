import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from agent.dqn_agent import DQNAgent
from config import Config
from env.trading_env import TradingEnv
from utils.data_utils import load_and_prepare_data

warnings.filterwarnings("ignore", category=FutureWarning)


def get_last_state_info(cfg: Config) -> tuple[float, int]:
    """Retrieves the last balance and shares_held from action_log.json if exists."""
    action_log_path = cfg.outputs_dir / "action_log.json"
    if action_log_path.exists():
        with open(action_log_path, "r", encoding="utf-8") as f:
            log = json.load(f)
            if log:
                return float(log[-1]["balance"]), int(log[-1]["shares_held"])
    return float(cfg.initial_balance), 0


def calculate_thresholds(df: pd.DataFrame, window: int) -> tuple[float, float, float]:
    """
    Returns (range_low, range_high, current_price) to find thresholds.
    Discount threshold = range_low + (range_high - range_low) * 0.5
    """
    last_window = df.tail(window)
    range_high = last_window["high"].max()
    range_low = last_window["low"].min()
    current_price = df.iloc[-1]["close"]
    
    # To be in discount, pd_pos < 0.5. 
    # pd_pos = (price - range_low) / (range_high - range_low)
    # 0.5 = (mid_price - range_low) / (range_high - range_low)
    mid_price = range_low + (range_high - range_low) * 0.5
    
    return range_low, range_high, current_price, mid_price


def simulate_scenario(df: pd.DataFrame, cfg: Config, agent: DQNAgent, 
                      start_balance: float, start_shares: int, daily_change: float) -> list[str]:
    """Simulates 7 days into the future given a daily price change percentage."""
    actions_map = {0: "HOLD", 1: "BUY", 2: "SELL"}
    sim_df = df.copy()
    
    last_row = sim_df.iloc[-1]
    current_price = last_row["close"]
    
    sim_balance = start_balance
    sim_shares = start_shares
    
    predictions = []
    
    for i in range(1, 8):
        new_price = current_price * (1 + daily_change) ** i
        # Create a fake new row
        new_row = last_row.copy()
        new_row["open"] = new_price
        new_row["high"] = new_price
        new_row["low"] = new_price
        new_row["close"] = new_price
        
        # We need to append and recalculate pd_pos for the last window
        sim_df = pd.concat([sim_df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Recalculate rolling stats for the new row
        window_df = sim_df.tail(cfg.rolling_window)
        r_high = window_df["high"].max()
        r_low = window_df["low"].min()
        
        pd_pos = (new_price - r_low) / (r_high - r_low + 1e-8)
        sim_df.at[sim_df.index[-1], "pd_pos"] = pd_pos
        sim_df.at[sim_df.index[-1], "is_premium"] = 1 if pd_pos > 0.5 else 0
        sim_df.at[sim_df.index[-1], "is_discount"] = 1 if pd_pos <= 0.5 else 0
        
        # Normalized price (approximate, using the min/max of the whole df so far)
        sim_df.at[sim_df.index[-1], "close_norm"] = (new_price - sim_df["close"].min()) / (sim_df["close"].max() - sim_df["close"].min() + 1e-8)

        # Build state manually
        equity = sim_balance + sim_shares * new_price
        state = np.array([
            sim_df.iloc[-1]["close_norm"],
            pd_pos,
            sim_df.iloc[-1]["is_premium"],
            sim_df.iloc[-1]["is_discount"],
            sim_balance / cfg.initial_balance,
            (sim_shares * new_price) / max(equity, 1e-8),
            equity / cfg.initial_balance
        ], dtype=np.float32)
        
        action = int(agent.select_action(state, greedy=True))
        predictions.append(f"Day {i} (Price: {new_price:.2f}): {actions_map[action]}")
        
        # Execute action on sim balance
        if action == 1 and sim_balance > 0: # BUY
            max_shares = int(sim_balance // (new_price * (1 + cfg.transaction_cost_rate)))
            if max_shares > 0:
                cost = max_shares * new_price
                fee = cost * cfg.transaction_cost_rate
                sim_balance -= (cost + fee)
                sim_shares += max_shares
        elif action == 2 and sim_shares > 0: # SELL
            revenue = sim_shares * new_price
            fee = revenue * cfg.transaction_cost_rate
            sim_balance += (revenue - fee)
            sim_shares = 0
            
    return predictions


def main():
    cfg = Config()
    
    print("\n" + "="*50)
    print("📈 PD-RL 未來 7 天操作建議分析報告")
    print("="*50)
    
    # 1. Load Data and Agent
    try:
        df = load_and_prepare_data(str(cfg.data_path), rolling_window=cfg.rolling_window)
        agent = DQNAgent(
            state_dim=cfg.state_dim,
            action_dim=cfg.action_dim,
            gamma=cfg.gamma,
            lr=cfg.lr,
            epsilon_start=cfg.epsilon_start,
            epsilon_decay=cfg.epsilon_decay,
            epsilon_min=cfg.epsilon_min,
        )
        agent.load(str(cfg.model_path))
    except Exception as e:
        print(f"[錯誤] 無法載入資料或模型: {e}")
        return

    # 2. Get current real state
    balance, shares = get_last_state_info(cfg)
    last_row = df.iloc[-1]
    current_price = last_row["close"]
    equity = balance + shares * current_price
    
    print(f"\n📊 【當前帳戶與市場狀態】")
    print(f"最新收盤價: {current_price:.2f}")
    print(f"目前現金餘額: {balance:.2f}")
    print(f"目前持股數量: {shares}")
    print(f"目前總權益: {equity:.2f}")
    print(f"當前 PD Array 位置: {last_row['pd_pos']:.2f} ({'Premium 溢價區' if last_row['is_premium'] else 'Discount 折價區'})")

    # 3. Predict Tomorrow
    state = np.array([
        last_row["close_norm"],
        last_row["pd_pos"],
        last_row["is_premium"],
        last_row["is_discount"],
        balance / cfg.initial_balance,
        (shares * current_price) / max(equity, 1e-8),
        equity / cfg.initial_balance
    ], dtype=np.float32)
    
    action = int(agent.select_action(state, greedy=True))
    actions_map = {0: "HOLD (持有)", 1: "BUY (買入)", 2: "SELL (賣出)"}
    print(f"\n🎯 【明日明確操作建議】: >>> {actions_map[action]} <<<")
    
    # 4. Calculate Thresholds
    range_low, range_high, curr_px, mid_price = calculate_thresholds(df, cfg.rolling_window)
    print(f"\n💡 【關鍵價位監控 (Threshold Triggers)】")
    print(f"近期 {cfg.rolling_window} 天區間: {range_low:.2f} ~ {range_high:.2f}")
    print(f"多空分界線 (中軸): {mid_price:.2f}")
    print(f"-> 若股價跌破 {mid_price:.2f}，將進入『折價區 (Discount)』，模型傾向【買入】。")
    print(f"-> 若股價突破 {mid_price:.2f}，將進入『溢價區 (Premium)』，模型傾向【賣出】。")
    
    # 5. Scenario Analysis
    print(f"\n🔮 【未來 7 天情境推演 (Scenario Analysis)】")
    
    print("\n[情境 A] 牛市延續 (假設每天上漲 1%)")
    bull_preds = simulate_scenario(df, cfg, agent, balance, shares, 0.01)
    for p in bull_preds: print("  " + p)
        
    print("\n[情境 B] 盤整震盪 (假設每天波動 0%)")
    flat_preds = simulate_scenario(df, cfg, agent, balance, shares, 0.0)
    for p in flat_preds: print("  " + p)
        
    print("\n[情境 C] 熊市回調 (假設每天下跌 1%)")
    bear_preds = simulate_scenario(df, cfg, agent, balance, shares, -0.01)
    for p in bear_preds: print("  " + p)

    print("\n" + "="*50)


if __name__ == "__main__":
    main()
