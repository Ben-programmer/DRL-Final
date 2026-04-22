# PD-RL Trading MVP

A runnable MVP for a **PD Array + Reinforcement Learning** stock trading system.

## What this project does
- Loads OHLCV daily data from CSV
- Builds a simplified **PD Array** signal using a rolling dealing range
- Creates a trading environment with:
  - discrete actions: Hold / Buy / Sell
  - portfolio tracking
  - transaction cost
  - PD alignment reward
- Trains a **DQN** agent
- Runs backtesting on the test split
- Saves:
  - model weights
  - training reward curve
  - equity curve
  - performance metrics

## Project structure
```text
pd_rl_trading_mvp/
├── agent/
│   └── dqn_agent.py
├── data/
│   └── sample_data.csv
├── env/
│   └── trading_env.py
├── model/
│   └── network.py
├── outputs/
├── utils/
│   ├── data_utils.py
│   ├── metrics.py
│   └── replay_buffer.py
├── train.py
├── backtest.py
├── config.py
├── requirements.txt
└── README.md
```

## Install
```bash
pip install -r requirements.txt
```

## Run training
```bash
python train.py
```

## Run backtest
```bash
python backtest.py
```

## Input data format
Place your CSV in `data/` with these columns:

- `date`
- `open`
- `high`
- `low`
- `close`
- `volume`

Example:
```csv
date,open,high,low,close,volume
2023-01-02,100,102,99,101,1500000
2023-01-03,101,103,100,102,1600000
```

## PD Array logic in this MVP
This MVP uses a simplified rolling dealing range:

- `range_high_t = rolling max(high, N)`
- `range_low_t = rolling min(low, N)`
- `pd_pos_t = (close_t - range_low_t) / (range_high_t - range_low_t)`

Zones:
- `pd_pos_t > 0.5` → premium
- `pd_pos_t < 0.5` → discount

PD alignment reward:
- Buy in discount: positive bonus
- Sell in premium: positive bonus
- Buy in premium: penalty
- Sell in discount: penalty

## Notes
- This is an MVP for research and prototyping.
- It is **not** investment advice.
- Replace the sample data with real market data for meaningful evaluation.
