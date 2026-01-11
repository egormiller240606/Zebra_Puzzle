import os
from typing import Dict, List, Optional, Any, Tuple


# Parse a CSV line by stripping whitespace and splitting by ';'
def parse_csv_line(line: str) -> Optional[List[str]]:
    line = line.strip()
    if not line:
        return None
    return line.split(';')


# Format a log entry for CSV output
def log_formatter(event_number: int, time: int, event_type: str, *extra: Any) -> str:
    extra_str = ";".join(str(v) for v in extra)
    return f"{event_number};{time};{event_type};{extra_str}"


# Load agent strategies from CSV file
def load_strategies(path_to_strategies: str) -> Dict[int, Dict[str, Any]]:
    strategies = {}
    with open(path_to_strategies, encoding='utf-8') as f:
        for line in f:
            parts = parse_csv_line(line)
            if not parts or len(parts) < 2:
                continue

            agent_id = int(parts[0])
            nation = parts[1]

            route_probs_list = [int(x) if x else 0 for x in parts[2:8]]
            route_probs = {i+1: p for i, p in enumerate(route_probs_list)}

            house_exchange_prob = int(parts[8]) if len(parts) > 8 and parts[8] else 0
            pet_exchange_prob = int(parts[9]) if len(parts) > 9 and parts[9] else 0

            strategies[agent_id] = {
                "route_probs": route_probs,
                "house_exchange_prob": house_exchange_prob,
                "pet_exchange_prob": pet_exchange_prob,
                "nation": nation
            }
    return strategies


# Load initial agent and house data from CSV
def load_initial_data(path_to_zebra_01: str, strategies: Optional[Dict[int, Dict[str, Any]]] = None) -> Tuple[Dict[int, 'Agent'], Dict[int, 'House']]:
    from entities.agent import Agent
    from entities.house import House

    agents = {}
    houses = {}

    with open(path_to_zebra_01, encoding='utf-8') as f:
        for line in f:
            parts = parse_csv_line(line)
            if not parts or len(parts) < 1:
                continue

            house_id = int(parts[0])
            color = parts[1] if len(parts) > 1 else ""
            nation = parts[2] if len(parts) > 2 else ""
            drink = parts[3] if len(parts) > 3 else ""
            smoke = parts[4] if len(parts) > 4 else ""
            pet = parts[5] if len(parts) > 5 else ""

            house = House(house_id=house_id, color=color, owner_id=house_id)
            houses[house_id] = house

            if strategies and house_id in strategies:
                strat = strategies[house_id]
                route_probs = strat["route_probs"]
                house_exch = strat["house_exchange_prob"]
                pet_exch = strat["pet_exchange_prob"]
            else:
                route_probs = {}
                house_exch = 0
                pet_exch = 0

            agent = Agent(
                agent_id=house_id,
                nationality=nation,
                drink=drink,
                cigarettes=smoke,
                pet=pet,
                house_id=house_id,
                route_probs=route_probs,
                house_exchange_prob=house_exch,
                pet_exchange_prob=pet_exch
            )
            agents[house_id] = agent

    return agents, houses


# Build mapping of house colors to probability indices
def build_color_to_prob_index(houses: Dict[int, 'House']) -> Dict[str, int]:
    colors = [houses[hid].color for hid in sorted(houses.keys())]
    return {color: idx + 1 for idx, color in enumerate(colors)}


# Load travel matrix from geography CSV
def load_geography(path_to_geography: str) -> List[List[Optional[int]]]:
    rows = []
    with open(path_to_geography, encoding='utf-8') as f:
        for line in f:
            parts = parse_csv_line(line)
            if not parts:
                continue
            rows.append(parts)

    num_houses = len(rows)
    travel_matrix = [[None] * (num_houses + 1) for _ in range(num_houses + 1)]

    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row[2:], start=1):
            if i == j:
                travel_matrix[i][j] = 0
            elif val.strip().upper() == "NA" or val.strip() == "":
                travel_matrix[i][j] = None
            else:
                travel_matrix[i][j] = int(val)

    return travel_matrix

