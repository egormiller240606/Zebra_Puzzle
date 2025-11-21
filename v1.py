import random
import heapq


def load_initial_data(path_to_zebra_01):
    """
    Загружает данные агентов из CSV-файла и формирует словарь по номеру дома.

    Каждая строка CSV должна содержать:
        house;color;nation;drink;smoke;pet
        (проверки формата нет — предполагается, что CSV корректен)

    Возвращает:
        dict: Словарь, где ключ — номер дома (house),
        а значение — словарь с характеристиками агента:
            {
                'color': str,      # цвет дома
                'nation': str,     # нация агента
                'drink': str,      # любимый напиток
                'smoke': str,      # сигарета
                'pet': str         # питомец
            }
    """
    agent_specs = {}

    with open(path_to_zebra_01, encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            parts = line.split(';')
            house, color, nation, drink, smoke, pet = parts
            house = int(house)

            agent_specs[house] = {
                'color': color,
                'nation': nation,
                'drink': drink,
                'smoke': smoke,
                'pet': pet
            }

    return agent_specs


def load_geography(path_to_geography):
    """
    Загружает карту домов и расстояний из CSV и строит матрицу T (*мин размер 3 на 3*).

    Формат CSV:
        house;color;d1;d2;...;dN
        - house: номер дома
        - color: цвет дома
        - d1..dN: расстояния до других домов (NA — недоступно, пустое — тоже недоступно)
        - на диагонали (дом сам с собой) может стоять 0

    Возвращает:
        list[list[int | None]]: матрица размера (num_houses + 1) x (num_houses + 1),
        где индексация домов с 1.
        T[a][b] — расстояние из дома a в дом b.
        Значения:
            - int > 0 — расстояние между домами
            - 0 — если a == b (дом сам с собой)
            - None — если поездка невозможна или данных нет (NA или пустое)
    """
    rows = []

    with open(path_to_geography, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            rows.append(line.split(';'))

    num_houses = len(rows)
    T = [[None] * (num_houses + 1) for _ in range(num_houses + 1)]

    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row[2:], start=1):
            if i == j:
                T[i][j] = 0
            elif val.strip().upper() == "NA" or val.strip() == "":
                T[i][j] = None
            else:
                T[i][j] = int(val)

    return T

class Agent:
    """
    Агент, который живет в доме и может совершать поездки к другим домам.

    Attributes:
        house (int): текущий дом агента.
        home (int): постоянный дом агента (откуда начинается каждая поездка).
        specs (dict): характеристики агента (color, nation, drink, smoke, pet и т.д.).
        on_trip (bool): True, если агент находится в поездке.
        target_house (int | None): дом, куда агент направляется в текущей поездке.
    """
    def __init__(self, house, specs):
        self.house = house
        self.home = house  
        self.specs = specs
        self.on_trip = False
        self.target_house = None
    
    def choose_destination(self, num_houses):
        """Случайно выбирает целевой дом, отличный от текущего пока с равной вероятностью"""
        possible = [h for h in range(1, num_houses + 1) if h != self.house]
        return random.choice(possible)

    def schedule_trip(self, environment, target):
        """
        Планирует поездку агента: создаёт события startTrip и finishTrip в FEL.

        Args:
            environment (Environment): объект симуляции.
            target (int): номер дома для поездки.

        Notes:
            - dist = None или 0 → поездка не планируется.
            - startTrip выполняется при обработке события из FEL.
            - finishTrip логируется при фактическом прибытии.
        """
        if target is None:
            return  # target должен быть целым числом
        dist = environment.T[self.house][target]
        if dist is None or dist == 0:
            return

        self.target_house = target
        self.on_trip = True

        # Планируем startTrip на текущее время
        environment.push_event(environment.time, "startTrip", self.house)
        # Планируем finishTrip на environment.time + dist
        finish_time = environment.time + dist
        environment.push_event(finish_time, "finishTrip", self.house)


class Environment:
    """
    Среда событийной симуляции для агентов.

    Attributes:
        T (list[list[int | None]]): матрица расстояний между домами.
        time (int): текущее время симуляции.
        FEL (list[tuple]): очередь будущих событий (time, eventtype, house).
        log (list[tuple]): журнал всех событий.
        population (dict[int, Agent]): агенты по номеру дома.
    """
    def __init__(self, agent_specs, T):
        self.T = T
        self.time = 0
        self.FEL = [] 
        self.log = []
        self.population = {}
        self.event_counter = 0

        for house, specs in agent_specs.items():
            person = Agent(house, specs)
            self.population[house] = person

    def push_event(self, t, eventtype, house):
        """Добавляет событие в очередь FEL."""
        heapq.heappush(self.FEL, (t, eventtype, house))

    def log_event(self, t, eventtype, house, target=None):
        """Логирует событие в журнал симуляции."""
        self.event_counter += 1
        self.log.append((self.event_counter, t, eventtype, house, target))


    def step_new_trips(self):
        """Планирует новые поездки для свободных агентов, находящихся дома."""
        num_houses = len(self.population)
        for agent in self.population.values():
            if agent.on_trip or agent.house != agent.home:
                continue
            target = agent.choose_destination(num_houses)
            agent.schedule_trip(self, target)

    def process_finish_trip(self, house):
        """Обрабатывает завершение поездки агента и планирует возврат домой или новые поездки."""
        agent = self.population[house]

        # Завершение поездки только если target_house валиден
        if agent.target_house is not None:
            agent.house = agent.target_house
            agent.target_house = None
            self.log_event(self.time, "finishTrip", house)

        # Планируем возвращение домой, только если home валиден
        if agent.house != agent.home and agent.home is not None:
            agent.schedule_trip(self, agent.home)
        else:
            agent.on_trip = False
            self.step_new_trips()

    def run(self, Tmax=50):
        """Главный цикл событийной симуляции с обработкой всех событий FEL.

        Логика:
            1. Достаём все события с минимальным временем t.
            2. Сортируем события: finishTrip < startTrip.
            3. Обрабатываем finishTrip.
            4. Выполняем обмены (process_exchanges).
            5. Обрабатываем startTrip и логируем.
        """
        self.step_new_trips()  # стартовые поездки

        while self.FEL and self.time < Tmax:
            # 1. Определяем минимальное время событий
            current_t = self.FEL[0][0]
            self.time = current_t

            # 2. Достаём все события с current_t
            events = []
            while self.FEL and self.FEL[0][0] == current_t:
                events.append(heapq.heappop(self.FEL))

            # 3. Сортируем: finishTrip < startTrip
            events.sort(key=lambda x: 0 if x[1] == "finishTrip" else 1)

            # 4. Обрабатываем finishTrip
            for t, eventtype, house in events:
                if eventtype == "finishTrip":
                    self.process_finish_trip(house)

            # 5. Выполняем обмены
            # <-- сюда вставить логику обменов

            # 6. Обрабатываем startTrip и логируем
            for _, eventtype, house in events:
                if eventtype == "startTrip":
                    agent = self.population[house]
                    if agent.target_house is not None:  # проверка на None
                        self.log_event(self.time, "startTrip", house, agent.target_house)


        return self.log


path_to_zebra_01 = "zebra-01.csv"
agent_specs = load_initial_data(path_to_zebra_01)

path_to_geography = "ZEBRA-geo.csv"
T = load_geography(path_to_geography)

env = Environment(agent_specs, T)
log = env.run(Tmax=50)

for entry in log:
    print(entry)


#добавить класс house чтоб не было лишних циуклов (туда поля агнета ??)

#исправить логи как в overleaf  (1;Russian (излишне ?))

#что-то сделать с обменами 

#сделать завершение процессов, даже если t вылетело за предел

#читать файлик с вероятностями

"""

"""