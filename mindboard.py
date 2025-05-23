import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(layout="wide")
st.title("🌍 Animated ROAS Dashboard (Choropleth by week, 99th percentile, min installs filter)")

# ===== Pro Mode (уменьшенная кнопка + увеличенный тумблер) =====
st.markdown("""
<style>
.fake-pro-btn {
    display: inline-block;
    background: linear-gradient(90deg,#ffe066 60%,#ad69fa 100%);
    color: #232324;
    font-size: 1.06rem;
    font-weight: 800;
    border: none;
    border-radius: 15px;
    padding: 0.33em 1.3em;
    cursor: pointer;
    box-shadow: 0 4px 15px #ad69fa55;
    margin: 10px 0 2px 0;
    letter-spacing: 0.7px;
    text-shadow: 0 1px 4px #fff5, 0 1px 1px #ffe06650;
    user-select: none;
    animation: shine 2.1s linear infinite;
    transition: 
        transform 0.13s cubic-bezier(.4,2.4,.9,.8), 
        box-shadow 0.15s, 
        color 0.13s;
    outline: none;
}
.fake-pro-btn:hover {
    transform: scale(1.11) rotate(-2deg);
    box-shadow: 0 6px 20px #ffe06655, 0 0px 0 2px #ad69fa77;
    color: #ad69fa;
}
@keyframes shine {
    0% { box-shadow: 0 0 8px #ffe06644, 0 0 0 #ad69fa33;}
    50% { box-shadow: 0 0 16px #ad69fa99, 0 0 14px #ffe06633;}
    100% { box-shadow: 0 0 8px #ffe06644, 0 0 0 #ad69fa33;}
}
.big-toggle label[data-testid="stWidgetLabel"] {
    font-size: 1.42rem !important;
    font-weight: 800 !important;
    color: #ad69fa !important;
    letter-spacing: 0.5px;
}
.big-toggle div[data-testid="stToggle"] {
    zoom: 1.5;
}
</style>
<div class="fake-pro-btn" tabindex="0" title="Переведи тумблер ниже для активации!">🚀 Enable Pro Mode</div>
""", unsafe_allow_html=True)

if 'pro_mode_on' not in st.session_state:
    st.session_state['pro_mode_on'] = False

with st.container():
    st.markdown('<div class="big-toggle">', unsafe_allow_html=True)
    pro_mode = st.toggle("✨Pro Mode", value=st.session_state['pro_mode_on'], key="pro_toggle")
    st.markdown('</div>', unsafe_allow_html=True)
st.session_state['pro_mode_on'] = pro_mode

if st.session_state['pro_mode_on']:
    st.markdown("""
        <div style="
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(30,30,40,0.92); z-index: 9999; display: flex; align-items: center; justify-content: center;
        ">
            <div style="background: #232324; border: 3px solid #ffe066; border-radius: 18px; padding: 36px 48px; box-shadow: 0 8px 32px #0007; min-width: 370px; text-align: center;">
                <div style="font-size: 2.3rem; font-weight: bold; color: #ffe066;">🚀 Pro Mode</div>
                <div style="margin-top: 20px; font-size: 1.1rem; color: #fff;">
                    Хочешь пожизненный доступ к Pro-функциям и секретным фичам? 😉<br>
                    <span style="font-size: 1.45rem; font-weight: bold; color: #38ef7d;">0.003฿</span>
                    <div style="margin-top:12px; color:#ffe066; font-size: 1.15rem;">
                        Переведи на адрес:<br>
                        <span style="user-select: all; color: #fff; font-family: monospace;">
                            14H4r2phGv9mbK4XHDdDDR6JPjDbvDr6Zp
                        </span>
                    </div>
                    <div style="margin-top:10px; color:#ff6363; font-size: 0.99rem;">
                        После оплаты — напиши в <a href="https://t.me/kalty13" target="_blank" style="color:#ffe066;">Telegram</a>.<br>
                        Твой аккаунт будет разблокирован в течение 10 минут!
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    close_col = st.columns([6,1,6])[1]
    with close_col:
        if st.button("Закрыть окно Pro Mode", key="close_pro_btn"):
            st.session_state['pro_mode_on'] = False

#$33333333333            

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

exclude_cols = {"week", "country", "channel"}
metrics = [col for col in df.columns if df[col].dtype in [float, int] and col not in exclude_cols]

choropleth_metric = st.selectbox(
    "🗺 Метрика для заливки карты (Choropleth)",
    metrics,
    index=metrics.index("roas_w0") if "roas_w0" in metrics else 0
)

# --- Вот здесь фильтруем по installs ---
min_installs = 300
display_df = df[df['installs'] >= min_installs].copy()

# --- Домножаем на 100, если это ROAS ---
if "roas" in choropleth_metric.lower():
    display_df[choropleth_metric] = display_df[choropleth_metric] * 100

display_df['week'] = display_df['week'].astype(str)

# --- 99-й перцентиль по выбранной метрике ---
if "roas" in choropleth_metric.lower():
    vals = display_df[choropleth_metric][display_df[choropleth_metric] > 0]
    metric_max = np.percentile(vals, 99) if not vals.empty else 1
    metric_min = 0
else:
    vals = display_df[choropleth_metric]
    metric_min = vals.min()
    metric_max = np.percentile(vals, 99) if not vals.empty else 1

color_scales = ['Viridis', 'Plasma', 'Cividis', 'Inferno', 'Turbo', 'Bluered', 'Magma']
color_scale = st.selectbox("🎨 Цветовая схема", color_scales, index=0)

fig = px.choropleth(
    display_df,
    locations="country",
    locationmode="country names",
    color=choropleth_metric,
    hover_name="country",
    animation_frame="week",
    color_continuous_scale=color_scale,
    projection="natural earth",
    range_color=[metric_min, metric_max],
    title=f"Animated {choropleth_metric} (%) by Country and Week"
)

fig.update_geos(
    showcoastlines=True,
    showcountries=True,
    fitbounds="locations",
    coastlinecolor="Black",
    landcolor="rgb(245,245,245)",
)
fig.update_layout(
    margin={"r":0,"t":40,"l":0,"b":0},
    autosize=True,
    width=1800,
    height=900,
    coloraxis_colorbar=dict(title=f"{choropleth_metric} (%)")
)

fig.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>" +
    f"{choropleth_metric}: " + "%{z:.2f}%" +
    "<extra></extra>"
)

st.plotly_chart(fig, use_container_width=True)
