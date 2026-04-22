from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

from agent.dqn_agent import DQNAgent
from config import Config
from env.trading_env import TradingEnv
from utils.data_utils import load_and_prepare_data, set_seed, split_data
from utils.replay_buffer import ReplayBuffer


def main() -> None:
    cfg = Config()
    cfg.outputs_dir.mkdir(parents=True, exist_ok=True)
    set_seed(cfg.seed)

    df = load_and_prepare_data(str(cfg.data_path), rolling_window=cfg.rolling_window)
    train_df, val_df, test_df = split_data(df, cfg.train_ratio, cfg.val_ratio, cfg.test_ratio)

    env = TradingEnv(
        data=train_df,
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
    replay_buffer = ReplayBuffer(capacity=cfg.replay_capacity)

    episode_rewards = []
    episode_losses = []

    for episode in range(cfg.episodes):
        state = env.reset()
        done = False
        total_reward = 0.0
        losses = []

        while not done:
            action = agent.select_action(state)
            next_state, reward, done, _ = env.step(action)
            replay_buffer.push(state, action, reward, next_state, done)

            loss = agent.update(replay_buffer, batch_size=cfg.batch_size)
            if loss > 0:
                losses.append(loss)

            state = next_state
            total_reward += reward

        if (episode + 1) % cfg.target_update_freq == 0:
            agent.update_target()

        episode_rewards.append(total_reward)
        episode_losses.append(sum(losses) / len(losses) if losses else 0.0)
        print(
            f"Episode {episode + 1:03d}/{cfg.episodes} | "
            f"Reward: {total_reward:.4f} | "
            f"Avg Loss: {episode_losses[-1]:.6f} | "
            f"Epsilon: {agent.epsilon:.4f}"
        )

    agent.save(str(cfg.model_path))

    # Save split metadata
    meta = {
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "test_rows": len(test_df),
        "data_path": str(cfg.data_path),
    }
    with open(cfg.outputs_dir / "train_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Plot training rewards
    plt.figure(figsize=(10, 5))
    plt.plot(episode_rewards, label="Episode Reward")
    plt.title("Training Reward Curve")
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.legend()
    plt.tight_layout()
    plt.savefig(cfg.outputs_dir / "training_rewards.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(episode_losses, label="Average Loss")
    plt.title("Training Loss Curve")
    plt.xlabel("Episode")
    plt.ylabel("Loss")
    plt.legend()
    plt.tight_layout()
    plt.savefig(cfg.outputs_dir / "training_losses.png", dpi=150)
    plt.close()

    print(f"Model saved to: {cfg.model_path}")
    print(f"Artifacts saved in: {cfg.outputs_dir}")


if __name__ == "__main__":
    main()
