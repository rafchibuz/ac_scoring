# src/visualizer.py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

def plot_basic_telemetry(df):
    """
    Анализ движения: Дистанция, Скорость и Ускорение.
    """
    time = df['Time']
    speed_kmh = df['Ground Speed']
    accel_g = df['CG Accel Longitudinal']

    # Расчет дистанции
    dt = time.diff().fillna(time.iloc[1] - time.iloc[0])
    distance = ((speed_kmh / 3.6) * dt).cumsum()

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    
    ax1.plot(time, distance, color='blue', label='Дистанция (м)')
    ax1.set_ylabel('Дистанция [м]')
    ax1.set_title('Общий анализ движения')
    ax1.grid(True, alpha=0.3)

    ax2.plot(time, speed_kmh, color='green', label='Скорость (км/ч)')
    ax2.set_ylabel('Скорость [км/ч]')
    ax2.grid(True, alpha=0.3)

    ax3.plot(time, accel_g, color='red', label='Ускорение (G)', alpha=0.7)
    ax3.axhline(0, color='black', linestyle='--', linewidth=1)
    ax3.set_ylabel('Ускорение [G]')
    ax3.set_xlabel('Время [с]')
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

def plot_gg_diagram(df, comfort_limit=0.4):
    """
    G-G Diagram: Распределение продольных и поперечных перегрузок.
    """
    lat_accel = df['CG Accel Lateral']
    long_accel = df['CG Accel Longitudinal']

    plt.figure(figsize=(8, 8))
    plt.scatter(lat_accel, long_accel, c='royalblue', alpha=0.2, s=10)
    
    # Оси координат
    plt.axhline(0, color='black', linewidth=1)
    plt.axvline(0, color='black', linewidth=1)

    # Зона комфорта
    circle = plt.Circle((0, 0), comfort_limit, color='green', fill=False, 
                        linestyle='--', label=f'Зона комфорта ({comfort_limit}G)')
    plt.gca().add_patch(circle)

    limit = 2.0
    plt.xlim(-limit, limit)
    plt.ylim(-limit, limit)
    plt.gca().set_aspect('equal')
    
    plt.title('G-G Diagram: Распределение перегрузок')
    plt.xlabel('Боковое (Lateral G) — Повороты')
    plt.ylabel('Продольное (Longitudinal G) — Газ/Тормоз')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.show()

def plot_pedal_dynamics(df):
    """
    Анализ работы педалями: позиции и резкость (Jerk).
    """
    t = df['Time']
    # Расчет резкости прямо здесь, если её нет в DF
    t_jerk = np.gradient(df['Throttle Pos'], t)
    b_jerk = np.gradient(df['Brake Pos'], t)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    ax1.plot(t, df['Throttle Pos'], color='green', alpha=0.6, label='Газ (%)')
    ax1.plot(t, df['Brake Pos'], color='red', alpha=0.6, label='Тормоз (%)')
    ax1.set_ylabel('Позиция [%]')
    ax1.set_title('Динамика работы педалями')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.2)

    ax2.plot(t, t_jerk, color='darkgreen', alpha=0.7, label='Резкость газа')
    ax2.plot(t, b_jerk, color='darkred', alpha=0.7, label='Резкость тормоза')
    ax2.set_ylim(-1000, 1000)
    ax2.set_ylabel('Скорость нажатия [%/с]')
    ax2.set_xlabel('Время [с]')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.show()

def plot_safety_systems(df):
    """
    Визуализация срабатывания ABS и TC.
    """
    t = df['Time']
    abs_active = df['ABS Active']
    tc_active = df['TC Active']

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    ax1.fill_between(t, 0, abs_active, color='red', alpha=0.5, label='ABS')
    ax1.plot(t, df['Brake Pos'] / 100, color='black', alpha=0.2, label='Тормоз')
    ax1.set_title('Срабатывание ABS (Блокировка)')
    ax1.legend()

    ax2.fill_between(t, 0, tc_active, color='orange', alpha=0.5, label='TC')
    ax2.plot(t, df['Throttle Pos'] / 100, color='black', alpha=0.2, label='Газ')
    ax2.set_title('Срабатывание TC (Пробуксовка)')
    ax2.set_xlabel('Время [с]')
    ax2.legend()

    plt.tight_layout()
    plt.show()

