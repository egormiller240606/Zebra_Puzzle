import random
import heapq
from typing import Dict, List, Optional, Any, Tuple

# Constants for event priorities in simulation
EVENT_PRIORITY_FINISH_TRIP = 1
EVENT_PRIORITY_EXCHANGE = 2
EVENT_PRIORITY_START_TRIP = 3

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

# Agent class representing a simulation entity
class Agent:
    def __init__(self, agent_id: int, nationality: str, drink: str, cigarettes: str, pet: str,
                  house_id: int, route_probs: Dict[int, int], house_exchange_prob: int, pet_exchange_prob: int):
        self.id = agent_id
        self.nationality = nationality
        self.drink = drink
        self.cigarettes = cigarettes
        self.pet = pet

        self.house_id = house_id
        self.location = house_id
        self.is_travelling = False

        self.route_probs = route_probs
        self.house_exchange_prob = house_exchange_prob
        self.pet_exchange_prob = pet_exchange_prob
        self.last_update_time = 0

        self.knowledge = {
            self.id: {
                # "nationality": self.nationality,
                # "drink": self.drink,
                # "cigarettes": self.cigarettes,
                "pet": self.pet,
                "house": self.house_id,
                "location": self.location,
                "t": 0
            }
        }
    
    def _get_agent_info(self) -> Dict[str, Any]:
        return {
            # "nationality": self.nationality,
            # "drink": self.drink,
            # "cigarettes": self.cigarettes,
            "pet": self.pet,
            "house": self.house_id,
            "location": self.location
        }
    
    def update_knowledge(self, other_agent: 'Agent', time: int) -> None:
        self.knowledge[other_agent.id] = {**other_agent._get_agent_info(), "t": time}

    def choose_trip_target(self, travel_matrix: List[List[Optional[int]]], houses: Dict[int, 'House'], color_to_prob_index: Dict[str, int]) -> Optional[int]:
        possible_targets = [
            h for h in range(1, len(travel_matrix))
            if travel_matrix[self.location][h] is not None and h != self.location
        ]

        if not possible_targets:
            return None

        weights = []
        for h in possible_targets:
            house_color = houses[h].color
            prob_index = color_to_prob_index.get(house_color, 0)
            weight = self.route_probs.get(prob_index, 0)
            weights.append(weight)

        if sum(weights) == 0:
            return random.choice(possible_targets)

        total = sum(weights)
        rnd = random.uniform(0, total)
        cumulative = 0
        for h, w in zip(possible_targets, weights):
            cumulative += w
            if rnd <= cumulative:
                return h

    def __repr__(self) -> str:
        loc = self.location if self.location == self.house_id else f"travel→{self.location}"
        return (f"Agent(id={self.id}, nat={self.nationality}, "
                f"drink={self.drink}, cig={self.cigarettes}, pet={self.pet}, "
                f"home={self.house_id}, loc={loc})")

# House class representing a location
class House:
    def __init__(self, house_id: int, color: str, owner_id: int):
        self.id = house_id
        self.color = color
        self.owner_id = owner_id
        self.present_agents = set()

    def enter(self, agent_id: int) -> None:
        self.present_agents.add(agent_id)

    def leave(self, agent_id: int) -> None:
        self.present_agents.discard(agent_id)

    def set_owner(self, new_owner_id: int) -> None:
        self.owner_id = new_owner_id

    def is_owner_home(self) -> bool:
        return self.owner_id in self.present_agents

    def __repr__(self) -> str:
        return (f"House(id={self.id}, color={self.color}, "
                f"owner={self.owner_id}, present={list(self.present_agents)})")

# Base Event class for simulation events
class Event:
    def __init__(self, time: int, agent_id: Optional[int] = None):
        self.time = time
        self.agent_id = agent_id

    def run(self, env: 'Environment') -> Tuple[List[int], List[int]]:
        return ([self.agent_id] if self.agent_id is not None else [], [])

    def is_invalid(self) -> bool:
        return False

    def __lt__(self, other: 'Event') -> bool:
        return self.time < other.time

