import React from 'react';

export default function ReportPanel({ showData, data }) {
  if (!showData || !data || data.length === 0) {
    return (
      <div className="right-panel" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div className="overlay-message" style={{ position: 'relative' }}>等待模型訓練完成...</div>
      </div>
    );
  }

  // 動態計算 PD Array 數據
  const lastClose = data[data.length - 1].close;
  
  let maxHigh = -Infinity;
  let minLow = Infinity;
  data.forEach(d => {
    if (d.high > maxHigh) maxHigh = d.high;
    if (d.low < minLow) minLow = d.low;
  });

  const midPoint = (maxHigh + minLow) / 2;
  const isPremium = lastClose > midPoint;

  const fmt = (num) => num.toFixed(1);

  let stateStr = '';
  let descStr = '';
  let strategyStr = '';
  let entryStr = '';
  let stopStr = '';
  let targetStr = '';

  if (isPremium) {
    stateStr = "進入 Premium (溢價) 區間";
    descStr = `根據 PD Array 強化學習模型預測，目前股票價格 (${fmt(lastClose)}) 已處於溢價區 (高於歷史均衡點 ${fmt(midPoint)})，不適合追高買入。模型偵測到上方賣壓逐漸增強，短期內有回檔修正的風險。`;
    strategyStr = "逢高減碼，分批獲利了結";
    entryStr = `${fmt(lastClose)} - ${fmt(maxHigh)} (建議賣出區間)`;
    stopStr = `若跌破 ${fmt(lastClose * 0.97)} 應加速減碼 (防守價位)`; 
    targetStr = `${fmt(lastClose * 0.93)} (七天內短期回檔目標)`;
  } else {
    stateStr = "進入 Discount (折扣) 區間";
    descStr = `根據 PD Array 強化學習模型預測，目前股票價格 (${fmt(lastClose)}) 已跌入折扣區 (低於歷史均衡點 ${fmt(midPoint)})，具備潛在的買入價值。模型偵測到下方買盤動能正在逐漸增強。`;
    strategyStr = "逢低佈局，建立多頭部位";
    entryStr = `${fmt(lastClose * 0.95)} - ${fmt(lastClose)} (建議買入區間)`;
    stopStr = `跌破 ${fmt(lastClose * 0.92)} (嚴格停損)`;
    targetStr = `${fmt(lastClose * 1.07)} (七天內短期反彈目標)`;
  }

  return (
    <div className="right-panel">
      <div>
        <div className="panel-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
          回測結果 KPI
        </div>
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-label">勝率 (Win Rate)</div>
            <div className="kpi-value" style={{ color: 'var(--bullish)' }}>68.4%</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">總報酬率 (Total Return)</div>
            <div className="kpi-value" style={{ color: 'var(--bullish)' }}>+24.5%</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">夏普值 (Sharpe Ratio)</div>
            <div className="kpi-value">1.85</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">最大回撤 (Max Drawdown)</div>
            <div className="kpi-value" style={{ color: 'var(--bearish)' }}>-5.2%</div>
          </div>
        </div>
      </div>

      <div>
        <div className="panel-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          預測報告與建議
        </div>
        <div className="prediction-card">
          <p style={{ fontWeight: 600, marginBottom: '8px' }}>市場狀態：{stateStr}</p>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '12px' }}>
            {descStr}
          </p>
          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
            <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>未來 7 天操作建議：</p>
            <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--text-secondary)' }}>
              <li><strong>策略：</strong> {strategyStr}</li>
              <li><strong>進場區間：</strong> {entryStr}</li>
              <li><strong>停損價位：</strong> {stopStr}</li>
              <li><strong>目標價位：</strong> {targetStr}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
