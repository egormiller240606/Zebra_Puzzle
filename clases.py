import random
import heapq

# Constants for event priorities in simulation
EVENT_PRIORITY_FINISH_TRIP = 1
EVENT_PRIORITY_EXCHANGE = 2
EVENT_PRIORITY_START_TRIP = 3

# Parse a CSV line by stripping whitespace and splitting by ';'
def parse_csv_line(line):
    line = line.strip()
    if not line:
        return None
    return line.split(';')

# Format a log entry for CSV output
def log_formatter(event_number, time, event_type, **kwargs):
    extra = ";".join(str(v) for v in kwargs.values())
    return f"{event_number};{time};{event_type};{extra}"

# Load agent strategies from CSV file
def load_strategies(path_to_strategies):
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
def load_initial_data(path_to_zebra_01, strategies=None):
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
def build_color_to_prob_index(houses):
    colors = sorted(set(house.color for house in houses.values() if house.color))
    return {color: idx + 1 for idx, color in enumerate(colors)}

# Load travel matrix from geography CSV
def load_geography(path_to_geography):
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
    def __init__(self, agent_id, nationality, drink, cigarettes, pet,
                  house_id, route_probs, house_exchange_prob, pet_exchange_prob):
        self.id = agent_id
        self.nationality = nationality
        self.drink = drink
        self.cigarettes = cigarettes
        self.pet = pet

        self.house_id = house_id
        self.location = house_id
        self.is_travelling = False
        self.travel_target = None
        self.travel_finish_time = None

        self.route_probs = route_probs
        self.house_exchange_prob = house_exchange_prob
        self.pet_exchange_prob = pet_exchange_prob

        self.trip_count = 0

        self.knowledge = {
            self.id: {
                "nationality": self.nationality,
                "drink": self.drink,
                "cigarettes": self.cigarettes,
                "pet": self.pet,
                "house": self.house_id,
                "location": self.location
            }
        }
    
    def _get_agent_info(self):
        return {
            "nationality": self.nationality,
            "drink": self.drink,
            "cigarettes": self.cigarettes,
            "pet": self.pet,
            "house": self.house_id,
            "location": self.location
        }
    
    def update_knowledge(self, other_agent):
        self.knowledge[other_agent.id] = other_agent._get_agent_info()

    def choose_trip_target(self, travel_matrix, houses, color_to_prob_index):
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

    def __repr__(self):
        loc = self.location if self.location == self.house_id else f"travel→{self.location}"
        return (f"Agent(id={self.id}, nat={self.nationality}, "
                f"drink={self.drink}, cig={self.cigarettes}, pet={self.pet}, "
                f"home={self.house_id}, loc={loc})")

# House class representing a location
class House:
    def __init__(self, house_id, color, owner_id):
        self.id = house_id
        self.color = color
        self.owner_id = owner_id
        self.present_agents = set()

    def enter(self, agent_id):
        self.present_agents.add(agent_id)

    def leave(self, agent_id):
        self.present_agents.discard(agent_id)

    def set_owner(self, new_owner_id):
        self.owner_id = new_owner_id

    def is_owner_home(self):
        return self.owner_id in self.present_agents

    def __repr__(self):
        return (f"House(id={self.id}, color={self.color}, "
                f"owner={self.owner_id}, present={list(self.present_agents)})")

# Base Event class for simulation events
class Event:
    def __init__(self, time, agent_id=None):
        self.time = time
        self.agent_id = agent_id

    def run(self, env):
        return ([self.agent_id] if self.agent_id is not None else [], [])

    def is_invalid(self):
        return False

    def __lt__(self, other):
        return self.time < other.time

# Event for finishing a trip
class FinishTripEvent(Event):
    def __init__(self, time, agent_id, target_house):
        super().__init__(time, agent_id)
        self.target_house = target_house
        self.success = 0

    def run(self, env):
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
                    agent.update_knowledge(other_agent)
                    other_agent.update_knowledge(agent)

        return [agent.id], [self.target_house]

    def to_log_csv(self, event_number, env):
        agent = env.agents[self.agent_id]

        if self.target_house == agent.house_id:
            return f"{event_number};{self.time};FinishTrip;{agent.nationality};{self.target_house}"
        else:
            return f"{event_number};{self.time};FinishTrip;{self.success};{agent.nationality};{self.target_house}"

# Event for starting a trip
class StartTripEvent(Event):
    def __init__(self, time, agent_id, target_house):
        super().__init__(time, agent_id)
        self.target_house = target_house

    def run(self, env):
        agent = env.agents[self.agent_id]
        if agent.is_travelling:
            return [], []
        
        if not agent.is_travelling and agent.location in env.houses:
            env.houses[agent.location].leave(agent.id)
        
        agent.is_travelling = True
        agent.travel_target = self.target_house

        travel_time = env.travel_matrix[agent.location][self.target_house]
        if travel_time is None or travel_time <= 0:
            agent.is_travelling = False
            agent.travel_target = None
            return [], []
            
        arrival_time = self.time + travel_time
        finish_event = FinishTripEvent(arrival_time, agent.id, self.target_house)
        env.push_event(finish_event)

        agent.trip_count += 1

        return [agent.id], []

    def to_log_csv(self, event_number, env):
        agent = env.agents[self.agent_id]
        return f"{event_number};{self.time};StartTrip;{agent.nationality};{agent.location};{self.target_house}"

