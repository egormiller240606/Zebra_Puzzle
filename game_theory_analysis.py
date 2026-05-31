import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
import os
from fol_solver import load_metrics, compute_filtered_metrics, FactFilter

base_dir = os.path.dirname(os.path.abspath(__file__))
metrics_base = load_metrics(os.path.join(base_dir, "results/baseline/fol_metrics/"))
metrics_info = load_metrics(os.path.join(base_dir, "results/informational/fol_metrics/"))
metrics_ego  = load_metrics(os.path.join(base_dir, "results/egoistic/fol_metrics/"))
metrics_targ = load_metrics(os.path.join(base_dir, "results/targeted/fol_metrics/"))

agents  = [1, 2, 3, 4, 5, 6]
nations = {1:'Russian', 2:'English', 3:'Chinese',
           4:'German',  5:'French',  6:'American'}

timesteps = metrics_base.timesteps('m1')

STRATEGIES = {
    'Baseline':      metrics_base,
    'Informational': metrics_info,
    'Egoistic':      metrics_ego,
    'Targeted':      metrics_targ,
}
COLORS = {
    'Baseline':      'steelblue',
    'Informational': 'green',
    'Egoistic':      'red',
    'Targeted':      'orange',
}
LINES = {
    'Baseline':      '-',
    'Informational': '-',
    'Egoistic':      '--',
    'Targeted':      '-.',
}

os.makedirs('results/graphs', exist_ok=True)

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

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

def check_nash(metric_name, metric_label):
    print("\n" + "="*65)
    print(f"Nash Equilibrium Check: {metric_label}")
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
    print(f"\nConclusion: informational strategy "
          f"{'IS' if all_stable else 'IS NOT'} "
          f"a Nash Equilibrium for {metric_label}")
    return all_stable

# ============================================================
# БЛОК 1: ГРАФИКИ МЕТРИК
# ============================================================

titles = {
    'm1':     'M1: Knowledge Completeness across Strategies',
    'm1_raw': 'M1_raw: Knowledge Completeness without FOL Inference',
    'm2':     'M2: Fraction of Unknown Important Facts',
    'm4':     'M4: Location Prediction Accuracy',
    'm6':     'M6: Prediction Horizon (normalised)',
    'm8':     'M8: Fraction of Knowledge from FOL Inference',
    'm9':     'M9: FOL Gain over Raw Observations',
}

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
    ax.set_title(titles[metric])
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(f'results/graphs/graph_{metric}_comparison.png', dpi=150)
    plt.close()
    print(f"Graph {metric.upper()} saved")

# ============================================================
# БЛОК 2: ТАБЛИЦА M3
# ============================================================

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
        try:
            val = m.m3[a]
        except:
            val = None
        print(f"{'None' if val is None else str(val):>14}", end="")
    print()

# ============================================================
# БЛОК 3: ТАБЛИЦА M5
# ============================================================

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
            avg  = sum(vals) / len(vals)
            print(f"{avg:>14.4f}", end="")
        except:
            print(f"{'—':>14}", end="")
    print()

# ============================================================
# БЛОК 4: ФИНАЛЬНЫЕ ЗНАЧЕНИЯ ВСЕХ МЕТРИК
# ============================================================

print("\n" + "="*65)
print("Final values of all metrics (end of simulation, average)")
print("="*65)
print(f"{'Metric':<10}", end="")
for name in STRATEGIES:
    print(f"{name:>14}", end="")
print()
print("-"*65)

for metric in ['m1', 'm1_raw', 'm2', 'm4', 'm6', 'm8', 'm9']:
    print(f"{metric.upper():<10}", end="")
    for name, m in STRATEGIES.items():
        ts = m.timesteps(metric)
        if ts:
            vals = [m.get(metric, a, ts[-1]) for a in agents]
            avg  = sum(vals) / len(vals)
        else:
            avg = 0.0
        print(f"{avg:>14.4f}", end="")
    print()

# ============================================================
# БЛОК 5: NASH EQUILIBRIUM ПО ВСЕМ МЕТРИКАМ
# ============================================================

ne_m1 = check_nash('m1', 'M1 (knowledge completeness)')
ne_m4 = check_nash('m4', 'M4 (prediction accuracy)')
ne_m6 = check_nash('m6', 'M6 (prediction horizon)')
ne_m2 = check_nash('m2', 'M2 (unknown facts)')

print("\n" + "="*65)
print("NASH EQUILIBRIUM SUMMARY")
print("="*65)
print(f"{'Metric':<30} {'Info strategy = NE?':>20}")
print("-"*65)
print(f"{'M1 (knowledge completeness)':<30} {'Yes ✓' if ne_m1 else 'No ⚠':>20}")
print(f"{'M2 (unknown facts)':<30}       {'Yes ✓' if ne_m2 else 'No ⚠':>20}")
print(f"{'M4 (prediction accuracy)':<30}  {'Yes ✓' if ne_m4 else 'No ⚠':>20}")
print(f"{'M6 (prediction horizon)':<30}   {'Yes ✓' if ne_m6 else 'No ⚠':>20}")

