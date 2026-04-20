# src/metrics.py
import numpy as np
import pandas as pd

def calculate_jerk(series, time_series):
    return np.abs(np.gradient(series, time_series))

def get_driving_style(score):
    if score >= 85: return "Безопасный"
    elif score >= 65: return "Активный"
    elif score >= 40: return "Агрессивный"
    return "Опасный"

def calculate_stepped_speed_penalty(speed, limit, weight):
    """
    Расчет штрафа за скорость по ступеням 5 км/ч с геометрической прогрессией.
    """
    if speed <= limit:
        return 0
    
    # 1. Считаем количество пройденных ступеней (каждые 5 км/ч)
    # Например: при лимите 110 и скорости 122, превышение 12. 
    # Это 2 полные ступени и кусочек третьей.
    excess = speed - limit
    steps = excess / 5.0  
    
    # 2. Геометрическая прогрессия. 
    # Коэффициент 1.5 означает, что каждая следующая ступень на 50% тяжелее предыдущей.
    # Можно менять 1.5 на 2.0 для еще более дикого роста.
    penalty_factor = (2 ** steps) - 1
    
    # 3. Масштабируем фактор на вес параметра
    # Умножаем на 5, чтобы начальное превышение (на 5 км/ч) уже было заметным
    p = penalty_factor * (weight * 0.2) 
    
    return min(p, weight)

def analyze_telemetry(df):
    t = df['Time'].values
    
    # 1. Подготовка параметров
    df['throttle_jerk'] = calculate_jerk(df['Throttle Pos'], t)
    df['brake_jerk'] = calculate_jerk(df['Brake Pos'], t)
    df['steer_speed'] = calculate_jerk(df['Steering Angle'], t)
    
    df['total_g'] = np.sqrt(df['CG Accel Lateral']**2 + df['CG Accel Longitudinal']**2)
    df['lat_g'] = np.abs(df['CG Accel Lateral'])
    df['long_g'] = df['CG Accel Longitudinal']
    
    rear_slip_cols = ['Tire Slip Angle RL', 'Tire Slip Angle RR']
    front_slip_cols = ['Tire Slip Angle FL', 'Tire Slip Angle FR']

    # --- 2. ВЕСА ---
    WEIGHTS = {
        'slip': 35.0,
        'speed': 30.0,
        'accel': 25.0,
        'jerk': 10.0,
        'lat_g': 5.0,
        'systems': 5.0
    }

    LIMITS = {
        'slip': 5.0,
        'speed': 110,
        'accel': 0.3,
        'jerk': 300,
        'lat_g': 0.6
    }

    TOTAL_WEIGHT_SUM = sum(WEIGHTS.values())

    def calc_penalty(value, limit, weight, exponential=False):
        if value <= limit: return 0
        ratio = (value - limit) / limit
        if exponential:
            p = (ratio ** 2.0) * weight 
        else:
            p = ratio * weight
        return min(p, weight)

    ordered_keys = [
        'Снос/Занос (Slip)', 'Скорость', 'Опасный разгон', 
        'Резкость педалей', 'Боковые перегрузки', 'Системы (ABS/TC)'
    ]
    p_history = {k: [] for k in ordered_keys}
    scores = []
    seg_times = []
    
    window_size = 60 
    step_size = 10 

    for i in range(0, len(df) - window_size, step_size):
        win = df.iloc[i : i + window_size]
        
        # Сбор данных
        speed_val = win['Ground Speed'].max()
        
        slip_val = max(
            win[rear_slip_cols].abs().mean(axis=1).max() if all(c in win for c in rear_slip_cols) else 0,
            win[front_slip_cols].abs().mean(axis=1).max() if all(c in win for c in front_slip_cols) else 0
        )
        
        accel_val = max(0, win['long_g'].max())
        jerk_val = max(win['throttle_jerk'].max(), win['brake_jerk'].max())
        lat_g_val = win['lat_g'].max()

        # --- РАСЧЕТ ШТРАФОВ (Скорость теперь ступенчатая) ---
        p_speed = calculate_stepped_speed_penalty(speed_val, LIMITS['speed'], WEIGHTS['speed'])
        
        p_slip = calc_penalty(slip_val, LIMITS['slip'], WEIGHTS['slip'])
        p_accel = calc_penalty(accel_val, LIMITS['accel'], WEIGHTS['accel'], exponential=True)
        p_jerk = calc_penalty(jerk_val, LIMITS['jerk'], WEIGHTS['jerk'])
        p_lat_g = calc_penalty(lat_g_val, LIMITS['lat_g'], WEIGHTS['lat_g'])
        p_sys = WEIGHTS['systems'] if (win['ABS Active'].any() or win['TC Active'].any()) else 0

        # Итоги
        total_p = p_slip + p_speed + p_accel + p_jerk + p_lat_g + p_sys
        penalty_percent = (total_p / TOTAL_WEIGHT_SUM) * 100
        
        scores.append(max(0, 100 - penalty_percent))
        seg_times.append(win['Time'].iloc[-1])

        p_history['Снос/Занос (Slip)'].append((p_slip / TOTAL_WEIGHT_SUM) * 100)
        p_history['Скорость'].append((p_speed / TOTAL_WEIGHT_SUM) * 100)
        p_history['Опасный разгон'].append((p_accel / TOTAL_WEIGHT_SUM) * 100)
        p_history['Резкость педалей'].append((p_jerk / TOTAL_WEIGHT_SUM) * 100)
        p_history['Боковые перегрузки'].append((p_lat_g / TOTAL_WEIGHT_SUM) * 100)
        p_history['Системы (ABS/TC)'].append((p_sys / TOTAL_WEIGHT_SUM) * 100)

    avg_score = np.mean(scores) if scores else 0
    return {
        "avg_score": round(avg_score, 1),
        "style": get_driving_style(avg_score),
        "crash_detected": df['total_g'].max() > 3.5,
        "max_g": round(df['total_g'].max(), 2),
        "scores_history": scores,
        "penalty_history": p_history,
        "seg_times": seg_times
    }