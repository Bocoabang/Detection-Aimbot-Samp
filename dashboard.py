# dashboard.py
import streamlit as st
import sqlite3, pandas as pd, json, requests, datetime, time

st.set_page_config(page_title="SA-MP Anticheat Dashboard", layout="wide")
st.title("🔫 SA-MP Aimbot Detector Dashboard")

# --- Fungsi ---
@st.cache_data(ttl=5)  # Update otomatis tiap 5 detik
def load_detections():
    conn = sqlite3.connect("anticheat.db")
    df = pd.read_sql("SELECT * FROM ml_detections ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def send_rcon_command(cmd):
    # Contoh: kirim perintah RCON ke server (ganti IP/PORT/password)
    url = "http://localhost:5000/rcon"  # Endpoint RCON (bisa pakai SAMP-RCON API)
    try:
        r = requests.post(url, json={"cmd": cmd}, timeout=2)
        return r.text
    except:
        return "RCON offline"

# --- Sidebar ---
st.sidebar.header("⚙️ Kontrol")
auto_refresh = st.sidebar.checkbox("Auto-refresh (5s)", value=True)
threshold = st.sidebar.slider("Probability Threshold (%)", 50, 100, 80)

# --- Load data ---
df = load_detections()
df_show = df[df["probability"] >= threshold/100]

# --- Metric cards ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Deteksi", len(df))
col2.metric("Aktif (≥{}%)".format(threshold), len(df_show))
col3.metric("Update terakhir", datetime.datetime.now().strftime("%H:%M:%S"))

# --- Tabel deteksi ---
st.subheader("📋 Deteksi Terbaru")
with st.expander("Filter & aksi"):
    if not df_show.empty:
        for _, row in df_show.iterrows():
            st.write(f"**Player ID {row['player_id']}** - **{row['probability']*100:.1f}%** pada {row['timestamp']}")
            col_a, col_b, col_c = st.columns([1,1,3])
            if col_a.button("Ban", key=f"ban_{row['id']}"):
                send_rcon_command(f"ban {row['player_id']}")
                st.success(f"Player {row['player_id']} dibanned!")
            if col_b.button("Kick", key=f"kick_{row['id']}"):
                send_rcon_command(f"kick {row['player_id']}")
                st.success(f"Player {row['player_id']} dikick!")
            with col_c.expander("Lihat fitur"):
                st.json(json.loads(row["features"]))
    else:
        st.info("Tidak ada deteksi di atas threshold.")

# --- Grafik trend ---
st.subheader("📈 Trend Deteksi (24 jam)")
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["hour"] = df["timestamp"].dt.hour
hourly = df.groupby("hour").size()
st.bar_chart(hourly)

# --- Auto-refresh ---
if auto_refresh:
    time.sleep(5)
    st.rerun()
    
