"""Smart Kisan (سمارٹ کسان) - Urdu advisory web app for cotton farmers.

Run:  streamlit run app.py
"""
import json
import os
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="سمارٹ کسان", page_icon="🌱", layout="centered")

MANDI_CSV = Path(__file__).parent / "data" / "mandi_rates.csv"
RAIN_ALERT_PERCENT = 60
DAY_NAMES = ["پیر", "منگل", "بدھ", "جمعرات", "جمعہ", "ہفتہ", "اتوار"]


def ensure_mandi_csv() -> None:
    """Creates the mandi rates file (empty rates) the first time the app runs."""
    if not MANDI_CSV.exists():
        MANDI_CSV.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            {
                "city": ["ملتان", "بہاولپور", "رحیم یار خان", "فیصل آباد", "سکھر"],
                "rate_per_maund": [None] * 5,
                "updated": [None] * 5,
            }
        ).to_csv(MANDI_CSV, index=False)


ensure_mandi_csv()

# Approximate district-centre coordinates, used only for the weather forecast.
DISTRICTS = {
    "ملتان": (30.1575, 71.5249),
    "بہاولپور": (29.3956, 71.6836),
    "رحیم یار خان": (28.4202, 70.2952),
    "وہاڑی": (30.0452, 72.3489),
    "لودھراں": (29.5393, 71.6324),
    "ساہیوال": (30.6682, 73.1114),
    "فیصل آباد": (31.4504, 73.1350),
    "سکھر": (27.7052, 68.8574),
    "حیدرآباد": (25.3960, 68.3578),
    "میرپور خاص": (25.5276, 69.0111),
}

SRC = "[ماخذ شامل کریں: CCRI ملتان / محکمہ زراعت]"

# TODO(verify): the day ranges and advice are generic PLACEHOLDERS. Replace them
# with recommendations from CCRI Multan, PCCC or your provincial agriculture
# department before real farmers use the app. Never add spray or fertilizer
# doses without an official source.
STAGES = [
    {"name": "کاشت اور اگاؤ", "from": 0, "to": 20,
     "task": "کھیت میں اگاؤ کا معائنہ کریں اور خالی جگہوں کی نشاندہی کریں۔",
     "warning": "اگاؤ کمزور یا بے ترتیب ہو تو اپنے زرعی افسر سے رابطہ کریں۔"},
    {"name": "ابتدائی نشوونما", "from": 21, "to": 45,
     "task": "ہفتہ وار کھیت کا معائنہ کریں اور پتوں کے نیچے سفید مکھی اور دیگر کیڑے دیکھیں۔",
     "warning": "ماہر کے مشورے کے بغیر ادویات کا سپرے نہ کریں۔"},
    {"name": "شاخیں اور کلیاں", "from": 46, "to": 70,
     "task": "پتوں اور کلیوں کا معائنہ جاری رکھیں اور پانی کی ضرورت کا جائزہ لیں۔",
     "warning": "پتہ مروڑ وائرس کے آثار نظر آئیں تو فوراً ماہر سے مشورہ لیں۔"},
    {"name": "پھول اور ٹینڈے بننا", "from": 71, "to": 110,
     "task": "گلابی سنڈی کے لیے پھولوں اور ٹینڈوں کا باقاعدہ معائنہ کریں۔",
     "warning": "بارش یا گرمی کی لہر کی اطلاع کے لیے موسم کا ٹیب دیکھتے رہیں۔"},
    {"name": "ٹینڈے کھلنا اور چنائی", "from": 111, "to": 200,
     "task": "صاف اور خشک پھٹی چنیں اور اسے نمی اور ملاوٹ سے بچا کر رکھیں۔",
     "warning": "گیلی یا ملاوٹ والی پھٹی کا ریٹ کم ملتا ہے۔"},
]

