import pandas as pd
from datetime import date
from app.models import PollenData, PollenType
import numpy as np

def monthly_pollen_forecast(
    pollen_type: PollenType,
    target_month: int,
    years_back: int = 5
):
    """
    Улучшенный прогноз на месяц на основе исторических данных
    """
    
    today = date.today()
    
    # Забираем исторические данные
    qs = PollenData.objects.filter(
        pollen_type=pollen_type,
        date__month=target_month
    )
    
    if not qs:
        return []
    
    # ---------- 1. Подготовка данных ----------
    df = pd.DataFrame.from_records(
        qs.values("date", "concentration")
    )    
    df["date"] = pd.to_datetime(df["date"])

    df["day"] = df["date"].dt.day
    
    # ---------- 2. Агрегация по дням ----------
    daily_profile = (
        df.groupby("day")["concentration"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    
    daily_profile.columns = ["day", "mean", "std", "count"]
    
    # Если данных мало, используем просто среднее по дню
    if len(daily_profile) < 10:
        daily_mean = df.groupby("day")["concentration"].mean().reset_index()
        forecast = []
        
        for _, row in daily_mean.iterrows():
            forecast.append({
                "date": date(today.year, target_month, int(row["day"])),
                "value": round(row["concentration"], 2),
                "type": "forecast",
                "confidence": "low"
            })
        return forecast
    
    # ---------- 3. Прогнозирование с учетом тренда ----------
    forecast = []
    
    daily_profile = df.groupby("day")["concentration"].agg(['mean', 'std', 'count']).reset_index()
    
    # Заполняем пропущенные дни интерполяцией
    all_days = pd.DataFrame({'day': range(1, 32)})
    daily_profile = pd.merge(all_days, daily_profile, on='day', how='left')
    daily_profile['mean'] = daily_profile['mean'].interpolate(method='linear')
    daily_profile['std'] = daily_profile['std'].fillna(daily_profile['std'].mean())
    
    for _, row in daily_profile.iterrows():
        day_num = int(row['day'])
        
        try:
            forecast_date = date(today.year, target_month, day_num)
        except ValueError:
            continue
        
        base_value = row['mean']
        
        if pd.notna(row['std']) and row['std'] > 0:
            noise = np.random.normal(0, min(row['std'], base_value * 0.3))
            forecast_value = max(0, base_value + noise)
        else:
            forecast_value = base_value
        
        if pd.notna(row['count']) and row['count'] >= 3:
            confidence = "high"
        elif pd.notna(row['count']) and row['count'] >= 1:
            confidence = "medium"
        else:
            confidence = "low"
        
        forecast.append({
            "date": forecast_date,
            "value": round(forecast_value, 2),
            "type": "forecast",
            "confidence": confidence,
            "std": round(row['std'], 2) if pd.notna(row['std']) else None
        })
    
    return forecast

def get_seasonal_pattern(pollen_type: PollenType):
    """
    Возвращает сезонный паттерн для типа пыльцы
    """
    qs = PollenData.objects.filter(pollen_type=pollen_type)
    
    if not qs.exists():
        return None
    
    df = pd.DataFrame.from_records(qs.values("date", "concentration"))
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear
    
    monthly_avg = df.groupby("month")["concentration"].mean().reset_index()
    
    return {
        "peak_month": int(monthly_avg.loc[monthly_avg["concentration"].idxmax(), "month"]),
        "peak_value": float(monthly_avg["concentration"].max()),
        "season_start": int(monthly_avg[monthly_avg["concentration"] > monthly_avg["concentration"].mean() * 0.3]["month"].min()),
        "season_end": int(monthly_avg[monthly_avg["concentration"] > monthly_avg["concentration"].mean() * 0.3]["month"].max()),
    }