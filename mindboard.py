import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pycountry
import matplotlib
import matplotlib.cm

st.set_page_config(layout="wide")
st.title("🌍 ROAS vs LTV/CPI — Динамика по неделям + вес installs")

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

# Метрики для второй оси
ltv_metrics = ['lifetime_value', 'ltv_adv', 'ltv_iap', 'cpi']  # под свои названия!
all_metrics = ['roas_w0'] + ltv_metrics

# Глобальный фильтр по installs за всё время
country_installs = df.groupby('country', as_index=False)['installs'].sum()
country_list = country_installs[country_installs['installs'] > 300].sort_values('installs', ascending=False)
top_countries = country_list['country'].tolist()[:5]

st.subheader("Выберите страны для сравнения (installs > 300 за всё время):")
selected_countries = []
for country in country_list['country']:
    flag = ''
    try:
        country_obj = pycountry.countries.lookup(country)
        flag = ''.join([chr(127397 + ord(c)) for c in country_obj.alpha_2.upper()])
    except Exception:
        pass
    checked = st.checkbox(f"{flag} {country} ({int(country_list[country_list['country']==country]['installs'])} installs)", 
                          value=country in top_countries, key=country)
    if checked:
        selected_countries.append(country)

if not selected_countries:
    st.warning("Выбери хотя бы одну страну!")
    st.stop()

# Фильтр по странам и installs (по неделям)
df_view = df[df['country'].isin(selected_countries)].copy()
df_view['roas_w0'] = df_view['roas_w0'] * 100

# Сортируем недели
weeks = sorted(df_view['week'].unique())
df_view['week'] = pd.Categorical(df_view['week'], categories=weeks, ordered=True)

# Для градиента по installs
min_installs = df_view['installs'].min()
max_installs = df_view['installs'].max()
colormap = matplotlib.cm.get_cmap('viridis')

def installs_to_color(installs):
    norm_val = (installs - min_installs) / (max_installs - min_installs) if max_installs > min_installs else 0.5
    return matplotlib.colors.rgb2hex(colormap(norm_val))

def installs_to_width(installs):
    # Ширина линии от 2 до 6, пропорционально installs
    if max_installs > min_installs:
        return 2 + 4 * (installs - min_installs) / (max_installs - min_installs)
    else:
        return 4

# График: комбинированный (ROAS слева, остальные — справа)
fig = go.Figure()

for country in selected_countries:
    country_mask = df_view['country'] == country
    flag = ''
    try:
        country_obj = pycountry.countries.lookup(country)
        flag = ''.join([chr(127397 + ord(c)) for c in country_obj.alpha_2.upper()])
    except Exception:
        pass
    label = f"{flag} {country}"

    # Градиент и ширина по installs (берём installs по каждой неделе, список)
    installs_vals = df_view[country_mask]['installs'].tolist()
    color_vals = [installs_to_color(inst) for inst in installs_vals]
    width_vals = [installs_to_width(inst) for inst in installs_vals]

    # ROAS — левая ось, индивидуальный стиль для каждой точки линии
    fig.add_trace(go.Scatter(
        x=df_view[country_mask]['week'],
        y=df_view[country_mask]['roas_w0'],
        name=f"ROAS (%) {label}",
        mode="lines+markers",
        yaxis="y1",
        # Только для всего trace можно color/width, но можно разбить на сегменты если хочется прям “градиент”
        line=dict(color=installs_to_color(df_view[country_mask]['installs'].mean()), width=installs_to_width(df_view[country_mask]['installs'].mean())),
        marker=dict(
            color=color_vals,
            size=10,
            line=dict(width=2, color='white')
        ),
        showlegend=True,
    ))

    # LTV All, Ad, IAP, CPI — правая ось
    for m_idx, metric in enumerate(ltv_metrics):
        if metric not in df_view.columns:
            continue
        fig.add_trace(go.Scatter(
            x=df_view[country_mask]['week'],
            y=df_view[country_mask][metric],
            name=f"{metric.upper()} {label}",
            mode="lines+markers",
            yaxis="y2",
            line=dict(dash='dot', color=f"rgba(160,160,{100 + 30*m_idx},0.7)"),
            marker=dict(size=7),
            showlegend=(country == selected_countries[0])
        ))

# Layout с осями и цветовой легендой
fig.update_layout(
    title="ROAS (%) — цвет/толщина по installs, LTV/CPI ($) — правая ось",
    xaxis=dict(title="Неделя"),
    yaxis=dict(title="ROAS (%)", side='left'),
    yaxis2=dict(
        title="LTV All / LTV Ad / LTV IAP / CPI ($)",
        overlaying='y',
        side='right',
        showgrid=False,
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5,
        font=dict(size=11)
    ),
    margin=dict(r=30, t=60, l=30, b=30),
    height=600
)

st.plotly_chart(fig, use_container_width=True)
