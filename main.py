from src.processor import process_motec_log
from src.metrics import analyze_telemetry
from src.dataset_creator import create_training_dataset
from src.visualizer import plot_basic_telemetry, plot_style_distribution, plot_penalty_stack, plot_gg_diagram, plot_pedal_dynamics, plot_safety_systems, plot_colored_scoring, plot_style_distribution
from src.rating import calculate_final_rating, print_rating_report

def main():
    raw_path = 'data/horizon_life_moscow_&_delic_m5_f90_renatko_&_rafchibus_&_stint_1.csv'
    clean_path = 'output/processed_dataset.csv'

    # 1. Очистка
    df = process_motec_log(raw_path, clean_path)

    # 2. Анализ
    report = analyze_telemetry(df)

    # 3. Получение датасета для обучения
    dataset = create_training_dataset(df, report)

    #plot_basic_telemetry(df)
    plot_gg_diagram(df)
    #plot_pedal_dynamics(df)
    #plot_safety_systems(df)
    plot_colored_scoring(df, report)
    plot_style_distribution(report)
    plot_penalty_stack(report)
    rating_results = calculate_final_rating(report, df)
    print_rating_report(rating_results)
    # 4. Вывод вердикта
    print("=== ОТЧЕТ ПО ВОДИТЕЛЮ ===")
    print(f"Общий стиль вождения: {report['style']}")
    print(f"Средний балл:  {report['avg_score']}/100")

if __name__ == "__main__":
    main()