# src/processor.py
import pandas as pd
from pathlib import Path

def process_motec_log(input_file, output_path):
    """
    Парсит сырой CSV из Assetto Corsa, удаляет метаданные и единицы измерения,
    оставляя только чистые числовые данные.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    target_columns = [
        "Time", "Ground Speed", "Steering Angle", "Throttle Pos", 
        "Brake Pos", "CG Accel Lateral", "CG Accel Longitudinal", 
        "CG Accel Vertical", "Chassis Yaw Rate", "ABS Active", 
        "TC Active", "Tire Slip Angle FL", "Tire Slip Angle FR", 
        "Tire Slip Angle RL", "Tire Slip Angle RR"
    ]

    # 1. Поиск строки заголовка
    header_idx = 0
    with open(input_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if '"Time"' in line or 'Time,' in line:
                header_idx = i
                break

    # 2. Загрузка (пропускаем метаданные до заголовка)
    df = pd.read_csv(input_file, skiprows=header_idx, quotechar='"', skipinitialspace=True, low_memory=False)

    # 3. Удаляем первую строку (там всегда единицы измерения: s, km/h...)
    df = df.drop(0).reset_index(drop=True)

    # 4. Чистим названия колонок от кавычек
    df.columns = [c.replace('"', '').strip() for c in df.columns]

    # 5. Оставляем только нужные колонки и переводим в числа
    available_cols = [c for c in target_columns if c in df.columns]
    filtered_df = df[available_cols].apply(pd.to_numeric, errors='coerce')

    # 6. Сохранение
    filtered_df.to_csv(output_path, index=False)
    return filtered_df  # Возвращаем DF, чтобы можно было сразу работать дальше