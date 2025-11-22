import random
import heapq


def load_initial_data(path_to_zebra_01):
   
    agents = {}
    houses = {}

    with open(path_to_zebra_01, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(';')
            house_id, color, nation, drink, smoke, pet = parts
            house_id = int(house_id)

            # Создаём дом
            house = House(house_id=house_id, color=color, owner_id=house_id)
            houses[house_id] = house

            # Создаём агента
            agent = Agent(
                agent_id=house_id,
                nationality=nation,
                drink=drink,
                cigarettes=smoke,
                pet=pet,
                house_id=house_id,
                route_probs={},        # пока пусто
                house_exchange_prob=0, # пока 0
                pet_exchange_prob=0    # пока 0
            )
            agents[house_id] = agent

    return agents, houses


def load_geography(path_to_geography):
    """
    Загружает карту домов и расстояний из CSV и строит travel_matrix.

    CSV формат:
        house;color;d1;d2;...;dN
    На диагонали 0, NA или пустое = None

    Возвращает:
        list[list[int | None]] — матрица travel_matrix, индексация домов с 1
    """
    rows = []

    with open(path_to_geography, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(line.split(';'))

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

        # -------------------- агент знает только про себя --------------------
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

    # -------------------- метод обновления знаний --------------------
    def update_knowledge(self, other_agent):
        self.knowledge[other_agent.id] = {
            "nationality": other_agent.nationality,
            "drink": other_agent.drink,
            "cigarettes": other_agent.cigarettes,
            "pet": other_agent.pet,
            "house": other_agent.house_id,
            "location": other_agent.location
        }

    def choose_trip_target(self, travel_matrix):
    # идём по индексам 1..N (игнорируем 0)
        possible_targets = [
            h for h in range(1, len(travel_matrix))
            if travel_matrix[self.location][h] is not None and h != self.location
        ]
        if not possible_targets:
            return None
        return random.choice(possible_targets)

    def __repr__(self):
        loc = self.location if self.location == self.house_id else f"travel→{self.location}"
        return (f"Agent(id={self.id}, nat={self.nationality}, "
                f"drink={self.drink}, cig={self.cigarettes}, pet={self.pet}, "
                f"home={self.house_id}, loc={loc})")



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


class Event:
    def __init__(self, time, agent_id=None):
        self.time = time
        self.agent_id = agent_id

    def run(self, env):
        return ([self.agent_id] if self.agent_id is not None else [], [])

    def to_log_string(self):
        return f"{self.time};BASE_EVENT;agent={self.agent_id}"

    def isInvalid(self):
        return False

    def __lt__(self, other):
        return self.time < other.time

class FinishTripEvent(Event):
    def __init__(self, time, agent_id, target_house):
        super().__init__(time, agent_id)
        self.target_house = target_house

    def run(self, env):
        agent = env.agents[self.agent_id]
        agent.is_travelling = False
        agent.location = self.target_house
        house = env.houses[self.target_house]
        house.enter(agent.id)

        # успех — встретил хозяина дома?
        self.success = 1 if env.houses[self.target_house].is_owner_home() else 0
        
        print(f"{env.time};FinishTrip;{self.success};{agent.nationality};{self.target_house}")

         # -------------------- обмен знаниями с другими агентами --------------------
        for other_id in house.present_agents:
            if other_id != agent.id:
                other_agent = env.agents[other_id]
                agent.update_knowledge(other_agent)
                other_agent.update_knowledge(agent)

        # -------------------- добавляем новую поездку --------------------
        new_target = agent.choose_trip_target(env.travel_matrix)
        if new_target is not None:
            start_event = StartTripEvent(time=env.time, agent_id=agent.id, target_house=new_target)
            env.push_event(start_event)

        return [agent.id], [self.target_house]
    
    def to_log_csv(self, event_number, env):
        agent = env.agents[self.agent_id]

        return f"{event_number};{self.time};FinishTrip;{self.success};{agent.nationality};{self.target_house}"

    def to_log_string(self):
        return f"{self.time};FINISH_TRIP;agent={self.agent_id};house={self.target_house}"
    
class StartTripEvent(Event):
    def __init__(self, time, agent_id, target_house):
        super().__init__(time, agent_id)
        self.target_house = target_house

    def run(self, env):
        agent = env.agents[self.agent_id]
        env.houses[agent.location].leave(agent.id)
        agent.is_travelling = True
        agent.travel_target = self.target_house

        travel_time = env.travel_matrix[agent.location][self.target_house]
        agent.travel_finish_time = env.time + travel_time

        finish_event = FinishTripEvent(agent.travel_finish_time, agent.id, self.target_house)
        env.push_event(finish_event)

        print(f"{env.time};startTrip;{agent.nationality};{agent.location};{self.target_house}")

        return [agent.id], []

    def to_log_csv(self, event_number, env):
        agent = env.agents[self.agent_id]
        return f"{event_number};{self.time};startTrip;{agent.nationality};{agent.location};{self.target_house}"
    

class Environment:
    def __init__(self, agents: dict, houses: dict, travel_matrix):
        self.agents = agents
        self.houses = houses
        self.travel_matrix = travel_matrix
        self.time = 0
        self.event_queue = []
        self.log = []

        # Агент по умолчанию в своём доме
        for house_id, house in houses.items():
            owner = house.owner_id
            house.enter(owner)

        # -------------------- Первичные поездки всех агентов --------------------
        for agent_id, agent in self.agents.items():
            target = agent.choose_trip_target(self.travel_matrix)
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
        """
        Пока skeleton: позже сюда будет логика обменов.
        Возвращает список новых событий обмена времени t.
        """
        return []

    def run(self, max_time):
        
        event_counter = 1  # глобальный счётчик событий
        csv_log = []       # список строк CSV

        while self.event_queue and self.time < max_time:
            # -------------------- Шаг 1: извлекаем все события с минимальным временем --------------------
            first_event = heapq.heappop(self.event_queue)
            t = first_event.time
            self.time = t

            batch = [first_event] + self.pop_all_events_with_time(t)

            # -------------------- Шаг 2: сортируем finishTrip → exchange → startTrip --------------------
            # exchange_events будут вставлены позже, пока сортируем finish и start
            def event_priority(e):
                if isinstance(e, FinishTripEvent):
                    return 1
                elif isinstance(e, StartTripEvent):
                    return 3
                else:
                    return 2
            batch.sort(key=event_priority)

            # -------------------- Шаг 3: выполняем все FinishTrip --------------------
            finish_events = [e for e in batch if isinstance(e, FinishTripEvent)]
            for event in finish_events:
                event.run(self)
                # успех поездки (успел встретить хозяина) сохранён в event.success

            # -------------------- Шаг 4: генерируем события обменов --------------------
            exchange_events = self.detect_and_generate_exchanges()
            # exchange_events должны иметь время t и будут вставлены перед startTrip

            # -------------------- Шаг 5: формируем итоговый порядок для выполнения и логирования --------------------
            start_events = [e for e in batch if isinstance(e, StartTripEvent)]
            final_batch = finish_events + exchange_events + start_events

            # -------------------- Шаг 6: выполняем все StartTrip --------------------
            for event in start_events:
                event.run(self)

            # -------------------- Шаг 7: логируем все события в CSV --------------------
            for event in final_batch:
                # используем новый метод to_log_csv(event_number, env)
                csv_log.append(event.to_log_csv(event_counter, self))
                event_counter += 1

        return csv_log


# Загружаем данные
agents, houses = load_initial_data("zebra-01.csv")
T = load_geography("ZEBRA-geo.csv")

# Создаём окружение
env = Environment(agents, houses, T)


# Запускаем симуляцию
log = env.run(max_time=10)

# Печатаем CSV-лог
for entry in log:
    print(entry)
