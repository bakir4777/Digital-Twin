"""Streamlit: мониторинг процесса отдувки метанола."""

from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

from data_utils import COLUMNS, demo_data, to_excel, validate_data


st.set_page_config(page_title="Отдувка метанола", page_icon="📈", layout="wide")
st.title("Отдувка метанола из ВМР")
st.caption("Технологические параметры водометанольного раствора")

with st.sidebar:
    st.header("Источник данных")
    source = st.radio("Режим", ["Демонстрация", "Excel"])
    st.download_button("Скачать пример Excel", to_excel(demo_data()),
                       file_name="methanol_example.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.caption("Формат загрузки: .xlsx. Единицы измерения должны соответствовать шаблону.")

if source == "Демонстрация":
    hours = st.sidebar.slider("Длительность, ч", 6, 72, 24, 6)
    data = demo_data(hours)
    st.info("Синтетические данные для демонстрации интерфейса. Они не являются расчётной моделью процесса.")
else:
    uploaded = st.sidebar.file_uploader("Загрузить измерения", type=["xlsx"])
    if uploaded is None:
        st.info("Загрузите Excel-файл или выберите демонстрационный режим.")
        st.stop()
    try:
        workbook = pd.ExcelFile(BytesIO(uploaded.getvalue()), engine="openpyxl")
        sheet = st.sidebar.selectbox("Лист", workbook.sheet_names)
        raw = pd.read_excel(workbook, sheet_name=sheet)
        st.sidebar.markdown("**Сопоставление столбцов**")
        mapping = {}
        for key, label in [("timestamp", "Время"), *[(k, f"{v[0]}, {v[1]}") for k, v in COLUMNS.items()]]:
            options = list(raw.columns)
            selected = st.sidebar.selectbox(label, options,
                                            index=options.index(key) if key in options else 0,
                                            key=f"column_{key}")
            mapping[key] = selected
        if len(set(mapping.values())) != len(mapping):
            raise ValueError("Для каждого параметра выберите отдельный столбец.")
        data = validate_data(pd.DataFrame({key: raw[col] for key, col in mapping.items()}))
    except Exception as exc:
        st.error(f"Не удалось прочитать данные: {exc}")
        st.stop()
    st.success(f"Загружено измерений: {len(data)}")

st.sidebar.header("Период отображения")
times = data["timestamp"].tolist()
if len(times) > 1:
    start, end = st.sidebar.select_slider("Интервал времени", options=times,
                                          value=(times[0], times[-1]),
                                          format_func=lambda t: t.strftime("%d.%m %H:%M"))
    view = data[data["timestamp"].between(start, end)]
else:
    view = data

st.caption(f"Период: {view.timestamp.iloc[0]:%d.%m.%Y %H:%M} — {view.timestamp.iloc[-1]:%d.%m.%Y %H:%M} · Точек: {len(view)}")
metrics = st.columns(4)
for column, (name, (label, unit)) in zip(metrics, COLUMNS.items()):
    column.metric(label, f"{view[name].iloc[-1]:.2f} {unit}")
st.caption("Карточки показывают последнее измерение в выбранном интервале.")

colors = ["#ef8354", "#6c63ff", "#159a9c", "#c84b85"]
for i, (name, (label, unit)) in enumerate(COLUMNS.items()):
    if i % 2 == 0:
        row = st.columns(2)
    fig = px.line(view, x="timestamp", y=name, title=label,
                  labels={"timestamp": "Время", name: f"{label}, {unit}"},
                  color_discrete_sequence=[colors[i]], markers=len(view) < 2)
    fig.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=50, b=20), height=320)
    row[i % 2].plotly_chart(fig, width="stretch")

with st.expander("Измерения и статистика"):
    st.dataframe(view, hide_index=True, width="stretch")
    stats = view[list(COLUMNS)].agg(["min", "mean", "max"]).rename(
        index={"min": "Минимум", "mean": "Среднее", "max": "Максимум"},
        columns={k: f"{v[0]}, {v[1]}" for k, v in COLUMNS.items()})
    st.dataframe(stats.style.format("{:.2f}"), width="stretch")
st.download_button("Скачать выбранные данные", to_excel(view), file_name="methanol_filtered.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
