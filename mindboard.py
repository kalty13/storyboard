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

# Метрики для второй оси — обязательно проверь названия!
ltv_metrics = ['lifetime_value', 'ltv_adv', 'ltv_iap', 'cpi']  # свои названия!
roas_metric = 'roas_w0'

# 1. Глобально по installs за всё время — только страны >300
country_installs = df.groupby('country', as_index=False)['installs'].sum()
country_list = country_installs[country_installs['installs'] > 300].sort_values('installs', ascending=False)
top_countries = country_list['country'].tolist()[:5]

# 2. Готовим фильтр по странам (выведем чекбоксы ПОД графиком)
selected_countries = top_countries  # временно, покажем все чекбоксы ниже

# 3. Подготовка данных для графика
df['roas_w0'] = df['roas_w0'] * 100
weeks = sorted(df['week'].unique())

# 4. Фильтруем только выбранные страны
df_plot = df[df['country'].isin(selected_countries)].copy()
df_plot['week'] = pd.Categorical(df_plot['week'], categories=weeks, ordered=True)

# 5. Для цвета bar-ов по installs:
min_installs = df_plot['installs'].min()
max_installs = df_plot['installs'].max()
colormap = matplotlib.cm.get_cmap('viridis')

def installs_to_color(installs):
    norm_val = (installs - min_installs) / (max_installs - min_installs) if max_installs > min_installs else 0.5
    return matplotlib.colors.rgb2hex(colormap(norm_val))

# 6. Строим график
fig = go.Figure()

# ROAS — бар-чарт с градиентом по installs
for country in selected_countries:
    flag = ''
    try:
        country_obj = pycountry.countries.lookup(country)
        flag = ''.join([chr(127397 + ord(c)) for c in country_obj.alpha_2.upper()])
    except Exception:
        pass
    mask = df_plot['country'] == country
    color_vals = [installs_to_color(inst) for inst in df_plot[mask]['installs']]
    # Бары: 1 bar = 1 неделя
    fig.add_trace(go.Bar(
        x=df_plot[mask]['week'],
        y=df_plot[mask][roas_metric],
        name=f"ROAS {flag} {country}",
        marker_color=color_vals,
        yaxis='y1',
        opacity=0.88
    ))

# LTV, CPI и др. — линии (Y2)
line_colors = ['#e74c3c', '#3498db', '#27ae60', '#8e44ad', '#f1c40f', '#16a085']
for m_idx, metric in enumerate(ltv_metrics):
    if metric not in df_plot.columns:
        continue
    for country in selected_countries:
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

# Оси и layout
fig.update_layout(
    barmode="group",
    title="ROAS (Бары, цвет = installs) + LTV/CPI (Линии) по неделям",
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
        y=1.05,
        xanchor="center",
        x=0.5,
        font=dict(size=11)
    ),
    margin=dict(r=30, t=60, l=30, b=30),
    height=640
)

st.plotly_chart(fig, use_container_width=True)

# =========== Список чекбоксов по странам ПОД графиком ==========
st.markdown("---")
st.subheader("Страны (показаны только с installs > 300 за всё время):")

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

# Если пользователь изменил выбор — обновим график (перезапусти страницу или сохрани selected_countries в session_state)
if set(updated_countries) != set(selected_countries):
    st.info("Измени выбор стран — нажми 'Rerun' или обнови страницу для обновления графика!")

