import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(layout="wide")
st.title("🌍 Animated ROAS Dashboard (Choropleth by week, 99th percentile, min installs filter)")

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
