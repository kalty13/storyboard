import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🌍 World ROAS Dashboard by Week")

# --- Загрузка данных ---
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    return df

df = load_data()

# --- Преобразование данных ---
# Список метрик (все float-колонки, кроме installs/ecpi)
exclude_cols = {"week", "country", "channel"}
metrics = [col for col in df.columns if df[col].dtype in [float, int] and col not in exclude_cols]

# Список недель
weeks = sorted(df['week'].unique())

# --- UI ---
col1, col2 = st.columns([2, 3])
with col1:
    metric = st.selectbox("📈 Выберите метрику", metrics, index=metrics.index("roas_w0") if "roas_w0" in metrics else 0)
with col2:
    week = st.select_slider("🗓 Неделя", options=weeks, value=weeks[0])

# --- Фильтрация данных ---
df_week = df[df['week'] == week]

# --- Карта ---
fig = px.choropleth(
    df_week,
    locations="country",
    locationmode="country names",
    color=metric,
    hover_name="country",
    color_continuous_scale="Viridis",  # Больше контраста!
    title=f"{metric} by Country — {week}",
    projection="natural earth",
)

# Границы стран
fig.update_geos(showcoastlines=True, coastlinecolor="Black",
                showframe=False, showland=True, landcolor="rgb(220,220,220)")

# Подписи на ховере
fig.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>" +
                  metric + ": %{z:.2f}<extra></extra>"
)

# Яркая граница и отсутствие заливки у стран без данных
fig.update_traces(marker_line_width=1.2, marker_line_color="black")

fig.update_layout(
    margin={"r":0,"t":40,"l":0,"b":0},
    coloraxis_colorbar=dict(title=metric),
    geo=dict(bgcolor='rgba(0,0,0,0)'),
    paper_bgcolor='rgba(0,0,0,0)',
)

st.plotly_chart(fig, use_container_width=True)

