# src/dataset_creator.py
import pandas as pd
import numpy as np

def create_training_dataset(df, report, output_filename="output/scoring_dataset.csv"):
    """
    Объединяет физические данные и оценки в один файл для обучения ИИ.
    """
    # 1. Выбираем основные признаки для обучения
    features = [
        'Ground Speed', 'Steering Angle', 'Throttle Pos', 'Brake Pos',
        'CG Accel Lateral', 'CG Accel Longitudinal', 'total_g',
        'throttle_jerk', 'brake_jerk', 'steer_speed'
    ]
    
    # 2. Добавляем Slip Angle по осям (Feature Engineering)
    # Задняя ось (основной маркер дрифта)
    rear_cols = ['Tire Slip Angle RL', 'Tire Slip Angle RR']
    if all(c in df.columns for c in rear_cols):
        df['avg_slip_rear'] = df[rear_cols].abs().mean(axis=1)
        features.append('avg_slip_rear')
    
    # Передняя ось (маркер недостаточной поворачиваемости)
    front_cols = ['Tire Slip Angle FL', 'Tire Slip Angle FR']
    if all(c in df.columns for c in front_cols):
        df['avg_slip_front'] = df[front_cols].abs().mean(axis=1)
        features.append('avg_slip_front')

    # 3. Создаем обучающую выборку
    dataset = df[features].copy()

    # 4. Привязываем баллы (Target)
    scores_history = report['scores_history']
    # Растягиваем массив оценок до длины основного датафрейма (интерполяция)
    xp = np.linspace(0, len(df), len(scores_history))
    x = np.arange(len(df))
    dataset['target_score'] = np.interp(x, xp, scores_history)

    # 5. Сохранение
    dataset.to_csv(output_filename, index=False)
    print(f"Датасет создан! Признаки: {features}")
    print(f"Сохранено строк: {len(dataset)}")
    return dataset