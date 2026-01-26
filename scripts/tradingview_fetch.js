/*
  TradingView bridge: fetch OHLCV via @mathieuc/tradingview
  Usage: node tradingview_fetch.js --symbol BINANCE:BTCUSDT --timeframe 60 --range 200
*/

const TradingView = require('@mathieuc/tradingview');

function getArg(flag, fallback) {
  const idx = process.argv.indexOf(flag);
  if (idx !== -1 && idx + 1 < process.argv.length) return process.argv[idx + 1];
  return fallback;
}

const symbol = getArg('--symbol', getArg('-s', null));
const timeframe = getArg('--timeframe', getArg('-t', 'D'));
const rangeStr = getArg('--range', getArg('-r', '200'));
const range = Number.parseInt(rangeStr, 10) || 200;

if (!symbol) {
  console.error('Missing --symbol');
  process.exit(2);
}

const clientOptions = {};
if (process.env.TRADINGVIEW_SESSION && process.env.TRADINGVIEW_SIGNATURE) {
  clientOptions.token = process.env.TRADINGVIEW_SESSION;
  clientOptions.signature = process.env.TRADINGVIEW_SIGNATURE;
}

const client = new TradingView.Client(clientOptions);
const chart = new client.Session.Chart();

let done = false;
const timeoutMs = Number.parseInt(process.env.TV_FETCH_TIMEOUT_MS || '15000', 10);

const finishWithError = (msg) => {
  if (done) return;
  done = true;
  console.error(msg);
  try { chart.delete(); } catch (e) {}
  try { client.end(); } catch (e) {}
  process.exit(1);
};

chart.onError((...err) => {
  finishWithError(`Chart error: ${err.join(' ')}`);
});

chart.onUpdate(() => {
  if (done) return;
  if (!chart.periods || chart.periods.length === 0) return;

  const periods = chart.periods.map((p) => ({
    time: p.time,
    open: p.open,
    high: p.max,
    low: p.min,
    close: p.close,
    volume: p.volume,
  }));

  const ordered = periods.sort((a, b) => a.time - b.time).slice(-range);
  const payload = {
    symbol,
    timeframe,
    periods: ordered,
  };

  done = true;
  console.log(JSON.stringify(payload));
  try { chart.delete(); } catch (e) {}
  try { client.end(); } catch (e) {}
  process.exit(0);
});

chart.setMarket(symbol, {
  timeframe,
  range,
});

setTimeout(() => {
  if (!done) finishWithError('Timed out waiting for TradingView data');
}, timeoutMs);
