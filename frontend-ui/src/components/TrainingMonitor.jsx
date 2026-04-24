import React, { useEffect, useState, useRef } from 'react';

const SIMULATED_LOGS = [
  "Initializing DRL Environment...",
  "Loading Market Data (State Space: OHLCV + PD Arrays)...",
  "Initializing PPO Agent...",
  "Starting Training Episode 1/10...",
  "Episode 1 | Loss: 0.84 | Reward: -1.2",
  "Episode 2 | Loss: 0.62 | Reward: 2.4",
  "Episode 3 | Loss: 0.45 | Reward: 5.1",
  "Episode 4 | Loss: 0.38 | Reward: 8.7",
  "Episode 5 | Loss: 0.31 | Reward: 12.3",
  "Episode 6 | Loss: 0.29 | Reward: 15.6",
  "Episode 7 | Loss: 0.25 | Reward: 18.2",
  "Episode 8 | Loss: 0.22 | Reward: 22.1",
  "Episode 9 | Loss: 0.20 | Reward: 25.8",
  "Episode 10 | Loss: 0.18 | Reward: 28.5",
  "Training Completed.",
  "Starting Backtest Validation...",
  "Backtest Completed. Generating Predictions..."
];

export default function TrainingMonitor({ isTraining, onComplete }) {
  const [logs, setLogs] = useState([]);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (!isTraining) {
      setLogs([]);
      return;
    }

    let currentLogIndex = 0;
    setLogs([]); // Reset

    const interval = setInterval(() => {
      if (currentLogIndex < SIMULATED_LOGS.length) {
        setLogs(prev => [...prev, SIMULATED_LOGS[currentLogIndex]]);
        currentLogIndex++;
      } else {
        clearInterval(interval);
        setTimeout(() => {
          onComplete();
        }, 1000);
      }
    }, 300); // 模擬每行日誌延遲

    return () => clearInterval(interval);
  }, [isTraining, onComplete]);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-title">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>
        PD RL 訓練模型動態
      </div>
      <div className="terminal-wrapper">
        {!isTraining && logs.length === 0 && (
          <div className="overlay-message" style={{ position: 'relative', height: '100%' }}>等待訓練開始...</div>
        )}
        {logs.map((log, idx) => (
          <div key={idx} className={`terminal-line ${idx === logs.length - 1 ? 'active' : ''}`}>
            {'>'} {log}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
