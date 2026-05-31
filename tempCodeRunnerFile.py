import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
import os
from fol_solver import load_metrics

# Загружаем метрики для четырёх сценариев
base_dir = os.path.dirname(os.path.abspath(__file__))
metrics_base = load_metrics(os.path.join(base_dir, "results/baseline/fol_metrics/"))
metrics_info = load_metrics(os.path.join(base_dir, "results/informational/fol_metrics/"))
metrics_ego  = load_metrics(os.path.join(base_dir, "results/egoistic/fol_metrics/"))
metrics_targ = load_metrics(os.path.join(base_dir, "results/targeted/fol_metrics/"))

agents = [1, 2, 3, 4, 5, 6]
nations = {1:'Russian', 2:'English', 3:'Chinese',
           4:'German',  5:'French',  6:'American'}

timesteps = metrics_base.timesteps('m1')

STRATEGIES = {
    'Базовая':        metrics_base,
    'Информационная': metrics_info,
    'Эгоистичная':    metrics_ego,
    'Целевая':        metrics_targ,
}
COLORS = {
    'Базовая':        'steelblue',
    'Информационная': 'green',
    'Эгоистичная':    'red',
    'Целевая':        'orange',
}
LINES = {
    'Базовая':        '-',
    'Информационная': '-',
    'Эгоистичная':    '--',
    'Целевая':        '-.',
}

os.makedirs('results/graphs', exist_ok=True)

def avg_metric(metrics, metric_name, timesteps):
    result = []
    for t in timesteps:
        vals = [metrics.get(metric_name, a, t) for a in agents]
        result.append(sum(vals) / len(vals))
    return result

def final_value(metrics, metric_name, agent_id):
    ts = metrics.timesteps(metric_name)
    if not ts:
        return 0.0
    return metrics.get(metric_name, agent_id, ts[-1])

# --- Графики M1, M4, M6, M8, M9 ---
for metric in ['m1', 'm1_raw', 'm2', 'm4', 'm6', 'm8', 'm9']:
    fig, ax = plt.subplots(figsize=(10, 5))
    for name, m in STRATEGIES.items():
        ax.plot(timesteps,
                avg_metric(m, metric, timesteps),
                label=name,
                color=COLORS[name],
                linestyle=LINES[name],
                linewidth=2)
    ax.set_xlabel('Время (дни)')
    ax.set_ylabel(f'Средняя {metric.upper()}')
    titles = {
        'm1': 'M1: полнота знаний при разных стратегиях',
        'm1_raw': 'M1_raw: полнота знаний без FOL-вывода',
        'm2':     'M2: доля неизвестных важных фактов',
        'm4': 'M4: точность предсказания локаций',
        'm6': 'M6: горизонт предсказания (норм.)',
        'm8': 'M8: доля знаний от FOL-вывода',
        'm9': 'M9: выигрыш от FOL относительно наблюдений',
    }
    ax.set_title(titles[metric])
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'results/graphs/graph_{metric}_comparison.png', dpi=150)
    plt.close()
    print(f"График {metric.upper()} сохранён")

# --- Таблица M3 (время достижения порога 0.5) ---
print("\n" + "="*65)
print("M3: время достижения порога M1 = 0.5")
print("="*65)
print(f"{'Агент':<12}", end="")
for name in STRATEGIES:
    print(f"{name:>14}", end="")
print()
print("-"*65)

for a in agents:
    print(f"{nations[a]:<12}", end="")
    for name, m in STRATEGIES.items():
        val = m.m3[a] if hasattr(m, 'm3') else None
        # если нет атрибута m3, используем get
        try:
            val = m.m3[a]
        except:
            val = None
        print(f"{'None' if val is None else str(val):>14}", end="")
    print()

# --- Таблица M5 (устойчивость к потере наблюдений) ---
print("\n" + "="*65)
print("M5: устойчивость к потере наблюдений по drop_rate")
print("="*65)

drop_rates = [0.0, 0.1, 0.2, 0.5]  # типичные значения

print(f"{'drop_rate':<12}", end="")
for name in STRATEGIES:
    print(f"{name:>14}", end="")
print()
print("-"*65)

for dr in drop_rates:
    print(f"{dr:<12}", end="")
    for name, m in STRATEGIES.items():
        try:
            # M5 это словарь по drop_rate, усредняем по агентам
            vals = [m.m5_fol[a][dr] for a in agents]
            avg = sum(vals) / len(vals)
            print(f"{avg:>14.4f}", end="")
        except:
            print(f"{'—':>14}", end="")
    print()

# --- Таблица Nash Equilibrium ---
print("\n" + "="*65)
print("Проверка Nash Equilibrium (M1 в конце симуляции)")
print("="*65)
print(f"{'Агент':<12} {'M1 базовая':>12} {'M1 инф.':>10} "
      f"{'M1 ego':>10} {'M1 цел.':>10} {'NE устойч.?':>12}")
print("-"*65)