# ---------- Styling: right-to-left Urdu, large text, green theme ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;700&display=swap');
[data-testid="stMarkdownContainer"], label, button p, h1, h2, h3 {
    font-family: 'Noto Naskh Arabic', serif !important;
    direction: rtl; text-align: right;
}
[data-testid="stMarkdownContainer"] p { font-size: 20px; line-height: 1.9; }
.stTabs [data-baseweb="tab-list"] { flex-direction: row-reverse; overflow-x: auto; }
.stApp { background: #fbf7ee; }
</style>
""",
    unsafe_allow_html=True,
)


# ---------- Helpers ----------
def days_since(sowing: date) -> int:
    return (date.today() - sowing).days


def stage_for(day: int) -> dict:
    for s in STAGES:
        if s["from"] <= day <= s["to"]:
            return s
    return STAGES[0] if day < STAGES[0]["from"] else STAGES[-1]


@st.cache_data(ttl=3600, show_spinner=False)
def get_forecast(lat: float, lon: float) -> pd.DataFrame:
    """7-day forecast from Open-Meteo (free, no API key)."""
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": 7,
        },
        timeout=10,
    )
    r.raise_for_status()
    d = r.json()["daily"]
    return pd.DataFrame(
        {
            "date": pd.to_datetime(d["time"]),
            "max": d["temperature_2m_max"],
            "min": d["temperature_2m_min"],
            "rain": pd.Series(d["precipitation_probability_max"]).fillna(0).astype(int),
        }
    )


def speak_button(text: str) -> None:
    """Reads Urdu text aloud with the browser's speech engine (needs an Urdu voice)."""
    safe = json.dumps(text).replace("'", "\\u0027")
    components.html(
        f"""<button onclick='const u=new SpeechSynthesisUtterance({safe});u.lang="ur-PK";u.rate=0.9;speechSynthesis.cancel();speechSynthesis.speak(u);'
        style="font-size:18px;padding:8px 18px;border-radius:12px;border:1px solid #14532d;background:#e7f3e8;cursor:pointer">🔊 آواز میں سنیں</button>""",
        height=55,
    )


def admin_password():
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        return os.environ.get("ADMIN_PASSWORD")


# ---------- Setup (district + sowing date), kept in the page link ----------
qp = st.query_params
district = qp.get("d")
sowing = None
try:
    sowing = date.fromisoformat(qp.get("s", ""))
except ValueError:
    pass

if district not in DISTRICTS or sowing is None:
    st.title("🌱 خوش آمدید – سمارٹ کسان")
    with st.form("setup"):
        d = st.selectbox("آپ کا ضلع", list(DISTRICTS))
        s = st.date_input("کپاس کی کاشت کی تاریخ", value=date.today(), max_value=date.today())
        if st.form_submit_button("آگے بڑھیں", use_container_width=True):
            st.query_params["d"] = d
            st.query_params["s"] = s.isoformat()
            st.rerun()
    st.caption("ٹپ: اس صفحے کو بُک مارک کر لیں، آپ کا ضلع اور تاریخ محفوظ رہیں گے۔")
    st.stop()

day = days_since(sowing)
stage = stage_for(day)

tab_home, tab_weather, tab_cal, tab_mandi, tab_pest, tab_admin = st.tabs(
    ["🏠 ہوم", "🌦 موسم", "📅 کیلنڈر", "🏪 منڈی", "🔬 بیماری", "🔐 ایڈمن"]
)

# ---------- Home ----------
with tab_home:
    st.title("🌱 سمارٹ کسان")
    st.markdown(f"**ضلع:** {district} &nbsp;•&nbsp; **کاشت کو:** {day} دن")
    with st.container(border=True):
        st.subheader("آج کا کام")
        st.markdown(f"**{stage['name']}**")
        st.markdown(stage["task"])
        speak_button(f"{stage['name']}۔ {stage['task']}")
    if st.button("ضلع یا تاریخ تبدیل کریں"):
        st.query_params.clear()
        st.rerun()

# ---------- Weather ----------
with tab_weather:
    st.header(f"موسم – {district}")
    try:
        fc = get_forecast(*DISTRICTS[district])
        rainy = fc[fc["rain"] >= RAIN_ALERT_PERCENT]
        if not rainy.empty:
            first = rainy.iloc[0]
            msg = f"بارش کا امکان: {DAY_NAMES[first['date'].weekday()]} ({first['rain']}%)"
            st.warning("⚠ " + msg)
            speak_button(msg)
        for _, row in fc.iterrows():
            with st.container(border=True):
                st.markdown(
                    f"**{DAY_NAMES[row['date'].weekday()]}** &nbsp; "
                    f"{round(row['max'])}° / {round(row['min'])}° &nbsp; • &nbsp; بارش: {row['rain']}%"
                )
    except Exception:
        st.error("موسم کی معلومات نہیں مل سکیں۔ انٹرنیٹ چیک کر کے دوبارہ کوشش کریں۔")

# ---------- Crop calendar ----------
with tab_cal:
    st.header("فصل کیلنڈر")
    st.markdown(f"کاشت کو **{day}** دن ہو چکے ہیں")
    for s in STAGES:
        current = s is stage
        with st.container(border=True):
            st.subheader(("✅ " if current else "") + s["name"])
            st.caption(f"دن {s['from']} سے {s['to']} تک")
            st.markdown(s["task"])
            st.info("⚠ " + s["warning"])
            st.caption(SRC)
            if current:
                speak_button(f"{s['name']}۔ {s['task']} {s['warning']}")

# ---------- Mandi rates ----------
with tab_mandi:
    st.header("منڈی ریٹ")
    st.caption("روپے فی من (40 کلو)")
    mandi = pd.read_csv(MANDI_CSV)
    if mandi["rate_per_maund"].isna().all():
        st.warning("ریٹ ابھی شامل نہیں کیے گئے۔ ایڈمن ٹیب سے شامل کریں۔")
    for _, r in mandi.iterrows():
        rate = "—" if pd.isna(r["rate_per_maund"]) else f"{int(r['rate_per_maund']):,}"
        with st.container(border=True):
            st.markdown(f"**{r['city']}** &nbsp;•&nbsp; {rate}")
            if pd.notna(r["updated"]):
                st.caption(f"آخری اپڈیٹ: {r['updated']}")

# ---------- Pest / disease detection (phase 2 placeholder) ----------
with tab_pest:
    st.header("بیماری کی پہچان")
    photo = st.camera_input("پتے کی تصویر لیں") or st.file_uploader(
        "یا گیلری سے تصویر چنیں", type=["jpg", "jpeg", "png"]
    )
    if photo:
        st.image(photo, use_container_width=True)
        # TODO (phase 2): load the trained model (e.g. Keras/TFLite), predict, and show
        # the class with a confidence level. If confidence is low, show "پکا یقین نہیں"
        # and tell the farmer to contact an agriculture officer.
        st.info("پہچان کا ماڈل جلد شامل کیا جائے گا۔")

# ---------- Admin: edit mandi rates ----------
with tab_admin:
    st.header("ایڈمن")
    expected = admin_password()
    if not expected:
        st.info("ایڈمن پاس ورڈ سیٹ نہیں۔ README دیکھیں (ADMIN_PASSWORD)۔")
    elif st.text_input("پاس ورڈ", type="password") == expected:
        edited = st.data_editor(
            pd.read_csv(MANDI_CSV), num_rows="dynamic", use_container_width=True
        )
        if st.button("محفوظ کریں"):
            edited["updated"] = edited.apply(
                lambda r: r["updated"]
                if pd.notna(r["updated"])
                else (date.today().isoformat() if pd.notna(r["rate_per_maund"]) else None),
                axis=1,
            )
            edited.to_csv(MANDI_CSV, index=False)
            st.success("ریٹ محفوظ ہو گئے۔")