# ============================================================
# БЛОК 6: ЛУЧШИЙ АГЕНТ В КОНЦЕ СИМУЛЯЦИИ
# ============================================================

print("\n" + "="*55)
print("Best-informed agent at end of simulation (M1)")
print("="*55)
print(f"{'Agent':<12}", end="")
for name in STRATEGIES:
    print(f"{name:>14}", end="")
print()
print("-"*55)

for a in agents:
    print(f"{nations[a]:<12}", end="")
    for name, m in STRATEGIES.items():
        ts  = m.timesteps('m1')
        val = m.get('m1', a, ts[-1])
        print(f"{val:>14.4f}", end="")
    print()

# ============================================================
# БЛОК 7: АНАЛИЗ ХОМЯКА
# ============================================================

hamster = FactFilter(attribute='pet', value='Humpster')

STRATEGY_PATHS = {
    'Baseline':      'results/baseline',
    'Informational': 'results/informational',
    'Egoistic':      'results/egoistic',
    'Targeted':      'results/targeted',
}

hamster_m1 = {}

for name, path in STRATEGY_PATHS.items():
    observer_csv = os.path.join(base_dir, path, 'logs/observer.csv')
    logs_dir     = os.path.join(base_dir, path, 'logs/')
    zebra_csv    = os.path.join(base_dir, 'data/input_data/zebra-01.csv')
    result = compute_filtered_metrics(
        observer_csv=observer_csv,
        logs_dir=logs_dir,
        zebra_csv=zebra_csv,
        fact_filter=hamster,
        metrics=['m1'],
        max_horizon=100
    )
    hamster_m1[name] = {}
    for agent_id, series in result['m1'].items():
        hamster_m1[name][agent_id] = {t: v for t, v in series}
    print(f"{name}: loaded agents = {len(hamster_m1[name])}")

# --- Per-agent график со сглаживанием ---
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flatten()

for idx, a in enumerate(agents):
    ax = axes[idx]
    for name in STRATEGY_PATHS:
        if a not in hamster_m1[name]:
            continue
        data      = hamster_m1[name][a]
        ts_sorted = sorted(data.keys())
        vals      = [data[t] for t in ts_sorted]
        vals_smooth = pd.Series(vals).rolling(
            window=50, min_periods=1
        ).mean().tolist()
        ax.plot(ts_sorted, vals_smooth,
                label=name,
                color=COLORS[name],
                linestyle=LINES[name],
                linewidth=1.5)
    ax.set_title(f'Agent {a}: {nations[a]}')
    ax.set_xlabel('Time (days)')
    ax.set_ylabel('M1 — Hamster (rolling mean, w=50)')
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)

axes[0].legend(loc='lower right', fontsize=8)
plt.suptitle('Per-Agent Situational Awareness of Hamster Location', fontsize=13)
plt.tight_layout()
plt.savefig('results/graphs/graph_hamster_per_agent.png', dpi=150)
plt.close()
print("Hamster per-agent graph saved")

# --- Общий сглаженный график ---
timesteps_hamster = metrics_base.timesteps('m1')

fig, ax = plt.subplots(figsize=(10, 5))
for name, m in STRATEGIES.items():
    vals = []
    for t in timesteps_hamster:
        agent_vals = [m.get('m1', a, t) for a in agents]
        vals.append(sum(agent_vals) / len(agent_vals))
    vals_smooth = pd.Series(vals).rolling(
        window=50, min_periods=1
    ).mean().tolist()
    ax.plot(timesteps_hamster, vals_smooth,
            label=name,
            color=COLORS[name],
            linestyle=LINES[name],
            linewidth=2)

ax.set_xlabel('Time (days)')
ax.set_ylabel('Average M1 — Hamster tracking (rolling mean, w=50)')
ax.set_title('Situational Awareness of Hamster Location Across Strategies')
ax.set_xlim(left=0)
ax.set_ylim(0, 1)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('results/graphs/graph_hamster_smooth.png', dpi=150)
plt.close()
print("Hamster smooth graph saved")

# --- Таблица финальных M1 по хомяку ---
print("\n" + "="*60)
print("Hamster tracking: final M1 per agent")
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
            data  = hamster_m1[name][a]
            val   = data[max(data.keys())]
        else:
            val = 0.0
        print(f"{val:>14.4f}", end="")
    print()

print("\nAll done. Graphs saved to results/graphs/")

