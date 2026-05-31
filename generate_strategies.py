import os

os.makedirs('data/input_data/deviation_strategies', exist_ok=True)

# Базовые параметры Table 2.2
baseline = {
    1: [100, 0,  0,  0,  0,  0,  70, 70],
    2: [30,  10, 10, 25, 25, 0,  50, 50],
    3: [30,  20, 20, 20, 20, 0,  50, 50],
    4: [50,  0,  0,  0,  0,  50, 25, 25],
    5: [10,  10, 0,  10, 20, 50, 90, 40],
    6: [15,  15, 15, 15, 20, 20, 100,100],
}

nations = {
    1: 'Russian',
    2: 'Englishman',
    3: 'Chinese',
    4: 'German',
    5: 'Frenchman',
    6: 'American',
}

def informational(agent_id):
    return [20, 20, 20, 20, 20, 20, 90, 90]

def egoistic(agent_id):
    probs = [0] * 6
    probs[agent_id - 1] = 100
    return probs + [0, 0]

def targeted(agent_id):
    probs = [5, 5, 5, 5, 5, 5]
    probs[5] = 75  # всегда к American (дом 6)
    return probs + [70, 70]

alternatives = {
    'informational': informational,
    'egoistic':      egoistic,
    'targeted':      targeted,
}

for agent_id in range(1, 7):
    for strat_name, strat_func in alternatives.items():
        filename = f'deviation_agent{agent_id}_{strat_name}.csv'
        filepath = os.path.join(
            'data/input_data/deviation_strategies', filename
        )
        with open(filepath, 'w') as f:
            for a in range(1, 7):
                if a == agent_id:
                    params = strat_func(agent_id)
                else:
                    params = baseline[a]
                nation = nations[a]
                line = f"{a};{nation};" + ";".join(map(str, params))
                f.write(line + "\n")
        print(f"Created: {filename}")

print("\nDone — 18 strategy files created")