# Event for exchanging houses
class ChangeHouseEvent(Event):
    def __init__(self, time: int, participant_ids: List[int], houses_after_exchange: List[int]):
        super().__init__(time)
        self.participant_ids = participant_ids
        self.houses_after_exchange = houses_after_exchange
        self.qty_participants = len(participant_ids)
        if self.qty_participants < 2:
            raise ValueError("Exchange requires at least 2 participants")

    def run(self, env: 'Environment') -> Tuple[List[int], List[int]]:
        first_participant = env.agents[self.participant_ids[0]]
        house_id = first_participant.location
        house = env.houses[house_id]

        # Update agent house_ids and house owners
        for agent_id, new_house_id in zip(self.participant_ids, self.houses_after_exchange):
            agent = env.agents[agent_id]
            agent.house_id = new_house_id
            agent.knowledge[agent_id] = {**agent._get_agent_info(), "t": self.time}
            agent.last_update_time = self.time

        # Update house owners
        for new_house_id, new_owner_id in zip(self.houses_after_exchange, self.participant_ids):
            env.houses[new_house_id].set_owner(new_owner_id)

        # Update knowledge of all present agents (witnesses)
        all_present = list(house.present_agents)
        for witness_id in all_present:
            witness = env.agents[witness_id]
            for participant_id in self.participant_ids:
                witness.update_knowledge(env.agents[participant_id], self.time)

        return self.participant_ids, []

    def get_log_data(self, env: 'Environment') -> Tuple[str, List[Any]]:
        nationalities = [env.agents[agent_id].nationality for agent_id in self.participant_ids]
        extra = [self.qty_participants] + nationalities + list(map(str, self.houses_after_exchange))
        return "changeHouse", extra

# Event for finishing a trip
class FinishTripEvent(Event):
    def __init__(self, time: int, agent_id: int, target_house: int):
        super().__init__(time, agent_id)
        self.target_house = target_house
        self.success = 0

    def run(self, env: 'Environment') -> Tuple[List[int], List[int]]:
        agent = env.agents[self.agent_id]

        agent.is_travelling = False
        agent.location = self.target_house
        house = env.houses[self.target_house]
        house.enter(agent.id)

        self.success = 1 if house.is_owner_home() else 0

        if self.success == 1:
            for other_id in list(house.present_agents):
                if other_id != agent.id:
                    other_agent = env.agents[other_id]
                    agent.update_knowledge(other_agent, self.time)
                    other_agent.update_knowledge(agent, self.time)

            # Detect and execute house exchange
            house_exchange_event = self.detect_house_exchange(env, house)
            if house_exchange_event:
                house_exchange_event.run(env)
                env.house_exchange_events.append(house_exchange_event)

        return [agent.id], [self.target_house]

    def detect_house_exchange(self, env: 'Environment', house: 'House') -> Optional[ChangeHouseEvent]:
        present_agents = sorted(list(house.present_agents))
        if len(present_agents) < 2:
            return None

        ready_participants = []
        for agent_id in present_agents:
            agent = env.agents[agent_id]
            if random.randint(1, 100) <= agent.house_exchange_prob:
                ready_participants.append(agent_id)

        if len(ready_participants) < 2:
            return None

        participants = sorted(ready_participants)
        current_houses = [env.agents[pid].house_id for pid in participants]
        houses_after_exchange = current_houses[1:] + [current_houses[0]]

        return ChangeHouseEvent(time=self.time, participant_ids=participants, houses_after_exchange=houses_after_exchange)

    def get_log_data(self, env: 'Environment') -> Tuple[str, List[Any]]:
        agent = env.agents[self.agent_id]
        if self.target_house == agent.house_id:
            return "FinishTrip", [agent.nationality, self.target_house]
        else:
            return "FinishTrip", [self.success, agent.nationality, self.target_house]

# Event for starting a trip
class StartTripEvent(Event):
    def __init__(self, time: int, agent_id: int, target_house: int):
        super().__init__(time, agent_id)
        self.target_house = target_house

    def run(self, env: 'Environment') -> Tuple[List[int], List[int]]:
        agent = env.agents[self.agent_id]
        if agent.is_travelling:
            return [], []

        if not agent.is_travelling and agent.location in env.houses:
            env.houses[agent.location].leave(agent.id)

        agent.is_travelling = True

        travel_time = env.travel_matrix[agent.location][self.target_house]
        if travel_time is None or travel_time < 0:  # Changed from <= 0 to < 0
            agent.is_travelling = False
            return [], []

        arrival_time = self.time + travel_time
        if arrival_time > env.max_time:
            agent.is_travelling = False
            return [], []

        finish_event = FinishTripEvent(arrival_time, agent.id, self.target_house)
        env.push_event(finish_event)

        return [agent.id], []

    def get_log_data(self, env: 'Environment') -> Tuple[str, List[Any]]:
        agent = env.agents[self.agent_id]
        return "StartTrip", [agent.nationality, agent.location, self.target_house]

