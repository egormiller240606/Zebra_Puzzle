import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import os
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
from fol_solver import load_metrics

base_dir = os.path.dirname(os.path.abspath(__file__))

agents  = [1, 2, 3, 4, 5, 6]
nations = {1:'Russian', 2:'English', 3:'Chinese',
           4:'German',  5:'French',  6:'American'}

dev_strategies = ['informational', 'egoistic', 'targeted']

COLORS_DEV = {
    'informational': 'green',
    'egoistic':      'red',
    'targeted':      'orange',
}
LINES_DEV = {
    'informational': '-',
    'egoistic':      '--',
    'targeted':      '-.',
}

# загружаем baseline
metrics_base = load_metrics(
    os.path.join(base_dir, 'results/baseline/fol_metrics/')
)

# загружаем все 18 прогонов
deviation_metrics = {}
for agent_id in agents:
    deviation_metrics[agent_id] = {}
    for strat in dev_strategies:
        path = os.path.join(
            base_dir,
            f'results/deviation/agent{agent_id}_{strat}/fol_metrics/'
        )
        deviation_metrics[agent_id][strat] = load_metrics(path)

os.makedirs('results/graphs/deviation', exist_ok=True)

def final_value(metrics, metric_name, agent_id):
    ts = metrics.timesteps(metric_name)
    if not ts:
        return 0.0
    return metrics.get(metric_name, agent_id, ts[-1])

# ============================================================
# БЛОК 1: ГРАФИКИ M1 ПО КАЖДОМУ АГЕНТУ
# ============================================================

timesteps = metrics_base.timesteps('m1')

for a in agents:
    fig, ax = plt.subplots(figsize=(10, 5))

    # baseline — чёрная линия
    baseline_vals = [metrics_base.get('m1', a, t) for t in timesteps]
    ax.plot(timesteps, baseline_vals,
            label='Baseline (all agents)',
            color='black',
            linewidth=2,
            linestyle='-')

    # три варианта отклонения
    for strat in dev_strategies:
        m = deviation_metrics[a][strat]
        vals = [m.get('m1', a, t) for t in timesteps]
        vals_smooth = pd.Series(vals).rolling(
            window=30, min_periods=1
        ).mean().tolist()
        ax.plot(timesteps, vals_smooth,
                label=f'{nations[a]} deviates → {strat}',
                color=COLORS_DEV[strat],
                linestyle=LINES_DEV[strat],
                linewidth=2)

    ax.set_xlabel('Time (days)')
    ax.set_ylabel('M1 — Knowledge Completeness')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    plt.savefig(
        f'results/graphs/deviation/graph_deviation_agent{a}_{nations[a]}.png',
        dpi=150
    )
    plt.close()
    print(f"Deviation graph saved: Agent {a} {nations[a]}")

# ============================================================
# БЛОК 2: СВОДНАЯ ТАБЛИЦА UNILATERAL DEVIATION
# ============================================================

print("\n" + "="*75)
print("Unilateral Deviation Analysis — Final M1 values")
print("="*75)
print(f"{'Agent':<12} {'Baseline':>10} {'→ Info':>10} "
      f"{'→ Ego':>10} {'→ Target':>10} "
      f"{'Best deviation':>16} {'NE stable?':>12}")
print("-"*75)

ne_results = {}

for a in agents:
    v_base = final_value(metrics_base, 'm1', a)
    v_info = final_value(deviation_metrics[a]['informational'], 'm1', a)
    v_ego  = final_value(deviation_metrics[a]['egoistic'],      'm1', a)
    v_targ = final_value(deviation_metrics[a]['targeted'],      'm1', a)

    best_val  = max(v_info, v_ego, v_targ)
    best_name = max(
        [('Info', v_info), ('Ego', v_ego), ('Target', v_targ)],
        key=lambda x: x[1]
    )[0]

    # NE стабильно если ни одно отклонение не улучшает M1
    stable = "Yes ✓" if best_val <= v_base else "No ⚠"
    ne_results[a] = stable

    print(f"{nations[a]:<12} {v_base:>10.4f} {v_info:>10.4f} "
          f"{v_ego:>10.4f} {v_targ:>10.4f} "
          f"{best_name:>16} {stable:>12}")

print("\n" + "="*75)
print("CONCLUSION")
print("="*75)
all_stable = all("Yes" in v for v in ne_results.values())
print(f"Baseline strategy IS{' ' if all_stable else ' NOT '}"
      f"a Nash Equilibrium under M1")
print(f"(unilateral deviation {'does not improve' if all_stable else 'improves'} "
      f"M1 for {'all' if all_stable else 'some'} agents)")

