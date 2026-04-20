# src/rating.py
import numpy as np

def calculate_final_rating(report, df_ref):
    """
    Рассчитывает итоговый рейтинг водителя.
    Штраф за ДТП удален из расчетов, но события ДТП фиксируются.
    """
    avg_score = report['avg_score']
    scores_list = report['scores_history']
    p_hist = report['penalty_history']
    seg_times = report['seg_times']
    
    # --- 1. ПОИСК ДТП (Информационно) ---
    crashes = df_ref[df_ref['total_g'] > 3.5]
    crash_events = []
    last_t = -10
    for _, row in crashes.iterrows():
        if row['Time'] - last_t > 5:
            crash_events.append(row)
        last_t = row['Time']

    # --- 2. РАСЧЕТ ПОТЕРЬ (LOSS) ---
    
    # А. Потеря от среднего балла (множитель 0.05)
    loss_avg = (100 - avg_score) * 0.05

    # Б. Потеря от "Красных зон" (Штрафуем, если больше 1% времени в опасной зоне)
    scores_arr = np.array(scores_list)
    danger_zone_pct = (scores_arr < 40).mean() * 100
    loss_danger = (danger_zone_pct - 1) * 0.4 if danger_zone_pct > 1 else 0

    # В. Анализ систем (ABS/TC) на скорости > 45 км/ч
    high_speed_incidents = 0
    sys_penalties = p_hist.get('Системы (ABS/TC)', [])
    
    for i, p_val in enumerate(sys_penalties):
        if p_val > 0:
            t_event = seg_times[i]
            v_at_t = df_ref[abs(df_ref['Time'] - t_event) < 0.5]['Ground Speed'].mean()
            if v_at_t > 45:
                high_speed_incidents += 1

    incident_ratio = (high_speed_incidents / len(seg_times)) * 100 if len(seg_times) > 0 else 0
    loss_systems = (incident_ratio - 15) * 0.5 if incident_ratio > 15 else 0

    # --- 3. БОНУС ЗА АККУРАТНОСТЬ ---
    bonus = 0
    if danger_zone_pct < 5 and avg_score > 90:
        bonus = 7.0  
    elif danger_zone_pct < 10 and avg_score > 80:
        bonus = 3.5  

    # --- 4. ИТОГ (Без loss_crash) ---
    raw_score = 100 - (loss_avg + loss_danger + loss_systems)
    final_score = min(100, max(0, raw_score + bonus))

    return {
        "final_score": round(final_score, 1),
        "bonus_applied": bonus,
        "details": {
            "loss_avg": round(loss_avg, 2),
            "loss_danger": round(loss_danger, 2),
            "loss_systems": round(loss_systems, 2)
        },
        "crash_count": len(crash_events)
    }

def print_rating_report(rating_results):
    """Красивый вывод вердикта в консоль."""
    score = rating_results['final_score']
    details = rating_results['details']
    crash_count = rating_results['crash_count']
    
    print("\n" + "="*40)
    print("      ФИНАЛЬНЫЙ ВЕРДИКТ ВОДИТЕЛЯ")
    print("="*40)
    
    # Секция ДТП (только если они были)
    if crash_count > 0:
        print(f"ОБНАРУЖЕНО ДТП: {crash_count} шт.")
        print("-" * 40)

    print(f"ИТОГОВЫЙ РЕЙТИНГ:      {score}%")
    
    if rating_results['bonus_applied'] > 0:
        print(f"БОНУС ЗА АККУРАТНОСТЬ: +{rating_results['bonus_applied']}% 🟢")
    
    print("-" * 40)
    print("ДЕТАЛИЗАЦИЯ ПОТЕРЬ:")
    print(f" - Средний балл:      -{details['loss_avg']}%")
    print(f" - Опасные маневры:   -{details['loss_danger']}%")
    print(f" - Системы (>45км/ч): -{details['loss_systems']}%")
    print("-" * 40)

    # Категория доступа
    if score > 90: status = "⭐⭐⭐⭐⭐"
    elif score > 75: status = "⭐⭐⭐⭐☆"
    elif score > 50: status = "⭐⭐⭐☆☆"
    elif score > 25: status = "⭐⭐☆☆☆"
    else: status = "⭐☆☆☆☆"

    print(f"ОБЩИЙ РЕЙТИНГ {status}")
    print("="*40 + "\n")