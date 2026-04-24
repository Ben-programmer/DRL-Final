import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

export default function KLineChart({ data, showPDArray, isDrawing }) {
  const chartContainerRef = useRef(null);
  const chartInstanceRef = useRef(null);
  const seriesRef = useRef(null);
  const pdArraySeriesRef = useRef([]);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 建立圖表
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: 'solid', color: '#ffffff' },
        textColor: '#1a1b1e',
      },
      grid: {
        vertLines: { color: '#e5e7eb' },
        horzLines: { color: '#e5e7eb' },
      },
      timeScale: {
        borderColor: '#e5e7eb',
      },
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: '#e5e7eb',
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#ef4444',     // 紅漲
      downColor: '#22c55e',   // 綠跌
      borderVisible: false,
      wickUpColor: '#ef4444',
      wickDownColor: '#22c55e',
    });

    chartInstanceRef.current = chart;
    seriesRef.current = candlestickSeries;

    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current.clientWidth });
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // 更新 K 線資料
  useEffect(() => {
    if (seriesRef.current && data.length > 0) {
      if (isDrawing) {
        // 動畫模擬繪製 K 線
        seriesRef.current.setData([]);
        let i = 0;
        const totalFrames = 60; // 固定在 60 幀內畫完
        const chunkSize = Math.max(1, Math.ceil(data.length / totalFrames)); 
        const intervalTime = Math.max(16, Math.floor(2000 / (data.length / chunkSize))); // 總時間約 2000ms

        const interval = setInterval(() => {
          if (i < data.length) {
            const chunk = data.slice(i, i + chunkSize);
            chunk.forEach(d => seriesRef.current.update(d));
            i += chunkSize;
          } else {
            clearInterval(interval);
          }
        }, intervalTime); 
        
        return () => clearInterval(interval);
      } else {
        seriesRef.current.setData(data);
      }
    } else if (seriesRef.current && data.length === 0) {
      seriesRef.current.setData([]);
    }
  }, [data, isDrawing]);

  // 繪製 PD Array
  useEffect(() => {
    if (!chartInstanceRef.current || !seriesRef.current) return;

    // 清除舊的 PD Array (PriceLines)
    pdArraySeriesRef.current.forEach(line => seriesRef.current.removePriceLine(line));
    pdArraySeriesRef.current = [];

    if (showPDArray && data.length > 0) {
      // 找出整段區間的最大最高價與最小最低價
      let maxHigh = -Infinity;
      let minLow = Infinity;
      data.forEach(d => {
        if (d.high > maxHigh) maxHigh = d.high;
        if (d.low < minLow) minLow = d.low;
      });

      const midPoint = (maxHigh + minLow) / 2;

      // 使用 createPriceLine，這樣就不會影響 Lightweight Charts 的自動縮放 (Auto-scaling)
      const premiumLine = seriesRef.current.createPriceLine({ price: maxHigh, color: '#ef4444', lineWidth: 2, title: 'Premium (Sell)', lineStyle: 2 });
      const midLine = seriesRef.current.createPriceLine({ price: midPoint, color: '#5c626e', lineWidth: 1, title: 'Equilibrium', lineStyle: 3 });
      const discountLine = seriesRef.current.createPriceLine({ price: minLow, color: '#22c55e', lineWidth: 2, title: 'Discount (Buy)', lineStyle: 2 });

      pdArraySeriesRef.current.push(premiumLine, midLine, discountLine);
    }
  }, [showPDArray, data]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <div ref={chartContainerRef} className="chart-wrapper" />
      {data.length === 0 && (
        <div className="overlay-message">請先選擇或匯入資料</div>
      )}
    </div>
  );
}