# Event for exchanging pets
class ChangePetEvent(Event):
    def __init__(self, time, participant_ids, pets_after_exchange):
        super().__init__(time)
        self.participant_ids = participant_ids
        self.pets_after_exchange = pets_after_exchange
        self.qty_participants = len(participant_ids)
        if self.qty_participants < 2:
            raise ValueError("Exchange requires at least 2 participants")
    
    def run(self, env):
        first_participant = env.agents[self.participant_ids[0]]
        house_id = first_participant.location
        house = env.houses[house_id]
        
        for agent_id, new_pet in zip(self.participant_ids, self.pets_after_exchange):
            agent = env.agents[agent_id]
            agent.pet = new_pet
            agent.knowledge[agent_id] = agent._get_agent_info()
        
        all_present = list(house.present_agents)
        for witness_id in all_present:
            witness = env.agents[witness_id]
            for participant_id in self.participant_ids:
                witness.update_knowledge(env.agents[participant_id])
        
        return self.participant_ids, []
    
    def to_log_csv(self, event_number, env):
        nationalities = [env.agents[agent_id].nationality for agent_id in self.participant_ids]
        
        parts = [
            str(event_number),
            str(self.time),
            "ChangePet",
            str(self.qty_participants)
        ]
        
        parts.extend(nationalities)
        parts.extend(self.pets_after_exchange)
        
        return ";".join(parts)

# Environment class managing the simulation
class Environment:
    def __init__(self, agents: dict, houses: dict, travel_matrix):
        self.agents = agents
        self.houses = houses
        self.travel_matrix = travel_matrix
        self.time = 0
        self.event_queue = []
        self.log = []
        
        self.color_to_prob_index = build_color_to_prob_index(houses)

        for house_id, house in houses.items():
            owner = house.owner_id
            house.enter(owner)

        for agent_id, agent in self.agents.items():
            target = agent.choose_trip_target(self.travel_matrix, self.houses, self.color_to_prob_index)
            if target is not None:
                start_event = StartTripEvent(time=0, agent_id=agent_id, target_house=target)
                self.push_event(start_event)

    def push_event(self, event):
        heapq.heappush(self.event_queue, event)

    def pop_all_events_with_time(self, t):
        events = []
        while self.event_queue and self.event_queue[0].time == t:
            events.append(heapq.heappop(self.event_queue))
        return events

    def detect_and_generate_exchanges(self):
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
                
                num_participants = min(len(ready_participants_sorted), 3)
                participants = ready_participants_sorted[:num_participants]
                
                current_pets = [self.agents[agent_id].pet for agent_id in participants]
                
                pets_after_exchange = current_pets[1:] + [current_pets[0]]
                
                exchange_events.append(ChangePetEvent(
                    time=self.time,
                    participant_ids=participants,
                    pets_after_exchange=pets_after_exchange
                ))
                
        return exchange_events

    def run(self, max_time):
        event_counter = 1
        csv_log = []

        while self.event_queue and self.time <= max_time:
            first_event = heapq.heappop(self.event_queue)
            t = first_event.time
            self.time = t

            batch = [first_event]
            while self.event_queue and self.event_queue[0].time == t:
                batch.append(heapq.heappop(self.event_queue))

            def event_priority(e):
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

            if finish_events:
                exchange_events = self.detect_and_generate_exchanges()
                for event in exchange_events:
                    event.run(self)
            else:
                exchange_events = []

            for event in start_events:
                event.run(self)

            for event in other_events:
                event.run(self)

            for event in finish_events:
                csv_log.append(event.to_log_csv(event_counter, self))
                event_counter += 1

            for event in exchange_events:
                csv_log.append(event.to_log_csv(event_counter, self))
                event_counter += 1

            for event in start_events:
                csv_log.append(event.to_log_csv(event_counter, self))
                event_counter += 1

            for event in finish_events:
                agent = self.agents[event.agent_id]
                if agent.trip_count < 10:
                    if agent.location == agent.house_id:
                        new_target = agent.choose_trip_target(self.travel_matrix, self.houses, self.color_to_prob_index)
                        if new_target is not None and new_target != agent.location:
                            travel_time = self.travel_matrix[agent.location][new_target]
                            if travel_time is not None and travel_time > 0:
                                future_time = self.time + travel_time
                                start_event = StartTripEvent(time=future_time, agent_id=agent.id, target_house=new_target)
                                self.push_event(start_event)
                    else:
                        home = agent.house_id
                        travel_time = self.travel_matrix[agent.location][home]
                        if travel_time is not None and travel_time > 0:
                            future_time = self.time + travel_time
                            start_event = StartTripEvent(time=future_time, agent_id=agent.id, target_house=home)
                            self.push_event(start_event)

        return csv_log

if __name__ == "__main__":
    strategies = load_strategies("ZEBRA-strategies.csv")
    agents, houses = load_initial_data("zebra-01.csv", strategies=strategies)
    T = load_geography("ZEBRA-geo.csv")

    env = Environment(agents, houses, T)
    log = env.run(max_time=40)

    for entry in log:
        print(entry)

    print("---- KNOWLEDGE ----")
    for a in env.agents.values():
        print(a.id, a.knowledge)
