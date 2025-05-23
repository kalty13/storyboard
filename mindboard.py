import streamlit as st
import pandas as pd
import plotly.express as px
import emoji
import pycountry

st.set_page_config(layout="wide")
st.title("🌍 ROAS by Country — Horizontal Bar Chart")

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

exclude_cols = {"week", "country", "channel"}
metrics = [col for col in df.columns if df[col].dtype in [float, int] and col not in exclude_cols]

choropleth_metric = st.selectbox(
    "Метрика для сравнения (ROAS, LTV и т.д.)",
    metrics,
    index=metrics.index("roas_w0") if "roas_w0" in metrics else 0
)

min_installs = 300
selected_week = st.selectbox("Неделя", sorted(df['week'].unique()), index=0)

df_week = df[(df['week'] == selected_week) & (df['installs'] >= min_installs)].copy()

if "roas" in choropleth_metric.lower():
    df_week[choropleth_metric] = df_week[choropleth_metric] * 100

# Флаги через pycountry
def country_to_flag(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        return ''.join([chr(127397 + ord(c)) for c in country.alpha_2.upper()])
    except Exception:
        return ''

df_week['flag'] = df_week['country'].apply(country_to_flag)
df_week = df_week.sort_values(choropleth_metric, ascending=False)

# Собираем лейблы: Флаг + Название
df_week['country_label'] = df_week['flag'] + ' ' + df_week['country']

fig = px.bar(
    df_week,
    y='country_label',
    x=choropleth_metric,
    orientation='h',
    text=choropleth_metric,
    labels={choropleth_metric: f"{choropleth_metric} (%)", "country_label": "Страна"},
    title=f"{choropleth_metric} by Country — {selected_week}"
)

fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
fig.update_layout(
    yaxis={'categoryorder':'total ascending'},
    autosize=True,
    margin={"r":30,"t":40,"l":0,"b":0},
    height=50 + len(df_week)*30,
    xaxis_title=f"{choropleth_metric} (%)",
    yaxis_title=None
)

st.plotly_chart(fig, use_container_width=True)
