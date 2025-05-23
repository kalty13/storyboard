import streamlit as st
import pandas as pd
import plotly.express as px
import pycountry
import matplotlib
import matplotlib.cm

st.set_page_config(layout="wide")
st.title("🌍 ROAS by Country — Horizontal Bar Chart")

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

# 1. Фильтр по каналу (до всех остальных фильтров!)
channels = ["Все"] + sorted(df['channel'].unique())
selected_channel = st.selectbox("Канал", channels)

df_filtered = df.copy()
if selected_channel != "Все":
    df_filtered = df_filtered[df_filtered['channel'] == selected_channel]

# 2. Фильтр по неделе
weeks = sorted(df_filtered['week'].unique())
selected_week = st.selectbox("Неделя", weeks, index=0)

# 3. Фильтр по installs (и копия для работы)
min_installs = 300
df_week = df_filtered[(df_filtered['week'] == selected_week) & (df_filtered['installs'] >= min_installs)].copy()

# 4. Метрики
exclude_cols = {"week", "country", "channel"}
metrics = [col for col in df.columns if df[col].dtype in [float, int] and col not in exclude_cols]

choropleth_metric = st.selectbox(
    "Метрика для сравнения (ROAS, LTV и т.д.)",
    metrics,
    index=metrics.index("roas_w0") if "roas_w0" in metrics else 0
)

# 5. Перевод ROAS в проценты
if "roas" in choropleth_metric.lower():
    df_week[choropleth_metric] = df_week[choropleth_metric] * 100

# 6. Агрегация по стране (если нужно, например, максимум)
df_week_agg = df_week.groupby('country', as_index=False)[choropleth_metric].max()

# 7. Добавляем флаги и подписи
def country_to_flag(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        return ''.join([chr(127397 + ord(c)) for c in country.alpha_2.upper()])
    except Exception:
        return ''

df_week_agg['flag'] = df_week_agg['country'].apply(country_to_flag)
df_week_agg['country_label'] = df_week_agg['flag'] + ' ' + df_week_agg['country']

# 8. Цветовой градиент для баров (от min до max)
norm = matplotlib.colors.Normalize(vmin=df_week_agg[choropleth_metric].min(), vmax=df_week_agg[choropleth_metric].max())
colormap = matplotlib.cm.get_cmap('plasma')  # Можно менять
df_week_agg['bar_color'] = df_week_agg[choropleth_metric].apply(lambda x: matplotlib.colors.rgb2hex(colormap(norm(x))))

# 9. Построение barplot
fig = px.bar(
    df_week_agg,
    y='country_label',
    x=choropleth_metric,
    orientation='h',
    text=choropleth_metric,
    labels={choropleth_metric: f"{choropleth_metric} (%)", "country_label": "Страна"},
    title=f"{choropleth_metric} by Country — {selected_week}"
)

fig.update_traces(
    marker_color=df_week_agg['bar_color'],
    texttemplate='%{text:.2f}%',
    textposition='outside'
)
fig.update_layout(
    yaxis={'categoryorder':'total ascending'},
    autosize=True,
    margin={"r":30,"t":40,"l":0,"b":0},
    height=50 + len(df_week_agg)*30,
    xaxis_title=f"{choropleth_metric} (%)",
    yaxis_title=None
)

st.plotly_chart(fig, use_container_width=True)
