import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Crypto TA App", layout="wide")
st.title("📊 Crypto Technical Analysis with Fibonacci, MA, RSI, MACD")

# Input
coin_id = st.text_input("🔍 Masukkan ID CoinGecko (contoh: tron, bitcoin, ethereum)", "tron")
days = st.slider("Jumlah hari ke belakang", 30, 180, 90)

@st.cache_data
def get_price_data(coin_id, days):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily"
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None
    data = r.json()
    prices = data['prices']
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def add_indicators(df):
    # MA
    df['MA20'] = df['price'].rolling(window=20).mean()
    df['MA50'] = df['price'].rolling(window=50).mean()

    # RSI
    delta = df['price'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['price'].ewm(span=12, adjust=False).mean()
    exp2 = df['price'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    return df

df = get_price_data(coin_id, days)

if df is None or df.empty:
    st.warning("⚠️ Tidak ada data dari CoinGecko. Periksa ID koin.")
else:
    df = add_indicators(df)
    min_price = df['price'].min()
    max_price = df['price'].max()

    levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    fib_levels = {f"{int(level*100)}%": max_price - (max_price - min_price) * level for level in levels}

    # === CHART HARGA + FIBONACCI ===
    st.subheader("📈 Harga Harian + Fibonacci Levels")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['date'], df['price'], label="Harga", color="black")
    for label, level in fib_levels.items():
        ax.hlines(level, df['date'].min(), df['date'].max(), linestyle='--', label=f"{label} = ${level:.3f}")
    ax.set_title(f"Harga Harian dan Fibonacci: {coin_id.upper()}")
    ax.legend()
    st.pyplot(fig)

    # === MA ===
    st.subheader("📊 Moving Averages (MA20 & MA50)")
    fig_ma, ax_ma = plt.subplots(figsize=(10, 4))
    ax_ma.plot(df['date'], df['price'], label='Harga', color='black')
    ax_ma.plot(df['date'], df['MA20'], label='MA20', linestyle='--')
    ax_ma.plot(df['date'], df['MA50'], label='MA50', linestyle='-.')
    ax_ma.legend()
    st.pyplot(fig_ma)

    # === RSI ===
    st.subheader("📉 RSI (Relative Strength Index)")
    fig_rsi, ax_rsi = plt.subplots(figsize=(10, 3))
    ax_rsi.plot(df['date'], df['RSI'], label='RSI', color='purple')
    ax_rsi.axhline(70, color='red', linestyle='--')
    ax_rsi.axhline(30, color='green', linestyle='--')
    ax_rsi.set_ylim(0, 100)
    ax_rsi.legend()
    st.pyplot(fig_rsi)

    # === MACD ===
    st.subheader("📈 MACD (Moving Average Convergence Divergence)")
    fig_macd, ax_macd = plt.subplots(figsize=(10, 3))
    ax_macd.plot(df['date'], df['MACD'], label='MACD', color='blue')
    ax_macd.plot(df['date'], df['Signal'], label='Signal', color='orange')
    ax_macd.axhline(0, color='gray', linestyle='--')
    ax_macd.legend()
    st.pyplot(fig_macd)

    # === LEVEL NUMERIK FIBONACCI ===
    st.subheader("📋 Tabel Level Fibonacci")
    st.dataframe(pd.DataFrame(fib_levels, index=["USD"]).T)

    # === INTERPRETASI ===
    latest = df.iloc[-1]
    latest_price = latest['price']
    near_level_label, near_level_price = min(fib_levels.items(), key=lambda x: abs(x[1] - latest_price))

    st.subheader("🧠 Interpretasi Otomatis")
    st.markdown(f"Harga terakhir: **${latest_price:.3f}**, dekat level Fibonacci **{near_level_label}** (${near_level_price:.3f})")

    # RSI Interpretation
    if latest['RSI'] >= 70:
        st.warning("📍 RSI berada di atas 70: kondisi *overbought*, potensi koreksi.")
    elif latest['RSI'] <= 30:
        st.success("📍 RSI di bawah 30: kondisi *oversold*, potensi pantulan.")
    else:
        st.info("📍 RSI normal (30-70): belum ada sinyal jenuh beli/jual.")

    # MACD Interpretation
    if latest['MACD'] > latest['Signal']:
        st.success("📈 MACD di atas signal line: tren naik sedang berlangsung.")
    elif latest['MACD'] < latest['Signal']:
        st.warning("📉 MACD di bawah signal line: tren turun mungkin terjadi.")
    else:
        st.info("📍 MACD dan signal line berpotongan: tunggu konfirmasi arah.")