for a in agents:
    m1_base = final_value(metrics_base, 'm1', a)
    m1_info = final_value(metrics_info, 'm1', a)
    m1_ego  = final_value(metrics_ego,  'm1', a)
    m1_targ = final_value(metrics_targ, 'm1', a)
    # NE устойчиво если при отклонении (ego) агент не выигрывает
    stable = "Да ✓" if m1_ego <= m1_info else "Нет ⚠"
    print(f"{nations[a]:<12} {m1_base:>12.4f} {m1_info:>10.4f} "
          f"{m1_ego:>10.4f} {m1_targ:>10.4f} {stable:>12}")

print("\nВывод:")
print("NE устойчиво если при эгоистичном отклонении M1 не растёт.")

# --- Таблица по всем метрикам в конце симуляции ---
print("\n" + "="*65)
print("Финальные значения всех метрик (конец симуляции, среднее)")
print("="*65)
print(f"{'Метрика':<10}", end="")
for name in STRATEGIES:
    print(f"{name:>14}", end="")
print()
print("-"*65)

for metric in ['m1', 'm2', 'm4', 'm6', 'm8', 'm9']:
    print(f"{metric.upper():<10}", end="")
    for name, m in STRATEGIES.items():
        ts = m.timesteps(metric)
        if ts:
            vals = [m.get(metric, a, ts[-1]) for a in agents]
            avg = sum(vals) / len(vals)
        else:
            avg = 0.0
        print(f"{avg:>14.4f}", end="")
    print()

print("\nВсе таблицы выведены. Графики в папке results/graphs/")

def check_nash(metric_name, metric_label):
    print("\n" + "="*65)
    print(f"Проверка Nash Equilibrium по метрике {metric_label}")
    print("="*65)
    print(f"{'Агент':<12} {'Базовая':>10} {'Инф.':>10} "
          f"{'Ego':>10} {'Целевая':>10} {'NE (инф.)?':>12}")
    print("-"*65)

    results = []
    for a in agents:
        v_base = final_value(metrics_base, metric_name, a)
        v_info = final_value(metrics_info, metric_name, a)
        v_ego  = final_value(metrics_ego,  metric_name, a)
        v_targ = final_value(metrics_targ, metric_name, a)

        # NE устойчиво если отклонение на ego не улучшает метрику
        stable = "Да ✓" if v_ego <= v_info else "Нет ⚠"
        results.append(stable)
        print(f"{nations[a]:<12} {v_base:>10.4f} {v_info:>10.4f} "
              f"{v_ego:>10.4f} {v_targ:>10.4f} {stable:>12}")

    all_stable = all("Да" in r for r in results)
    print(f"\nВывод: информационная стратегия "
          f"{'ЯВЛЯЕТСЯ' if all_stable else 'НЕ ЯВЛЯЕТСЯ'} "
          f"Nash Equilibrium по метрике {metric_label}")
    return all_stable

# Запускаем для каждой метрики
ne_m1 = check_nash('m1', 'M1 (полнота знаний)')
ne_m4 = check_nash('m4', 'M4 (точность предсказания)')
ne_m6 = check_nash('m6', 'M6 (горизонт предсказания)')
ne_m2 = check_nash('m2', 'M2 (неизвестные факты)')  # тут NE = ego >= info

# Итоговая сводка
print("\n" + "="*65)
print("ИТОГОВАЯ СВОДКА Nash Equilibrium")
print("="*65)
print(f"{'Метрика':<30} {'Инф. стратегия = NE?':>20}")
print("-"*65)
print(f"{'M1 (полнота знаний)':<30} {'Да ✓' if ne_m1 else 'Нет ⚠':>20}")
print(f"{'M2 (неизвестные факты)':<30} {'Да ✓' if ne_m2 else 'Нет ⚠':>20}")
print(f"{'M4 (точность предсказания)':<30} {'Да ✓' if ne_m4 else 'Нет ⚠':>20}")
print(f"{'M6 (горизонт предсказания)':<30} {'Да ✓' if ne_m6 else 'Нет ⚠':>20}")


# --- Overall awareness plot (Hamster tracking case study) ---
timesteps_hamster = metrics_base.timesteps('m1')

fig, ax = plt.subplots(figsize=(10, 5))
for name, m in STRATEGIES.items():
    vals = []
    for t in timesteps_hamster:
        agent_vals = [m.get('m1', a, t) for a in agents]
        vals.append(sum(agent_vals) / len(agent_vals))
    ax.plot(timesteps_hamster, vals,
            label=name, color=COLORS[name],
            linestyle=LINES[name], linewidth=2)

ax.set_xlabel('Time (days)')
ax.set_ylabel('Average M1 across all agents')
ax.set_title('Overall Awareness (Hamster Tracking Case Study) by Strategy')
ax.legend()
ax.set_xlim(left=0)   # ← добавить
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('results/graphs/graph_hamster_overall.png', dpi=150)
plt.close()
print("Overall awareness graph saved")


# --- Who knows the most at end of simulation ---
print("\n" + "=" * 55)
print("Best-informed agent at end of simulation (M1)")
print("=" * 55)
print(f"{'Agent':<12}", end="")
for name in STRATEGIES:
    print(f"{name:>14}", end="")
print()
print("-" * 55)

for a in agents:
    print(f"{nations[a]:<12}", end="")
    for name, m in STRATEGIES.items():
        ts = m.timesteps('m1')
        val = m.get('m1', a, ts[-1])
        print(f"{val:>14.4f}", end="")
    print()