# Event for exchanging pets
class ChangePetEvent(Event):
    def __init__(self, time: int, participant_ids: List[int], pets_after_exchange: List[str]):
        super().__init__(time)
        self.participant_ids = participant_ids
        self.pets_after_exchange = pets_after_exchange
        self.qty_participants = len(participant_ids)
        if self.qty_participants < 2:
            raise ValueError("Exchange requires at least 2 participants")

    def run(self, env: 'Environment') -> Tuple[List[int], List[int]]:
        first_participant = env.agents[self.participant_ids[0]]
        house_id = first_participant.location
        house = env.houses[house_id]

        for agent_id, new_pet in zip(self.participant_ids, self.pets_after_exchange):
            agent = env.agents[agent_id]
            agent.pet = new_pet
            agent.knowledge[agent_id] = {**agent._get_agent_info(), "t": self.time}
            agent.last_update_time = self.time

        all_present = list(house.present_agents)
        for witness_id in all_present:
            witness = env.agents[witness_id]
            for participant_id in self.participant_ids:
                witness.update_knowledge(env.agents[participant_id], self.time)

        return self.participant_ids, []

    def get_log_data(self, env: 'Environment') -> Tuple[str, List[Any]]:
        nationalities = [env.agents[agent_id].nationality for agent_id in self.participant_ids]
        extra = [self.qty_participants] + nationalities + self.pets_after_exchange
        return "ChangePet", extra

