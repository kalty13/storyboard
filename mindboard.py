import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🌍 Animated ROAS Dashboard: Choropleth + Bubble Map")

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

# Список метрик
exclude_cols = {"week", "country", "channel"}
metrics = [col for col in df.columns if df[col].dtype in [float, int] and col not in exclude_cols]

choropleth_metric = st.selectbox("🗺 Метрика для заливки карты (Choropleth)", metrics, index=metrics.index("roas_w0") if "roas_w0" in metrics else 0)
bubble_metric = st.selectbox("🔵 Метрика для баблов (Bubble)", metrics, index=metrics.index("installs") if "installs" in metrics else 0)

# Делай неделю стрингом для анимации
df['week'] = df['week'].astype(str)

# Основная карта-анимация
fig = px.choropleth(
    df,
    locations="country",
    locationmode="country names",
    color=choropleth_metric,
    hover_name="country",
    animation_frame="week",
    color_continuous_scale="Viridis",
    projection="natural earth",
    title=f"Animated {choropleth_metric} + {bubble_metric} (bubbles) by Country and Week"
)

# Добавляем баблы — делаем отдельный scatter_geo поверх карты
for week in df['week'].unique():
    df_week = df[df['week'] == week]
    fig.add_scattergeo(
        locations=df_week["country"],
        locationmode="country names",
        lon=None, lat=None,
        text=df_week["country"],
        marker=dict(
            size=df_week[bubble_metric].fillna(0).clip(lower=1)**0.7 * 6, # Размер бабла
            color='rgba(255,0,100,0.6)',
            line_width=0,
        ),
        name=f"Bubbles ({week})",
        hoverinfo="text+marker.size",
        visible=False
    )

# Фикс: делаем баблы видимыми только для первого кадра
if len(fig.frames) > 0:
    fig.data[len(fig.data)-len(df['week'].unique())].visible = True

fig.update_geos(showcoastlines=True, showcountries=True, fitbounds="locations", coastlinecolor="Black")
fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

st.plotly_chart(fig, use_container_width=True)
