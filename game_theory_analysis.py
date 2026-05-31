import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
import os
from fol_solver import load_metrics

# Load metrics for four scenarios
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
    'Baseline':        metrics_base,
    'Informational':   metrics_info,
    'Egoistic':        metrics_ego,
    'Targeted':        metrics_targ,
}
COLORS = {
    'Baseline':        'steelblue',
    'Informational':   'green',
    'Egoistic':        'red',
    'Targeted':        'orange',
}
LINES = {
    'Baseline':        '-',
    'Informational':   '-',
    'Egoistic':        '--',
    'Targeted':        '-.',
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

# --- Plots M1, M4, M6, M8, M9 ---
for metric in ['m1', 'm1_raw', 'm2', 'm4', 'm6', 'm8', 'm9']:
    fig, ax = plt.subplots(figsize=(10, 5))
    for name, m in STRATEGIES.items():
        ax.plot(timesteps,
                avg_metric(m, metric, timesteps),
                label=name,
                color=COLORS[name],
                linestyle=LINES[name],
                linewidth=2)
    ax.set_xlabel('Time (days)')
    ax.set_ylabel(f'Average {metric.upper()}')


    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(f'results/graphs/graph_{metric}_comparison.png', dpi=150)
    plt.close()
    print(f"Graph {metric.upper()} saved")

# --- Table M3 (time to reach threshold 0.5) ---
print("\n" + "="*65)
print("M3: Time to reach M1 threshold = 0.5")
print("="*65)
print(f"{'Agent':<12}", end="")
for name in STRATEGIES:
    print(f"{name:>14}", end="")
print()
print("-"*65)

for a in agents:
    print(f"{nations[a]:<12}", end="")
    for name, m in STRATEGIES.items():
        val = m.m3[a] if hasattr(m, 'm3') else None
        try:
            val = m.m3[a]
        except:
            val = None
        print(f"{'None' if val is None else str(val):>14}", end="")
    print()

# --- Table M5 (robustness to observation loss) ---
print("\n" + "="*65)
print("M5: Robustness to Observation Loss by drop_rate")
print("="*65)

drop_rates = [0.0, 0.1, 0.2, 0.5]

print(f"{'drop_rate':<12}", end="")
for name in STRATEGIES:
    print(f"{name:>14}", end="")
print()
print("-"*65)

for dr in drop_rates:
    print(f"{dr:<12}", end="")
    for name, m in STRATEGIES.items():
        try:
            vals = [m.m5_fol[a][dr] for a in agents]
            avg = sum(vals) / len(vals)
            print(f"{avg:>14.4f}", end="")
        except:
            print(f"{'—':>14}", end="")
    print()

# --- Nash Equilibrium table ---
print("\n" + "="*65)
print("Nash Equilibrium Check (M1 at end of simulation)")
print("="*65)
print(f"{'Agent':<12} {'M1 baseline':>12} {'M1 info':>10} "
      f"{'M1 ego':>10} {'M1 targ':>10} {'NE stable?':>12}")
print("-"*65)

for a in agents:
    m1_base = final_value(metrics_base, 'm1', a)
    m1_info = final_value(metrics_info, 'm1', a)
    m1_ego  = final_value(metrics_ego,  'm1', a)
    m1_targ = final_value(metrics_targ, 'm1', a)
    stable = "Yes ✓" if m1_ego <= m1_info else "No ⚠"
    print(f"{nations[a]:<12} {m1_base:>12.4f} {m1_info:>10.4f} "
          f"{m1_ego:>10.4f} {m1_targ:>10.4f} {stable:>12}")

print("\nConclusion:")
print("NE is stable if egoistic deviation does not improve M1.")

# --- Final values table for all metrics ---
print("\n" + "="*65)
print("Final values of all metrics (end of simulation, average)")
print("="*65)
print(f"{'Metric':<10}", end="")
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

print("\nAll tables printed. Graphs saved to results/graphs/")

def check_nash(metric_name, metric_label):
    print("\n" + "="*65)
    print(f"Nash Equilibrium Check for metric {metric_label}")
    print("="*65)
    print(f"{'Agent':<12} {'Baseline':>10} {'Info':>10} "
          f"{'Ego':>10} {'Targeted':>10} {'NE (info)?':>12}")
    print("-"*65)

    results = []
    for a in agents:
        v_base = final_value(metrics_base, metric_name, a)
        v_info = final_value(metrics_info, metric_name, a)
        v_ego  = final_value(metrics_ego,  metric_name, a)
        v_targ = final_value(metrics_targ, metric_name, a)

        stable = "Yes ✓" if v_ego <= v_info else "No ⚠"
        results.append(stable)
        print(f"{nations[a]:<12} {v_base:>10.4f} {v_info:>10.4f} "
              f"{v_ego:>10.4f} {v_targ:>10.4f} {stable:>12}")

    all_stable = all("Yes" in r for r in results)
    print(f"\nConclusion: the informational strategy "
          f"{'IS' if all_stable else 'IS NOT'} "
          f"a Nash Equilibrium for metric {metric_label}")
    return all_stable

# Run for each metric
ne_m1 = check_nash('m1', 'M1 (knowledge completeness)')
ne_m4 = check_nash('m4', 'M4 (prediction accuracy)')
ne_m6 = check_nash('m6', 'M6 (prediction horizon)')
ne_m2 = check_nash('m2', 'M2 (unknown facts)')

# Final summary
print("\n" + "="*65)
print("NASH EQUILIBRIUM SUMMARY")
print("="*65)
print(f"{'Metric':<30} {'Info strategy = NE?':>20}")
print("-"*65)
print(f"{'M1 (knowledge completeness)':<30} {'Yes ✓' if ne_m1 else 'No ⚠':>20}")
print(f"{'M2 (unknown facts)':<30} {'Yes ✓' if ne_m2 else 'No ⚠':>20}")
print(f"{'M4 (prediction accuracy)':<30} {'Yes ✓' if ne_m4 else 'No ⚠':>20}")
print(f"{'M6 (prediction horizon)':<30} {'Yes ✓' if ne_m6 else 'No ⚠':>20}")


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


# ============================================================
# БЛОК: АНАЛИЗ ХОМЯКА ЧЕРЕЗ compute_filtered_metrics
# ============================================================
from fol_solver import compute_filtered_metrics, FactFilter

hamster = FactFilter(attribute='pet', value='Humpster')  # именно Humpster

STRATEGY_PATHS = {
    'Baseline':      'results/baseline',
    'Informational': 'results/informational',
    'Egoistic':      'results/egoistic',
    'Targeted':      'results/targeted',
}

hamster_m1 = {}  # {strategy_name: {agent_id: {t: value}}}

for name, path in STRATEGY_PATHS.items():
    observer_csv = os.path.join(base_dir, path, 'logs/observer.csv')
    logs_dir     = os.path.join(base_dir, path, 'logs/')
    zebra_csv = os.path.join(base_dir, 'data/input_data/zebra-01.csv')

    result = compute_filtered_metrics(
        observer_csv=observer_csv,
        logs_dir=logs_dir,
        zebra_csv=zebra_csv,
        fact_filter=hamster,
        metrics=['m1'],
        max_horizon=100
    )

    # result['m1'] = {agent_id: [(t, value), ...]}
    hamster_m1[name] = {}
    for agent_id, series in result['m1'].items():
        hamster_m1[name][agent_id] = {t: v for t, v in series}

    print(f"{name}: загружено агентов = {len(hamster_m1[name])}")

# --- График M1 по хомяку для каждого агента ---
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flatten()

for idx, a in enumerate(agents):
    ax = axes[idx]
    for name in STRATEGY_PATHS:
        if a not in hamster_m1[name]:
            continue
        data = hamster_m1[name][a]
        ts_sorted = sorted(data.keys())
        vals = [data[t] for t in ts_sorted]
        ax.plot(ts_sorted, vals,
                label=name,
                color=COLORS[name],
                linestyle=LINES[name],
                linewidth=1.5)
    ax.set_title(f'Agent {a}: {nations[a]}')
    ax.set_xlabel('Time')
    ax.set_ylabel('M1 (Humpster)')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)

