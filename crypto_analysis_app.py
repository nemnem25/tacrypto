import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import numpy as np

st.set_page_config(layout="wide", page_title="Crypto TA App")

# ============================
# Fungsi ambil data dari Binance
# ============================
def get_klines(symbol="TRXUSDT", interval="1d", limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    r = requests.get(url, params=params)
    data = r.json()
    if not data or isinstance(data, dict):
        return pd.DataFrame()
    df = pd.DataFrame(data, columns=[
        'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
        'Close_time', 'Quote_asset_volume', 'Number_of_trades',
        'Taker_buy_base', 'Taker_buy_quote', 'Ignore'
    ])
    df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('Date', inplace=True)
    df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
    return df

# ============================
# Streamlit UI
# ============================
st.title("📈 Real-Time Crypto Technical Analysis")

symbol = st.text_input("Masukkan simbol kripto (contoh: BTCUSDT, ETHUSDT, TRXUSDT)", "TRXUSDT").upper()
interval = st.selectbox("Pilih interval waktu", ['1m', '5m', '15m', '1h', '4h', '1d', '1w'], index=5)
limit = st.slider("Jumlah data terakhir", min_value=50, max_value=500, value=100)

try:
    df = get_klines(symbol, interval, limit)
except Exception as e:
    st.error(f"Gagal mengambil data: {e}")
    st.stop()

if df.empty:
    st.error("⚠️ Tidak ada data yang tersedia untuk simbol dan interval ini.")
    st.stop()

# ============================
# Indikator
# ============================
df['MA50'] = df['Close'].rolling(50).mean()
df['MA200'] = df['Close'].rolling(200).mean()

delta = df['Close'].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = -delta.where(delta < 0, 0).rolling(14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

ema12 = df['Close'].ewm(span=12).mean()
ema26 = df['Close'].ewm(span=26).mean()
df['MACD'] = ema12 - ema26
df['Signal'] = df['MACD'].ewm(span=9).mean()

df['BB_Mid'] = df['Close'].rolling(20).mean()
df['BB_Upper'] = df['BB_Mid'] + 2 * df['Close'].rolling(20).std()
df['BB_Lower'] = df['BB_Mid'] - 2 * df['Close'].rolling(20).std()

# ============================
# Fibonacci Levels
# ============================
max_price = df['Close'].max()
min_price = df['Close'].min()
diff = max_price - min_price
levels = {
    '0.0%': max_price,
    '23.6%': max_price - 0.236 * diff,
    '38.2%': max_price - 0.382 * diff,
    '50.0%': max_price - 0.5 * diff,
    '61.8%': max_price - 0.618 * diff,
    '78.6%': max_price - 0.786 * diff,
    '100.0%': min_price
}

# ============================
# Plot Grafik
# ============================
fig, ax = plt.subplots(figsize=(14, 8))
ax.plot(df['Close'], label='Harga', color='black')
ax.plot(df['MA50'], label='MA50', linestyle='--', color='blue')
ax.plot(df['MA200'], label='MA200', linestyle='--', color='red')
ax.plot(df['BB_Upper'], label='Bollinger Upper', color='green', alpha=0.3)
ax.plot(df['BB_Lower'], label='Bollinger Lower', color='green', alpha=0.3)

for name, level in levels.items():
    ax.axhline(level, linestyle='--', alpha=0.4, label=f'{name}: {level:.4f}')

ax.set_title(f'{symbol} Price Chart with Technical Indicators')
ax.legend()
ax.grid(True)
st.pyplot(fig)

# ============================
# Interpretasi Sederhana
# ============================
st.subheader("📊 Interpretasi Sederhana")

try:
    latest = df.iloc[-1]
    price = latest['Close']
    rsi = latest['RSI']
    macd = latest['MACD']
    signal = latest['Signal']

    st.markdown(f"- 💰 **Harga sekarang:** `{price:.4f}`")
    st.markdown(f"- 📉 **RSI:** `{rsi:.2f}` → " + ("*Overbought ⚠️*" if rsi > 70 else "*Oversold ✅*" if rsi < 30 else "*Netral*"))
    st.markdown(f"- 🧭 **MACD vs Signal:** `{macd:.4f}` / `{signal:.4f}` → " + ("*Bullish crossover ✅*" if macd > signal else "*Bearish crossover ❌*"))

    fib_support = None
    fib_resistance = None
    for level in reversed(levels.values()):
        if price > level:
            fib_support = level
            break
    for level in levels.values():
        if price < level:
            fib_resistance = level
            break

    if fib_support and fib_resistance:
        st.markdown(f"- 📐 **Support Fibonacci:** `{fib_support:.4f}`")
        st.markdown(f"- 📐 **Resistance Fibonacci:** `{fib_resistance:.4f}`")

    st.caption(f"Update terakhir: {df.index[-1].strftime('%Y-%m-%d %H:%M:%S')}")
except Exception as e:
    st.error(f"❌ Gagal menampilkan interpretasi: {e}")

# ============================
# Tampilkan Data Tabel
# ============================
st.subheader("🧾 Data Harga dan Indikator")

show_df = df[['Open', 'High', 'Low', 'Close', 'Volume', 'MA50', 'MA200', 'RSI', 'MACD', 'Signal']].tail(50)
st.dataframe(show_df, use_container_width=True)

# ============================
# Tombol Unduh
# ============================
csv = df.to_csv().encode('utf-8')
st.download_button(
    label="📥 Unduh Semua Data sebagai CSV",
    data=csv,
    file_name=f"{symbol}_{interval}_data.csv",
    mime='text/csv'
)
