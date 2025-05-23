import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(layout="wide")
st.title("🌍 Animated ROAS Dashboard (Choropleth by week, global scale)")

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

# Фильтруем страны, где installs < 300 за неделю
display_df = df.copy()
display_df = display_df[display_df['installs'] >= 300]

if "roas" in choropleth_metric.lower():
    display_df[choropleth_metric] = display_df[choropleth_metric] * 100

display_df['week'] = display_df['week'].astype(str)

# Игнорируем выбросы — 99-й перцентиль только по оставшимся данным!
if "roas" in choropleth_metric.lower():
    roas_vals = display_df[choropleth_metric][display_df[choropleth_metric] > 0]
    metric_max = np.percentile(roas_vals, 99)
    metric_min = 0
else:
    metric_min = display_df[choropleth_metric].min()
    metric_max = np.percentile(display_df[choropleth_metric], 99)

# дальше всё как раньше...

exclude_cols = {"week", "country", "channel"}
metrics = [col for col in df.columns if df[col].dtype in [float, int] and col not in exclude_cols]

choropleth_metric = st.selectbox(
    "🗺 Метрика для заливки карты (Choropleth)",
    metrics,
    index=metrics.index("roas_w0") if "roas_w0" in metrics else 0
)

st.write(f"Выбрана метрика: {choropleth_metric}")
st.write(f"Минимум: {metric_min}, Максимум: {metric_max}")


# Домножаем, если это ROAS
display_df = df.copy()
if "roas" in choropleth_metric.lower():
    display_df[choropleth_metric] = display_df[choropleth_metric] * 100

display_df['week'] = display_df['week'].astype(str)

if "roas" in choropleth_metric.lower():
    metric_min = display_df[choropleth_metric][display_df[choropleth_metric] > 0].min()
    metric_max = display_df[choropleth_metric].max()
else:
    metric_min = display_df[choropleth_metric].min()
    metric_max = display_df[choropleth_metric].max()

fig = px.choropleth(
    display_df,
    locations="country",
    locationmode="country names",
    color=choropleth_metric,
    hover_name="country",
    animation_frame="week",
    color_continuous_scale=color_scale,
    projection="natural earth",
    range_color=[metric_min, metric_max] if metric_max > metric_min else None,
    title=f"Animated {choropleth_metric} by Country and Week"
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

# Ховер с форматированием как процент
fig.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>" +
    f"{choropleth_metric}: " + "%{z:.2f}%" +
    "<extra></extra>"
)

st.plotly_chart(fig, use_container_width=True)