axes[0].legend(loc='lower right', fontsize=8)
plt.tight_layout()
plt.savefig('results/graphs/graph_humpster_per_agent.png', dpi=150)
plt.close()
print("Humpster per-agent graph saved")

# --- Средняя осведомлённость о хомяке по всем агентам ---
fig, ax = plt.subplots(figsize=(10, 5))

for name in STRATEGY_PATHS:
    # берём общие временные точки
    all_ts = sorted(set(
        t for a in agents
        if a in hamster_m1[name]
        for t in hamster_m1[name][a]
    ))
    avg_vals = []
    for t in all_ts:
        vals = [hamster_m1[name][a][t]
                for a in agents
                if a in hamster_m1[name] and t in hamster_m1[name][a]]
        avg_vals.append(sum(vals) / len(vals) if vals else 0)

    ax.plot(all_ts, avg_vals,
            label=name,
            color=COLORS[name],
            linestyle=LINES[name],
            linewidth=2)

ax.set_xlabel('Time (days)')
ax.set_ylabel('Average M1 (Humpster only)')
ax.legend()
ax.set_xlim(left=0)
ax.set_ylim(bottom=0)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('results/graphs/graph_humpster_overall.png', dpi=150)
plt.close()
print("Humpster overall graph saved")

# --- Таблица финальных значений M1 по хомяку ---
print("\n" + "="*60)
print("Humpster tracking: final M1 per agent")
print("="*60)
print(f"{'Agent':<12}", end="")
for name in STRATEGY_PATHS:
    print(f"{name:>14}", end="")
print()
print("-"*60)

for a in agents:
    print(f"{nations[a]:<12}", end="")
    for name in STRATEGY_PATHS:
        if a in hamster_m1[name]:
            data = hamster_m1[name][a]
            last_t = max(data.keys())
            val = data[last_t]
        else:
            val = 0.0
        print(f"{val:>14.4f}", end="")
    print()