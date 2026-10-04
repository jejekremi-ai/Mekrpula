import { useEffect, useRef, useState } from 'react';
import { createChart, CandlestickSeries, HistogramSeries } from 'lightweight-charts';
import { RefreshCw, BarChart3 } from 'lucide-react';
import { useData } from '../../lib/api';

export const TokenPriceChart = ({ token }) => {
  const [interval, setInterval] = useState('1h');
  const { data, loading, error, reload } = useData(`/tokens/${token.address}/ohlcv?interval=${interval}`);
  const container = useRef(null);
  useEffect(() => {
    if (!container.current || !data?.candles?.length || error) return;
    const last = data.candles[data.candles.length - 1].close;
    const precision = last > 1 ? 4 : Math.min(10, Math.max(4, Math.ceil(-Math.log10(last || .0001)) + 3));
    const chart = createChart(container.current, {
      autoSize: true,
      localization: { locale: 'en-US' },
      layout: { background: { color: '#0c1511' }, textColor: '#819b8b', fontFamily: 'IBM Plex Sans', fontSize: 10, attributionLogo: true },
      grid: { vertLines: { color: '#20342855' }, horzLines: { color: '#20342877' } },
      rightPriceScale: { borderColor: '#2d4434', scaleMargins: { top: .12, bottom: .2 } },
      timeScale: { borderColor: '#2d4434', timeVisible: interval !== '1d', secondsVisible: false },
      crosshair: { vertLine: { color: '#8aa592', labelBackgroundColor: '#365642' }, horzLine: { color: '#8aa592', labelBackgroundColor: '#365642' } },
      handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false },
    });
    const candles = chart.addSeries(CandlestickSeries, { upColor: '#36bd89', downColor: '#d27470', borderVisible: false, wickUpColor: '#36bd89', wickDownColor: '#d27470', priceFormat: { type: 'price', precision, minMove: 10 ** -precision } });
    candles.setData(data.candles.map(({ time, open, high, low, close }) => ({ time, open, high, low, close })));
    const volume = chart.addSeries(HistogramSeries, { priceFormat: { type: 'volume' }, priceScaleId: 'volume', lastValueVisible: false, priceLineVisible: false });
    volume.priceScale().applyOptions({ scaleMargins: { top: .86, bottom: 0 }, visible: false });
    volume.setData(data.candles.map(c => ({ time: c.time, value: c.volume, color: c.close >= c.open ? '#24583e' : '#6b3532' })));
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [data, error, interval]);
  return <div className="native-token-chart" data-testid="hub-native-chart">
    <div className="native-chart-toolbar"><strong data-testid="hub-chart-pair">${token.symbol} / USD</strong><div aria-label="Chart candle interval">{['15m', '1h', '4h', '1d'].map(v => <button key={v} type="button" data-testid={`hub-chart-interval-${v}`} aria-pressed={interval === v} className={interval === v ? 'active' : ''} onClick={() => setInterval(v)}>{v}</button>)}</div><button type="button" data-testid="hub-chart-refresh" title="Refresh chart" aria-label="Refresh chart" disabled={loading} onClick={reload}><RefreshCw size={13} /></button></div>
    <div className="native-chart-plot"><div ref={container} className="native-chart-canvas" data-testid="hub-chart-canvas" />{(loading || error || !data) && <div className="native-chart-state" data-testid={error ? 'hub-chart-error' : 'hub-chart-loading'}><BarChart3 size={27} /><p>{error || 'Loading price history…'}</p>{error && <button data-testid="hub-chart-retry" onClick={reload} className="text-link">Retry price history</button>}</div>}</div>
    <div className="native-chart-attribution"><a href="https://www.geckoterminal.com" target="_blank" rel="noopener noreferrer" data-testid="chart-geckoterminal-attribution">Data: GeckoTerminal ↗</a><a href="https://www.tradingview.com/" target="_blank" rel="noopener noreferrer" data-testid="chart-tradingview-attribution">TradingView Lightweight Charts™</a></div>
    {data && !error && <div className="native-chart-timestamp" data-testid="hub-chart-data-status">{data.candles.length} real candles · {new Date(data.fetched_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} · {data.cached ? 'cached ≤60s' : 'USD price history'}</div>}
  </div>;
};