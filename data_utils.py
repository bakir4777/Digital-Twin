"""Демонстрационные данные и проверка загружаемых измерений."""

from io import BytesIO

import numpy as np
import pandas as pd


COLUMNS = {
    "temperature": ("Температура", "°C"),
    "pressure": ("Давление", "бар"),
    "flow": ("Расход ВМР", "м³/ч"),
    "methanol": ("Содержание метанола", "% масс."),
}


def demo_data(hours: int = 24, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = np.arange(hours * 12 + 1) / 12
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=len(t), freq="5min"),
        "temperature": 78 + 4 * (1 - np.exp(-t / 3)) + 0.7 * np.sin(t) + rng.normal(0, 0.2, len(t)),
        "pressure": 1.15 + 0.03 * np.sin(t / 2) + rng.normal(0, 0.008, len(t)),
        "flow": 12 + 0.8 * np.sin(t / 3) + rng.normal(0, 0.15, len(t)),
        "methanol": np.clip(18 * np.exp(-t / 8) + 0.4 + rng.normal(0, 0.12, len(t)), 0, 100),
    })


def validate_data(frame: pd.DataFrame) -> pd.DataFrame:
    required = ["timestamp", *COLUMNS]
    missing = [name for name in required if name not in frame.columns]
    if missing:
        raise ValueError("Отсутствуют столбцы: " + ", ".join(missing))
    data = frame[required].copy()
    if data.empty:
        raise ValueError("Выбранный лист не содержит измерений.")
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")
    if data["timestamp"].isna().any():
        raise ValueError("Столбец времени содержит пустые или некорректные даты.")
    for name, (label, _) in COLUMNS.items():
        data[name] = pd.to_numeric(data[name].astype(str).str.replace(",", ".", regex=False), errors="coerce")
        if not np.isfinite(data[name]).all():
            raise ValueError(f"«{label}»: обнаружены пустые или некорректные числа.")
    if (data[["pressure", "flow"]] < 0).any().any():
        raise ValueError("Давление и расход не могут быть отрицательными.")
    if not data["methanol"].between(0, 100).all():
        raise ValueError("Содержание метанола должно быть в диапазоне 0–100 % масс.")
    if data["timestamp"].duplicated().any():
        raise ValueError("Найдены повторяющиеся отметки времени. Оставьте одну строку на каждую отметку.")
    return data.sort_values("timestamp").reset_index(drop=True)


def to_excel(data: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        data.to_excel(writer, index=False, sheet_name="Измерения")
    return buffer.getvalue()
