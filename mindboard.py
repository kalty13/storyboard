import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pycountry
import matplotlib
import matplotlib.cm

st.set_page_config(layout="wide")
st.title("🌍 ROAS (Bar, grad by installs) + LTV/CPI (Lines) — по неделям")

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

ltv_metrics = ['lifetime_value', 'ltv_adv', 'ltv_iap', 'cpi']  # свои названия!
roas_metric = 'roas_w0'

# Глобально по installs за всё время
country_installs = df.groupby('country', as_index=False)['installs'].sum()
country_list = country_installs[country_installs['installs'] > 300].sort_values('installs', ascending=False)
top_countries = country_list['country'].tolist()[:5]

st.markdown("---")
st.subheader("Страны (показаны только с installs > 300 за всё время):")

# Формируем список чекбоксов — ПОД графиком
updated_countries = []
for country in country_list['country']:
    flag = ''
    try:
        country_obj = pycountry.countries.lookup(country)
        flag = ''.join([chr(127397 + ord(c)) for c in country_obj.alpha_2.upper()])
    except Exception:
        pass
    checked = st.checkbox(
        f"{flag} {country} ({int(country_list[country_list['country']==country]['installs'])} installs)",
        value=country in top_countries, key=f"ck_{country}"
    )
    if checked:
        updated_countries.append(country)

if not updated_countries:
    st.warning("Выбери хотя бы одну страну!")
    st.stop()

# Данные только по выбранным странам
df_plot = df[df['country'].isin(updated_countries)].copy()
df_plot[roas_metric] = df_plot[roas_metric] * 100

weeks = sorted(df_plot['week'].unique())
df_plot['week'] = pd.Categorical(df_plot['week'], categories=weeks, ordered=True)

# Цветовая шкала по installs для bar-ов
min_installs = df_plot['installs'].min() if not df_plot.empty else 0
max_installs = df_plot['installs'].max() if not df_plot.empty else 1
colormap = matplotlib.cm.get_cmap('viridis')

def installs_to_color(installs):
    norm_val = (installs - min_installs) / (max_installs - min_installs) if max_installs > min_installs else 0.5
    return matplotlib.colors.rgb2hex(colormap(norm_val))

# --- Сам график
fig = go.Figure()

# ROAS — вертикальные бары (градиент installs)
for country in updated_countries:
    flag = ''
    try:
        country_obj = pycountry.countries.lookup(country)
        flag = ''.join([chr(127397 + ord(c)) for c in country_obj.alpha_2.upper()])
    except Exception:
        pass
    mask = df_plot['country'] == country
    color_vals = [installs_to_color(inst) for inst in df_plot[mask]['installs']]
    fig.add_trace(go.Bar(
        x=df_plot[mask]['week'],
        y=df_plot[mask][roas_metric],
        name=f"ROAS {flag} {country}",
        marker_color=color_vals,
        yaxis='y1',
        opacity=0.88
    ))

# LTV/CPI — линии (Y2)
line_colors = ['#e74c3c', '#3498db', '#27ae60', '#8e44ad', '#f1c40f', '#16a085']
for m_idx, metric in enumerate(ltv_metrics):
    if metric not in df_plot.columns:
        continue
    for country in updated_countries:
        flag = ''
        try:
            country_obj = pycountry.countries.lookup(country)
            flag = ''.join([chr(127397 + ord(c)) for c in country_obj.alpha_2.upper()])
        except Exception:
            pass
        mask = df_plot['country'] == country
        fig.add_trace(go.Scatter(
            x=df_plot[mask]['week'],
            y=df_plot[mask][metric],
            name=f"{metric.upper()} {flag} {country}",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color=line_colors[m_idx % len(line_colors)], width=3, dash='dot'),
            showlegend=True
        ))

# Layout
fig.update_layout(
    barmode="group",
    title="ROAS (Бары, цвет = installs) + LTV/CPI (Линии, правая ось) по неделям",
    xaxis=dict(title="Неделя"),
    yaxis=dict(title="ROAS (%)", side='left', rangemode='tozero'),
    yaxis2=dict(
        title="LTV All / LTV Ad / LTV IAP / CPI ($)",
        overlaying='y',
        side='right',
        showgrid=False,
        rangemode='tozero'
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.05,
        xanchor="center",
        x=0.5,
        font=dict(size=11)
    ),
    margin=dict(r=30, t=60, l=30, b=30),
    height=680,
)

st.plotly_chart(fig, use_container_width=True)
