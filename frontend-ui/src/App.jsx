import React, { useState } from 'react';
import Papa from 'papaparse';
import KLineChart from './components/KLineChart';
import TrainingMonitor from './components/TrainingMonitor';
import ReportPanel from './components/ReportPanel';
import { Play, RotateCcw, Upload, FileText } from 'lucide-react';
import './App.css';

const APP_STATE = {
  IDLE: 'IDLE',
  DATA_LOADED: 'DATA_LOADED',
  DRAWING_CHART: 'DRAWING_CHART',
  CHART_DONE: 'CHART_DONE',
  TRAINING: 'TRAINING',
  COMPLETED: 'COMPLETED'
};

function App() {
  const [appState, setAppState] = useState(APP_STATE.IDLE);
  const [data, setData] = useState([]);
  const [dataSource, setDataSource] = useState('');

  // 1. 載入資料
  const loadSampleData = async () => {
    try {
      const response = await fetch('/sample_data.csv');
      const csvText = await response.text();
      parseCSV(csvText, 'sample_data.csv');
    } catch (error) {
      console.error("載入預設資料失敗", error);
      alert("載入預設資料失敗");
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      parseCSV(event.target.result, file.name);
    };
    reader.readAsText(file);
    // 重置 input 以允許重複上傳相同檔案
    e.target.value = null;
  };

  const parseCSV = (csvText, sourceName) => {
    Papa.parse(csvText, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        // 簡單驗證欄位
        if (!results.data || results.data.length === 0) {
          alert('CSV 資料為空');
          return;
        }
        const firstRow = results.data[0];
        
        // 取得 key 時忽略大小寫
        const getVal = (row, key) => {
          const foundKey = Object.keys(row).find(k => k.toLowerCase() === key.toLowerCase());
          return row[foundKey];
        };

        if (!getVal(firstRow, 'date') || !getVal(firstRow, 'open') || !getVal(firstRow, 'high') || !getVal(firstRow, 'low') || !getVal(firstRow, 'close')) {
          alert('CSV 必須包含 Date, Open, High, Low, Close 欄位');
          return;
        }

        // 處理日期格式 (將 YYYY/M/D 或 YYYY/MM/DD 轉為 YYYY-MM-DD)
        const formatDate = (dateStr) => {
          if (!dateStr) return '';
          if (dateStr.includes('/')) {
            const parts = dateStr.split('/');
            if (parts.length === 3) {
              const y = parts[0];
              const m = parts[1].padStart(2, '0');
              const d = parts[2].padStart(2, '0');
              return `${y}-${m}-${d}`;
            }
          }
          return dateStr;
        };

        // 轉換為 lightweight-charts 格式: { time: '2024-01-01', open, high, low, close }
        const chartData = results.data.map(row => ({
          time: formatDate(getVal(row, 'date')),
          open: parseFloat(getVal(row, 'open')),
          high: parseFloat(getVal(row, 'high')),
          low: parseFloat(getVal(row, 'low')),
          close: parseFloat(getVal(row, 'close'))
        })).filter(row => !isNaN(row.close) && row.time !== ''); // 過濾掉異常行

        setData(chartData);
        setDataSource(sourceName);
        setAppState(APP_STATE.DATA_LOADED);
      }
    });
  };

  // 2. 開始流程
  const handleStartProcess = () => {
    if (appState !== APP_STATE.DATA_LOADED && appState !== APP_STATE.COMPLETED) return;
    setAppState(APP_STATE.DRAWING_CHART);
    
    // 動畫時間固定約為 2000ms
    const animationTime = 2000;
    setTimeout(() => {
      setAppState(APP_STATE.CHART_DONE);
      // 接著開始訓練
      setTimeout(() => {
        setAppState(APP_STATE.TRAINING);
      }, 1000);
    }, animationTime + 500);
  };

  const handleTrainingComplete = () => {
    setAppState(APP_STATE.COMPLETED);
  };

  // 3. 初始化
  const handleReset = () => {
    setAppState(APP_STATE.IDLE);
    setData([]);
    setDataSource('');
  };

  return (
    <div className="app-container">
      {/* Header & Controls */}
      <header className="header">
        <div className="header-title">PD Array & DRL Prediction Platform</div>
        <div className="controls">
          <select 
            className="btn" 
            style={{ width: 'auto' }}
            value={dataSource}
            onChange={(e) => {
              if (e.target.value === 'sample') loadSampleData();
              else if (e.target.value === '') handleReset();
            }}
            disabled={appState !== APP_STATE.IDLE && appState !== APP_STATE.DATA_LOADED && appState !== APP_STATE.COMPLETED}
          >
            <option value="">選擇資料來源...</option>
            <option value="sample">sample_data.csv</option>
          </select>

          <div className="file-upload-wrapper" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative' }}>
            <button className="btn" disabled={appState !== APP_STATE.IDLE && appState !== APP_STATE.DATA_LOADED && appState !== APP_STATE.COMPLETED}>
              <Upload size={16} /> 自行匯入檔案
            </button>
            <input 
              type="file" 
              accept=".csv" 
              onClick={(e) => {
                if (!window.confirm("【格式提醒】\n請確認您的 CSV 檔案「必須」包含以下欄位：\nDate, Open, High, Low, Close\n\n大小寫皆可，若缺少這些欄位將無法繪圖。\n是否繼續上傳檔案？")) {
                  e.preventDefault();
                }
              }}
              onChange={handleFileUpload} 
              disabled={appState !== APP_STATE.IDLE && appState !== APP_STATE.DATA_LOADED && appState !== APP_STATE.COMPLETED}
            />
            {/* 提示訊息 */}
            <div style={{ position: 'absolute', top: '100%', left: '50%', transform: 'translateX(-50%)', marginTop: '4px', fontSize: '11px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
              必須包含: Date, Open, High, Low, Close
            </div>
          </div>

          <div style={{ width: '1px', height: '24px', background: 'var(--border-color)', margin: '0 8px', marginLeft: '16px' }}></div>

          <button 
            className="btn btn-primary" 
            onClick={handleStartProcess}
            disabled={appState === APP_STATE.IDLE || appState === APP_STATE.DRAWING_CHART || appState === APP_STATE.TRAINING}
          >
            <Play size={16} /> 開始 PD Array
          </button>
          
          <button 
            className="btn" 
            onClick={handleReset}
          >
            <RotateCcw size={16} /> 初始化
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="main-content">
        {/* Left Side: Chart & Terminal */}
        <div className="left-panel">
          <div className="chart-container">
            <div className="panel-title" style={{ marginBottom: '0', flexShrink: 0, paddingBottom: '12px' }}>
              <FileText size={16} />
              K 線圖與 PD Array
              {dataSource && <span style={{ fontSize: '12px', fontWeight: 'normal', color: 'var(--text-secondary)', marginLeft: 'auto' }}>資料: {dataSource}</span>}
            </div>
            <KLineChart 
              data={data} 
              showPDArray={appState === APP_STATE.CHART_DONE || appState === APP_STATE.TRAINING || appState === APP_STATE.COMPLETED}
              isDrawing={appState === APP_STATE.DRAWING_CHART}
            />
          </div>
          <div className="training-monitor">
            <TrainingMonitor 
              isTraining={appState === APP_STATE.TRAINING} 
              onComplete={handleTrainingComplete} 
            />
          </div>
        </div>

        {/* Right Side: KPIs & Predictions */}
        <ReportPanel showData={appState === APP_STATE.COMPLETED} data={data} />
      </div>
    </div>
  );
}

export default App;
