import streamlit as st
import pandas as pd
import plotly.express as px
import pycountry

st.set_page_config(layout="wide")
st.title("📊 Сравнение метрик по странам — Grouped Bar Chart")

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

# Слайдер по неделям
weeks = sorted(df_filtered['week'].unique())
week_idx = st.slider("Неделя", min_value=0, max_value=len(weeks)-1, value=0, format="%d")
selected_week = weeks[week_idx]

# Фильтр по installs
min_installs = 300
df_week = df_filtered[(df_filtered['week'] == selected_week) & (df_filtered['installs'] >= min_installs)].copy()

# Метрики (можно выбрать несколько)
exclude_cols = {"week", "country", "channel"}
all_metrics = [col for col in df.columns if df[col].dtype in [float, int] and col not in exclude_cols]

multi_metrics = st.multiselect(
    "Какие метрики сравнивать?",
    all_metrics,
    default=[m for m in ["roas_w0", "lifetime_value", "cpi"] if m in all_metrics]
)
if not multi_metrics:
    st.warning("Выбери хотя бы одну метрику!")
    st.stop()

# Переводим ROAS в проценты (для наглядности)
for m in multi_metrics:
    if "roas" in m.lower():
        df_week[m] = df_week[m] * 100

# Агрегируем (max или mean по стране)
df_group = df_week.groupby("country", as_index=False)[multi_metrics].max()

# Добавляем флаги
def country_to_flag(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        return ''.join([chr(127397 + ord(c)) for c in country.alpha_2.upper()])
    except Exception:
        return ''

df_group['flag'] = df_group['country'].apply(country_to_flag)
df_group['country_label'] = df_group['flag'] + ' ' + df_group['country']

# Строим длинную таблицу для plotly
df_long = df_group.melt(
    id_vars=['country_label'],
    value_vars=multi_metrics,
    var_name='metric',
    value_name='value'
)

# Если в multi_metrics есть ROAS — подписываем %
def pretty_value(row):
    if "roas" in row['metric'].lower():
        return f"{row['value']:.2f}%"
    else:
        return f"{row['value']:.2f}"

df_long['pretty_value'] = df_long.apply(pretty_value, axis=1)

# График
fig = px.bar(
    df_long,
    x="country_label",
    y="value",
    color="metric",
    barmode="group",
    text='pretty_value',
    labels={"value": "Значение", "country_label": "Страна", "metric": "Метрика"},
    title=f"Группированный барчарт: {', '.join(multi_metrics)} — {selected_week}"
)
fig.update_traces(textposition='outside')
fig.update_layout(
    xaxis_title="Страна",
    yaxis_title="Значение",
    margin={"r":30,"t":40,"l":0,"b":0},
    height=600,
)
st.plotly_chart(fig, use_container_width=True)
