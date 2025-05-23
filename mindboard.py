import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🌍 Animated ROAS Dashboard (Choropleth by week)")

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

# Список метрик для выбора
exclude_cols = {"week", "country", "channel"}
metrics = [col for col in df.columns if df[col].dtype in [float, int] and col not in exclude_cols]

# UI
choropleth_metric = st.selectbox(
    "🗺 Метрика для заливки карты (Choropleth)", 
    metrics, 
    index=metrics.index("roas_w0") if "roas_w0" in metrics else 0
)

# Для красоты — пусть неделя будет строкой
df['week'] = df['week'].astype(str)

# Основная карта с анимацией по неделям
fig = px.choropleth(
    df,
    locations="country",
    locationmode="country names",
    color=choropleth_metric,
    hover_name="country",
    animation_frame="week",
    color_continuous_scale="Viridis",
    projection="natural earth",
    title=f"Animated {choropleth_metric} by Country and Week"
)

fig.update_geos(
    showcoastlines=True, 
    showcountries=True, 
    fitbounds="locations", 
    coastlinecolor="Black"
)
fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

st.plotly_chart(fig, use_container_width=True)
