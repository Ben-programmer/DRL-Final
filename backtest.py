from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

from agent.dqn_agent import DQNAgent
from config import Config
from env.trading_env import TradingEnv
from utils.data_utils import load_and_prepare_data, split_data
from utils.metrics import compute_performance


def run_policy(env: TradingEnv, agent: DQNAgent):
    state = env.reset()
    done = False

    equity_curve = [env.initial_balance]
    action_log = []

    while not done:
        action = agent.select_action(state, greedy=True)
        next_state, reward, done, info = env.step(action)
        equity_curve.append(info["equity"])
        action_log.append(
            {
                "date": info["date"],
                "action": int(action),
                "price": info["price"],
                "equity": info["equity"],
                "balance": info["balance"],
                "shares_held": info["shares_held"],
                "pd_pos": info["pd_pos"],
                "is_premium": info["is_premium"],
                "is_discount": info["is_discount"],
                "reward": reward,
            }
        )
        state = next_state

    return equity_curve, action_log


def run_buy_and_hold(env: TradingEnv):
    state = env.reset()
    done = False

    first_price = float(env.data.iloc[0]["close"])
    max_shares = int(env.balance // (first_price * (1 + env.transaction_cost_rate)))
    if max_shares > 0:
        gross = max_shares * first_price
        cost = gross * env.transaction_cost_rate
        env.balance -= gross + cost
        env.shares_held += max_shares

    equity_curve = [env.initial_balance]
    while not done:
        _, _, done, info = env.step(0)  # hold
        equity_curve.append(info["equity"])

    return equity_curve


def main() -> None:
    cfg = Config()
    cfg.outputs_dir.mkdir(parents=True, exist_ok=True)

    df = load_and_prepare_data(str(cfg.data_path), rolling_window=cfg.rolling_window)
    _, _, test_df = split_data(df, cfg.train_ratio, cfg.val_ratio, cfg.test_ratio)

    test_env = TradingEnv(
        data=test_df,
        initial_balance=cfg.initial_balance,
        transaction_cost_rate=cfg.transaction_cost_rate,
        pd_bonus=cfg.pd_bonus,
        reward_scale=cfg.reward_scale,
    )

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

    equity_curve, action_log = run_policy(test_env, agent)
    policy_metrics = compute_performance(equity_curve)

    buy_hold_env = TradingEnv(
        data=test_df,
        initial_balance=cfg.initial_balance,
        transaction_cost_rate=cfg.transaction_cost_rate,
        pd_bonus=cfg.pd_bonus,
        reward_scale=cfg.reward_scale,
    )
    bh_curve = run_buy_and_hold(buy_hold_env)
    bh_metrics = compute_performance(bh_curve)

    with open(cfg.outputs_dir / "backtest_metrics.json", "w", encoding="utf-8") as f:
        json.dump(
            {"pd_rl_policy": policy_metrics, "buy_and_hold": bh_metrics},
            f,
            ensure_ascii=False,
            indent=2,
        )

    with open(cfg.outputs_dir / "action_log.json", "w", encoding="utf-8") as f:
        json.dump(action_log, f, ensure_ascii=False, indent=2)

    plt.figure(figsize=(10, 5))
    plt.plot(equity_curve, label="PD-RL Policy")
    plt.plot(bh_curve, label="Buy and Hold")
    plt.title("Equity Curve Comparison")
    plt.xlabel("Step")
    plt.ylabel("Equity")
    plt.legend()
    plt.tight_layout()
    plt.savefig(cfg.outputs_dir / "equity_curve.png", dpi=150)
    plt.close()

    print("PD-RL Policy Metrics:")
    for k, v in policy_metrics.items():
        print(f"  {k}: {v:.6f}")

    print("Buy and Hold Metrics:")
    for k, v in bh_metrics.items():
        print(f"  {k}: {v:.6f}")

    print(f"Artifacts saved in: {cfg.outputs_dir}")


if __name__ == "__main__":
    main()
