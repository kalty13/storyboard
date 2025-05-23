import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pycountry

st.set_page_config(layout="wide")
st.title("🪄 Комбинированная динамика: ROAS vs LTV/CPI")

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

channels = ["Все"] + sorted(df['channel'].unique())
selected_channel = st.selectbox("Канал", channels)
df_filtered = df.copy()
if selected_channel != "Все":
    df_filtered = df_filtered[df_filtered['channel'] == selected_channel]

# --- Фильтр по installs ---
min_installs = 300
df_filtered = df_filtered[df_filtered['installs'] >= min_installs]

# --- Метрики и страны ---
exclude_cols = {"week", "country", "channel"}
all_metrics = [col for col in df.columns if df[col].dtype in [float, int] and col not in exclude_cols]

# Основная метрика по левой оси (например, roas_w0)
main_metric = st.selectbox(
    "Основная метрика (левая ось Y)", 
    [m for m in all_metrics if "roas" in m.lower()],
    index=0
)

# Метрики по правой оси
right_metrics = ["cpi", "lifetime_value", "ltv_adv", "ltv_sub"]  # укажи названия как в твоём CSV!
right_metrics = [m for m in right_metrics if m in all_metrics]

all_countries = sorted(df_filtered['country'].unique())
selected_countries = st.multiselect("Страны", all_countries, default=all_countries[:3])
df_plot = df_filtered[df_filtered['country'].isin(selected_countries)]

# --- Добавляем флаги для красоты ---
def country_to_flag(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        return ''.join([chr(127397 + ord(c)) for c in country.alpha_2.upper()])
    except Exception:
        return ''
df_plot['country_flag'] = df_plot['country'].apply(country_to_flag)
df_plot['country_label'] = df_plot['country_flag'] + ' ' + df_plot['country']

# --- Преобразуем ROAS в % ---
if "roas" in main_metric.lower():
    df_plot[main_metric] = df_plot[main_metric] * 100

# --- Сортируем недели для корректного графика ---
weeks = sorted(df_plot['week'].unique())
df_plot['week'] = pd.Categorical(df_plot['week'], categories=weeks, ordered=True)

# --- Построение комбинированного графика ---
fig = go.Figure()

# Основная ось Y — ROAS (или что выбрано), по странам
for country in selected_countries:
    mask = df_plot['country'] == country
    fig.add_trace(go.Scatter(
        x=df_plot[mask]['week'],
        y=df_plot[mask][main_metric],
        name=f"{main_metric.upper()} {country_to_flag(country)} {country}",
        mode="lines+markers",
        yaxis="y1"
    ))

# Правая ось Y2 — остальные метрики (по странам)
color_map = ["#A93226", "#2874A6", "#229954", "#AF7AC5", "#F5B041"]
for idx, metric in enumerate(right_metrics):
    for country in selected_countries:
        mask = df_plot['country'] == country
        fig.add_trace(go.Scatter(
            x=df_plot[mask]['week'],
            y=df_plot[mask][metric],
            name=f"{metric.upper()} {country_to_flag(country)} {country}",
            mode="lines+markers",
            yaxis="y2",
            line=dict(dash='dot', color=color_map[idx % len(color_map)])
        ))

# Лейаут и подписи
fig.update_layout(
    title="Сравнение динамики: основная метрика (Y1) + LTV/CPI/др. (Y2)",
    xaxis=dict(title="Неделя"),
    yaxis=dict(title=f"{main_metric.upper()} (%)" if 'roas' in main_metric.lower() else main_metric.upper()),
    yaxis2=dict(
        title="CPI / LTV / Adv LTV / Sub LTV",
        overlaying='y',
        side='right',
        showgrid=False,
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ),
    margin=dict(r=30, t=60, l=30, b=30),
    height=600
)

st.plotly_chart(fig, use_container_width=True)
