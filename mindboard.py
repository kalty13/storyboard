import streamlit as st
import pandas as pd
import plotly.express as px
import pycountry
import matplotlib
import matplotlib.cm

st.set_page_config(layout="wide")
st.title("🏁 Animated ROAS Bar Chart Race by Country")

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

# Фильтр по каналу
channels = ["Все"] + sorted(df['channel'].unique())
selected_channel = st.selectbox("Канал", channels)
df_filtered = df.copy()
if selected_channel != "Все":
    df_filtered = df_filtered[df_filtered['channel'] == selected_channel]

# Метрики
exclude_cols = {"week", "country", "channel"}
metrics = [col for col in df.columns if df[col].dtype in [float, int] and col not in exclude_cols]

choropleth_metric = st.selectbox(
    "Метрика для сравнения (ROAS, LTV и т.д.)",
    metrics,
    index=metrics.index("roas_w0") if "roas_w0" in metrics else 0
)

min_installs = 300
df_filtered = df_filtered[df_filtered['installs'] >= min_installs].copy()

if "roas" in choropleth_metric.lower():
    df_filtered[choropleth_metric] = df_filtered[choropleth_metric] * 100

# Добавляем флаги (для всех строк)
def country_to_flag(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        return ''.join([chr(127397 + ord(c)) for c in country.alpha_2.upper()])
    except Exception:
        return ''

df_filtered['flag'] = df_filtered['country'].apply(country_to_flag)

# Собираем подпись
df_filtered['country_label'] = (
    df_filtered['flag'] + ' ' + df_filtered['country'] +
    ' (' + df_filtered['installs'].astype(int).astype(str) + ' installs)'
)

# Градиент для bar race
norm = matplotlib.colors.Normalize(
    vmin=df_filtered[choropleth_metric].min(), vmax=df_filtered[choropleth_metric].max()
)
colormap = matplotlib.cm.get_cmap('plasma')
df_filtered['bar_color'] = df_filtered[choropleth_metric].apply(
    lambda x: matplotlib.colors.rgb2hex(colormap(norm(x)))
)

# Bar chart race: animation_frame = week
fig = px.bar(
    df_filtered,
    y='country_label',
    x=choropleth_metric,
    color='bar_color',
    animation_frame='week',
    orientation='h',
    text=choropleth_metric,
    labels={choropleth_metric: f"{choropleth_metric} (%)", "country_label": "Страна"},
    title=f"{choropleth_metric} by Country — Animated by Week",
    color_discrete_map="identity"
)

fig.update_traces(
    marker_color=df_filtered['bar_color'],
    texttemplate='%{text:.2f}%',
    textposition='outside'
)
fig.update_layout(
    yaxis={'categoryorder': 'total ascending'},
    autosize=True,
    margin={"r":30,"t":40,"l":0,"b":0},
    xaxis_title=f"{choropleth_metric} (%)",
    yaxis_title=None
)

st.plotly_chart(fig, use_container_width=True)
