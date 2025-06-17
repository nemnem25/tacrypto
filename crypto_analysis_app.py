import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.title("📈 Fibonacci Retracement Crypto via CoinGecko")

# Form input
coin_id = st.text_input("Masukkan ID CoinGecko (contoh: tron, bitcoin, ethereum)", "tron")
days = st.slider("Jumlah hari ke belakang", 30, 180, 90)

# Ambil data harga harian
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

df = get_price_data(coin_id, days)

if df is None or df.empty:
    st.warning("⚠️ Tidak ada data dari CoinGecko. Periksa ID koin.")
else:
    # Hitung level Fibonacci
    min_price = df['price'].min()
    max_price = df['price'].max()

    levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    fib_levels = {f"{int(level*100)}%": max_price - (max_price - min_price) * level for level in levels}

    # Plot
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['date'], df['price'], label="Harga", color="black")
    for label, level in fib_levels.items():
        ax.hlines(level, df['date'].min(), df['date'].max(), linestyle='--', label=f"{label} = ${level:.3f}")
    ax.set_title(f"Harga Harian dan Fibonacci Levels: {coin_id.upper()}")
    ax.legend()
    st.pyplot(fig)

    # Tampilkan nilai
    st.subheader("📊 Level Fibonacci (USD)")
    st.dataframe(pd.DataFrame(fib_levels, index=["Level"]).T)

    # Interpretasi sederhana
    latest_price = df['price'].iloc[-1]
    near_level = min(fib_levels.items(), key=lambda x: abs(x[1] - latest_price))
    st.subheader("🧠 Interpretasi Sederhana")
    st.markdown(f"Harga terakhir adalah **${latest_price:.3f}**, mendekati level **{near_level[0]}** di **${near_level[1]:.3f}**.")

    if latest_price > max_price:
        st.info("💡 Harga sedang mencetak level tertinggi baru, potensi breakout.")
    elif latest_price < min_price:
        st.warning("⚠️ Harga menembus support terendah, potensi breakdown.")
