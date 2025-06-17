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
    df['MA20'] = df['price'].rolling(window=20).mean()
    df['MA50'] = df['price'].rolling(window=50).mean()

    delta = df['price'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

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
    latest = df.dropna().iloc[-1]
    latest_price = latest['price']

    # Fibonacci
    min_price = df['price'].min()
    max_price = df['price'].max()
    levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    fib_levels = {f"{int(level*100)}%": max_price - (max_price - min_price) * level for level in levels}

    # Temukan level Fibonacci terdekat
    near_level_label = min(fib_levels, key=lambda k: abs(fib_levels[k] - latest_price))
    near_level_price = fib_levels[near_level_label]

    # === GRAFIK HARGA + FIBONACCI ===
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
    st.subheader("📊 Ringkasan Data Teknis")
    st.markdown(f"""
    - **Harga terakhir:** ${latest_price:.4f}  
    - **RSI:** {latest['RSI']:.2f}  
    - **MACD:** {latest['MACD']:.4f}  
    - **Signal Line:** {latest['Signal']:.4f}  
    - **MA20:** {latest['MA20']:.4f}  
    - **MA50:** {latest['MA50']:.4f}
    """)

    st.subheader("🧾 Tafsiran Naratif")

    fib_desc = f"Harga saat ini berada di sekitar level Fibonacci {near_level_label} yaitu sekitar ${near_level_price:.3f}, yang sering kali menjadi zona tarik-ulur antara pembeli dan penjual. Ini menunjukkan bahwa pasar sedang menguji batas penting dalam konteks psikologis dan teknikal."

    rsi_desc = ""
    if latest['RSI'] >= 70:
        rsi_desc = f"RSI yang berada di angka {latest['RSI']:.2f} menandakan kondisi *overbought*, mengindikasikan potensi koreksi atau perlambatan tren naik saat ini."
    elif latest['RSI'] <= 30:
        rsi_desc = f"RSI tercatat di {latest['RSI']:.2f}, menandakan kondisi *oversold*. Ini bisa membuka peluang pantulan harga dalam waktu dekat."
    else:
        rsi_desc = f"RSI berada di kisaran netral ({latest['RSI']:.2f}), yang menunjukkan belum ada tekanan beli atau jual yang ekstrem."

    macd_desc = ""
    if latest['MACD'] > latest['Signal']:
        macd_desc = f"MACD saat ini ({latest['MACD']:.4f}) berada di atas garis sinyal ({latest['Signal']:.4f}), mengindikasikan kekuatan tren naik sedang berkembang."
    elif latest['MACD'] < latest['Signal']:
        macd_desc = f"MACD ({latest['MACD']:.4f}) berada di bawah garis sinyal ({latest['Signal']:.4f}), yang mencerminkan momentum menurun."
    else:
        macd_desc = f"MACD dan signal line saling bertemu di {latest['MACD']:.4f}, menandakan ketidakpastian arah tren jangka pendek."

    ma_desc = ""
    if latest['MA20'] > latest['MA50']:
        ma_desc = f"Rata-rata MA20 (${latest['MA20']:.4f}) berada di atas MA50 (${latest['MA50']:.4f}), mencerminkan tren jangka pendek yang masih lebih kuat daripada jangka menengah, yang merupakan sinyal bullish."
    elif latest['MA20'] < latest['MA50']:
        ma_desc = f"MA20 (${latest['MA20']:.4f}) berada di bawah MA50 (${latest['MA50']:.4f}), sinyal teknikal awal potensi pembalikan ke bawah (bearish crossover)."
    else:
        ma_desc = f"MA20 dan MA50 berimpit, menunjukkan pasar sedang berada dalam fase konsolidasi."

    outlook = ""
    if latest['RSI'] < 70 and latest['MACD'] > latest['Signal'] and latest_price > latest['MA20']:
        outlook = "Secara umum, kombinasi RSI netral, MACD positif, dan harga di atas MA20 mengindikasikan peluang lanjutan tren naik dalam jangka pendek. Namun, perlu waspada terhadap volatilitas di sekitar level Fibonacci saat ini."
    else:
        outlook = "Meskipun indikator menunjukkan sinyal yang bercampur, pasar saat ini cenderung menunggu pemicu baru untuk bergerak signifikan. Trader sebaiknya memperhatikan konfirmasi volume dan breakout di atas level Fibonacci terdekat."

    st.markdown(f"""
    1️⃣ {fib_desc}

    2️⃣ {rsi_desc}

    3️⃣ {macd_desc}

    4️⃣ {ma_desc}

    5️⃣ {outlook}
    """)