def plot_colored_scoring(df, report, speed_limit=130):
    """
    Финальный график: скорость, окрашенная в зависимости от баллов вождения.
    """
    t_points = np.array(df['Time'])
    v_points = np.array(df['Ground Speed'])
    
    # Извлекаем историю баллов из отчета
    seg_scores = report['scores_history']
    # Временные метки для баллов (предполагаем равномерное распределение)
    seg_times = np.linspace(t_points.min(), t_points.max(), len(seg_scores))

    colors_line = []
    for i, t in enumerate(t_points):
        # Находим ближайший балл по времени
        idx = np.abs(seg_times - t).argmin()
        score = seg_scores[idx]

        if score >= 85: colors_line.append('green')
        elif score >= 65: colors_line.append('yellow')
        elif score >= 40: colors_line.append('orange')
        else: colors_line.append('red')

    points = np.array([t_points, v_points]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    lc = LineCollection(segments, colors=colors_line, linewidth=3, zorder=5)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

    # График скорости
    ax1.add_collection(lc)
    ax1.set_xlim(t_points.min(), t_points.max())
    ax1.set_ylim(0, v_points.max() * 1.1)
    ax1.plot(t_points, v_points, color='black', alpha=0.1)
    ax1.axhline(speed_limit, color='red', linestyle=':', alpha=0.5, label='Лимит')
    ax1.set_title("Оценка стиля вождения по ходу поездки")
    ax1.set_ylabel("Скорость [км/ч]")

    # График баллов
    ax2.plot(seg_times, seg_scores, color='#1f77b4', linewidth=2)
    ax2.fill_between(seg_times, 0, seg_scores, color='#1f77b4', alpha=0.2)
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("Баллы")
    ax2.set_xlabel("Время [с]")
    ax2.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.show()

def plot_style_distribution(report):
    """
    Круговая диаграмма распределения стилей.
    """
    scores = np.array(report['scores_history'])
    
    styles = []
    for s in scores:
        if s >= 85: styles.append("Безопасный")
        elif s >= 65: styles.append("Активный")
        elif s >= 40: styles.append("Агрессивный")
        else: styles.append("Опасный")

    style_counts = pd.Series(styles).value_counts()
    
    plt.figure(figsize=(8, 6))
    colors = ['#2ca02c', '#ff7f0e', '#d62728', '#9467bd']
    style_counts.plot(kind='pie', autopct='%1.1f%%', colors=colors, startangle=140)
    plt.title("Распределение стилей вождения")
    plt.ylabel("")
    plt.show()
    
def plot_penalty_stack(report):
    """
    Стек-график: показывает, какие именно нарушения съедали баллы во времени.
    """
    if 'penalty_history' not in report:
        print("Ошибка: В отчете нет данных о детализации штрафов.")
        return

    p_history = report['penalty_history']
    times = report['seg_times']

    plt.figure(figsize=(12, 6))
    
    # Цвета для соответствия категориям
    labels = list(p_history.keys())
    values = list(p_history.values())
    colors = ['#ff4d4d', '#3399ff', '#ffcc00', '#9933ff', '#00cc66', '#444444']

    plt.stackplot(times, values, labels=labels, alpha=0.8, colors=colors)

    plt.title("Анализ причин снижения баллов (Распределение штрафов)", fontsize=14)
    plt.ylabel("Суммарный штраф (вычитается из 100)")
    plt.xlabel("Время (сек)")
    plt.legend(loc='upper left', ncol=2)
    plt.grid(True, alpha=0.2)
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.show()

def plot_penalty_pie(report):
    """
    Круговая диаграмма: итоговое влияние каждого фактора за всю поездку.
    """
    if 'penalty_history' not in report: return

    p_history = report['penalty_history']
    
    # Считаем сумму штрафов по каждой категории
    total_damage = {k: sum(v) for k, v in p_history.items()}
    # Берем только те, где штраф > 0
    active_damage = {k: v for k, v in total_damage.items() if v > 0}

    if not active_damage:
        print("Идеальная поездка! Штрафов нет.")
        return

    plt.figure(figsize=(8, 8))
    # Рисуем Pie chart
    plt.pie(active_damage.values(), labels=active_damage.keys(), autopct='%1.1f%%',
            startangle=140, shadow=True, explode=[0.05]*len(active_damage))
    
    plt.title("Главные виновники снижения твоего рейтинга", fontsize=14)
    plt.tight_layout()
    plt.show()

    # Текстовое резюме
    main_culprit = max(active_damage, key=active_damage.get)
    print(f"\nАНАЛИЗ ЗАВЕРШЕН: Твой главный враг — '{main_culprit}'.")
    print(f"Именно этот параметр чаще всего тянул твой рейтинг вниз.")