# ============================================================
# БЛОК 3: СВОДНЫЙ ГРАФИК — ВСЕ АГЕНТЫ, ФИНАЛЬНЫЕ ЗНАЧЕНИЯ
# ============================================================

fig, ax = plt.subplots(figsize=(12, 6))

x = range(len(agents))
width = 0.2

baseline_finals = [final_value(metrics_base, 'm1', a) for a in agents]
info_finals    = [final_value(deviation_metrics[a]['informational'], 'm1', a)
                  for a in agents]
ego_finals     = [final_value(deviation_metrics[a]['egoistic'], 'm1', a)
                  for a in agents]
targ_finals    = [final_value(deviation_metrics[a]['targeted'], 'm1', a)
                  for a in agents]

ax.bar([i - 1.5*width for i in x], baseline_finals,
       width, label='Baseline', color='steelblue', alpha=0.85)
ax.bar([i - 0.5*width for i in x], info_finals,
       width, label='→ Informational', color='green', alpha=0.85)
ax.bar([i + 0.5*width for i in x], ego_finals,
       width, label='→ Egoistic', color='red', alpha=0.85)
ax.bar([i + 1.5*width for i in x], targ_finals,
       width, label='→ Targeted', color='orange', alpha=0.85)

ax.set_xlabel('Agent')
ax.set_ylabel('Final M1 (knowledge completeness)')
ax.set_xticks(list(x))
ax.set_xticklabels([nations[a] for a in agents])
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3, axis='y')
ax.set_ylim(0, 0.85)
plt.tight_layout()
plt.savefig('results/graphs/deviation/graph_deviation_summary.png', dpi=150)
plt.close()
print("\nSummary deviation graph saved")

print("\nAll deviation analysis complete.")

# ============================================================
# БЛОК 4: UNILATERAL DEVIATION ПО M6
# ============================================================

print("\n" + "="*75)
print("Unilateral Deviation Analysis — Final M6 values")
print("="*75)
print(f"{'Agent':<12} {'Baseline':>10} {'→ Info':>10} "
      f"{'→ Ego':>10} {'→ Target':>10} {'NE stable?':>12}")
print("-"*75)

ne_m6_results = {}

for a in agents:
    v_base = final_value(metrics_base, 'm6', a)
    v_info = final_value(deviation_metrics[a]['informational'], 'm6', a)
    v_ego  = final_value(deviation_metrics[a]['egoistic'],      'm6', a)
    v_targ = final_value(deviation_metrics[a]['targeted'],      'm6', a)

    best_val = max(v_info, v_ego, v_targ)
    stable = "Yes ✓" if best_val <= v_base else "No ⚠"
    ne_m6_results[a] = stable

    print(f"{nations[a]:<12} {v_base:>10.4f} {v_info:>10.4f} "
          f"{v_ego:>10.4f} {v_targ:>10.4f} {stable:>12}")

all_stable_m6 = all("Yes" in v for v in ne_m6_results.values())
print(f"\nConclusion: Baseline strategy IS"
      f"{' ' if all_stable_m6 else ' NOT '}"
      f"a Nash Equilibrium under M6")


# ============================================================
# БАРЧАРТ DEVIATION ПО M6
# ============================================================

fig, ax = plt.subplots(figsize=(12, 6))

width = 0.2
x = range(len(agents))

baseline_m6 = [final_value(metrics_base, 'm6', a) for a in agents]
info_m6     = [final_value(deviation_metrics[a]['informational'], 'm6', a)
               for a in agents]
ego_m6      = [final_value(deviation_metrics[a]['egoistic'], 'm6', a)
               for a in agents]
targ_m6     = [final_value(deviation_metrics[a]['targeted'], 'm6', a)
               for a in agents]

ax.bar([i - 1.5*width for i in x], baseline_m6,
       width, label='Baseline', color='steelblue', alpha=0.85)
ax.bar([i - 0.5*width for i in x], info_m6,
       width, label='→ Informational', color='green', alpha=0.85)
ax.bar([i + 0.5*width for i in x], ego_m6,
       width, label='→ Egoistic', color='red', alpha=0.85)
ax.bar([i + 1.5*width for i in x], targ_m6,
       width, label='→ Targeted', color='orange', alpha=0.85)

ax.set_xlabel('Agent')
ax.set_ylabel('Final M6 (prediction horizon)')
ax.set_xticks(list(x))
ax.set_xticklabels([nations[a] for a in agents])
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3, axis='y')
ax.set_ylim(0.6, 1.0)
plt.tight_layout()
plt.savefig('results/graphs/deviation/graph_deviation_summary_m6.png', dpi=150)
plt.close()
print("M6 deviation summary graph saved")