# Environment class managing the simulation
class Environment:
    def __init__(self, agents: Dict[int, Agent], houses: Dict[int, House], travel_matrix: List[List[Optional[int]]], max_time: int):
        self.agents = agents
        self.houses = houses
        self.travel_matrix = travel_matrix
        self.max_time = max_time
        self.time = 0
        self.event_queue: List[Event] = []
        self.house_exchange_events: List[ChangeHouseEvent] = []

        self.color_to_prob_index = build_color_to_prob_index(houses)

        for house_id, house in houses.items():
            owner = house.owner_id
            house.enter(owner)

        for agent_id, agent in self.agents.items():
            target = agent.choose_trip_target(self.travel_matrix, self.houses, self.color_to_prob_index)
            if target is not None:
                start_event = StartTripEvent(time=0, agent_id=agent_id, target_house=target)
                self.push_event(start_event)

    def push_event(self, event: Event) -> None:
        heapq.heappush(self.event_queue, event)

    def detect_and_generate_exchanges(self) -> List[ChangePetEvent]:
        exchange_events = []

        for house_id, house in self.houses.items():
            present_agents = sorted(list(house.present_agents))
            if len(present_agents) < 2:
                continue

            ready_participants = []
            for agent_id in present_agents:
                agent = self.agents[agent_id]
                if random.randint(1, 100) <= agent.pet_exchange_prob:
                    ready_participants.append(agent_id)

            if len(ready_participants) >= 2:
                ready_participants_sorted = sorted(ready_participants)

                # Use all ready participants instead of limiting to 3
                participants = ready_participants_sorted
                current_pets = [self.agents[agent_id].pet for agent_id in participants]

                # Rotate pets: each gets the next one's pet
                pets_after_exchange = current_pets[1:] + [current_pets[0]]

                exchange_events.append(ChangePetEvent(
                    time=self.time,
                    participant_ids=participants,
                    pets_after_exchange=pets_after_exchange
                ))

        return exchange_events

    def _process_batch_events(self, batch: List[Event]) -> Tuple[List[FinishTripEvent], List[StartTripEvent], List[Event], List[ChangePetEvent]]:
        def event_priority(e: Event) -> int:
            if isinstance(e, FinishTripEvent):
                return EVENT_PRIORITY_FINISH_TRIP
            elif hasattr(e, 'participant_ids'):
                return EVENT_PRIORITY_EXCHANGE
            else:
                return EVENT_PRIORITY_START_TRIP

        batch.sort(key=event_priority)

        finish_events = [e for e in batch if isinstance(e, FinishTripEvent)]
        start_events = [e for e in batch if isinstance(e, StartTripEvent)]
        other_events = [e for e in batch if not isinstance(e, (FinishTripEvent, StartTripEvent))]

        for event in finish_events:
            event.run(self)

        exchange_events = []
        if finish_events:
            exchange_events = self.detect_and_generate_exchanges()
            for event in exchange_events:
                event.run(self)

        for event in start_events:
            event.run(self)

        for event in other_events:
            event.run(self)

        return finish_events, start_events, other_events, exchange_events

    def _log_events(self, finish_events: List[FinishTripEvent], exchange_events: List[ChangePetEvent], house_exchange_events: List[ChangeHouseEvent], start_events: List[StartTripEvent], event_counter: int, csv_log: List[str]) -> int:
        all_events = finish_events + exchange_events + house_exchange_events + start_events
        for event in all_events:
            event_type, extra = event.get_log_data(self)
            csv_log.append(log_formatter(event_counter, event.time, event_type, *extra))
            event_counter += 1
        return event_counter

    def _plan_new_trips(self, finish_events: List[FinishTripEvent]) -> None:
        for event in finish_events:
            agent = self.agents[event.agent_id]
            if agent.is_travelling:
                continue  # Skip if already planning a trip (e.g., after house exchange)
            if agent.location == agent.house_id:
                new_target = agent.choose_trip_target(self.travel_matrix, self.houses, self.color_to_prob_index)
                if new_target is not None:
                    travel_time = self.travel_matrix[agent.location][new_target]
                    if travel_time is not None and travel_time >= 0:  # Allow zero travel time
                        start_time = self.time  # Schedule at current time for instant processing
                        start_event = StartTripEvent(time=start_time, agent_id=agent.id, target_house=new_target)
                        self.push_event(start_event)
            else:
                home = agent.house_id
                travel_time = self.travel_matrix[agent.location][home]
                if travel_time is not None and travel_time >= 0:
                    start_time = self.time
                    start_event = StartTripEvent(time=start_time, agent_id=agent.id, target_house=home)
                    self.push_event(start_event)

    def run(self, max_time: int) -> List[str]:
        event_counter = 1
        csv_log = []

        while self.event_queue and self.time <= max_time:
            t = self.event_queue[0].time
            self.time = t

            # Process all events at current t, including newly added ones
            while self.event_queue and self.event_queue[0].time == self.time:
                batch = []
                while self.event_queue and self.event_queue[0].time == self.time:
                    batch.append(heapq.heappop(self.event_queue))

                if not batch:
                    break

                # Sort batch by priority and process
                batch.sort(key=lambda e: (EVENT_PRIORITY_FINISH_TRIP if isinstance(e, FinishTripEvent) else
                                            EVENT_PRIORITY_EXCHANGE if hasattr(e, 'participant_ids') else
                                            EVENT_PRIORITY_START_TRIP))

                finish_events, start_events, other_events, exchange_events = self._process_batch_events(batch)
                event_counter = self._log_events(finish_events, exchange_events, self.house_exchange_events, start_events, event_counter, csv_log)
                self.house_exchange_events.clear()

                # Plan new trips after processing (may add events at current t)
                self._plan_new_trips(finish_events)

        return csv_log

if __name__ == "__main__":
    strategies = load_strategies("data/input_data/ZEBRA-strategies.csv")
    agents, houses = load_initial_data("data/input_data/zebra-01.csv", strategies=strategies)
    T = load_geography("data/input_data/ZEBRA-geo.csv")

    max_time = 2000
    env = Environment(agents, houses, T, max_time)
    log = env.run(max_time)

    with open("data/output_data/logs/observer.csv", "w", encoding="utf-8") as f:
        for entry in log:
            f.write(entry + "\n")
        f.write("---- KNOWLEDGE ----\n")
        for a in env.agents.values():
            f.write(f"{a.id};{a.knowledge}\n")