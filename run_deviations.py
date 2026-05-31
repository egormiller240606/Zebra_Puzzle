import os
import subprocess
import shutil

base_dir = os.path.dirname(os.path.abspath(__file__))

agents_list = [1, 2, 3, 4, 5, 6]
strategies  = ['informational', 'egoistic', 'targeted']


original = os.path.join(base_dir, 'data/other_data/uniform_strategies.csv')
backup   = os.path.join(base_dir, 'data/other_data/uniform_strategies_backup.csv')

if not os.path.exists(backup):
    shutil.copy(original, backup)
    print("Backup created")

for agent_id in agents_list:
    for strat_name in strategies:

        strat_file = os.path.join(
            base_dir,
            'data/input_data/deviation_strategies',
            f'deviation_agent{agent_id}_{strat_name}.csv'
        )

        result_dir = os.path.join(
            base_dir,
            f'results/deviation/agent{agent_id}_{strat_name}'
        )
        os.makedirs(os.path.join(result_dir, 'logs'),        exist_ok=True)
        os.makedirs(os.path.join(result_dir, 'fol_metrics'), exist_ok=True)

        print(f"\n{'='*50}")
        print(f"Agent {agent_id} — {strat_name}")
        print(f"{'='*50}")

        shutil.copy(strat_file, original)

        subprocess.run(['python', 'main.py'], check=True)

        shutil.copytree(
            os.path.join(base_dir, 'data/output_data/logs'),
            os.path.join(result_dir, 'logs'),
            dirs_exist_ok=True
        )
        shutil.copytree(
            os.path.join(base_dir, 'data/output_data/fol_metrics'),
            os.path.join(result_dir, 'fol_metrics'),
            dirs_exist_ok=True
        )

        print(f"Saved: {result_dir}")

shutil.copy(backup, original)
