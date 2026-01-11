# Zebra Puzzle — Multi-Agent Simulation

Симуляция классической «Зебра-проблемы» с использованием мультиагентной системы на Python. Агенты путешествуют между домами, обмениваются имуществом и накапливают знания друг о друге.

---

## Содержание

- [Описание проекта](#описание-проекта)
- [Архитектура](#архитектура)
- [Структура проекта](#структура-проекта)
- [Входные данные](#входные-данные)
- [Выходные данные](#выходные-данные)
- [Агенты и их характеристики](#агенты-и-их-характеристики)
- [Типы событий](#типы-событий)
- [Логирование и анализ](#логирование-и-анализ)
- [Детальное объяснение алгоритмов](#детальное-объяснение-алгоритмов)
  - [Min-Heap для очереди событий](#min-heap-для-очереди-событий)
  - [Batch Processing (Пакетная обработка)](#batch-processing-пакетная-обработка)
  - [Приоритеты событий](#приоритеты-событий)
  - [Обмен знаниями](#обмен-знаниями)

---

## Описание проекта

Симуляция моделирует взаимодействие n агентов на острове, где каждый агент:
- Имеет постоянный дом с определённым цветом
- Владеет домашним питомцем
- Следует собственной стратегии путешествий
- Может обмениваться домами и питомцами с другими агентами
- Накапливает знания о местонахождении и имуществе других агентов

### Агенты в симуляции

| ID | Национальность | Цвет дома | Питомец | Напиток | Сигареты |
|----|---------------|-----------|---------|---------|----------|
| 1 | Russian | Red | Dog | Water | Marlboro |
| 2 | English | Blue | Cat | Beer | Pall Mall |
| 3 | Chinese | Yellow | Zebra | Juice | Dunhill |
| 4 | German | Green | Fish | Whiskey | Kent |
| 5 | French | White | Humpster | Vodka | Camel |
| 6 | American | Black | Bear | Wine | Parliament |

### Масштабируемость

Симуляция **автоматически адаптируется под любое количество агентов**. Система не имеет жёстко закодированных ограничений на число участников.

**Ключевые механизмы масштабирования:**

```python
# Матрица расстояний строится динамически на основе данных CSV
num_houses = len(rows)
travel_matrix = [[None] * (num_houses + 1) for _ in range(num_houses + 1)]

# Агенты и дома создаются из входных данных
for line in f:
    house = House(house_id=house_id, color=color, owner_id=house_id)
    agent = Agent(agent_id=house_id, ...)
    agents[house_id] = agent

# Очередь событий работает с любым количеством агентов
while event_queue:
    batch = []  # Обрабатывает всех агентов одного времени
```

**Для добавления новых агентов достаточно:**
1. Добавить строку в `zebra-01.csv`
2. Добавить строку в `ZEBRA-geo.csv` (матрица расстояний)
3. Добавить строку в `ZEBRA-strategies.csv`

### Что происходит в симуляции

1. **Путешествия** — агенты выбирают цель и отправляются в путь, используя матрицу расстояний
2. **Встречи** — при успешном прибытии (владелец дома находится дома) агенты обмениваются знаниями
3. **Обмены** — готовые участники обмениваются домами и питомцами
4. **Знания** — каждый агент строит карту «кто где живёт и какой питомец»

---

## Архитектура

Симуляция построена на событийно-ориентированной архитектуре с использованием:

```
┌─────────────────────────────────────────────────────────────────┐
│                      Event-Driven Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────────────────────────────┐  │
│  │   EVENT      │────▶│  MIN-HEAP PRIORITY QUEUE             │  │
│  │   QUEUE      │     │  (сортировка по времени)             │  │
│  └──────────────┘     └──────────────────────────────────────┘  │
│         │                        │                              │
│         │                        ▼                              │
│         │              ┌─────────────────────┐                  │
│         │              │    BATCH PROCESS    │                  │
│         │              │  (все события t=5)  │                  │
│         │              └─────────────────────┘                  │
│         │                        │                              │
│         ▼                        ▼                              │
│  ┌──────────────┐     ┌─────────────────────┐                   │
│  │  ENVIRONMENT │────▶│      AGENTS &       │                   │
│  │    (run)     │     │      HOUSES         │                   │
│  └──────────────┘     └─────────────────────┘                   │
│                               │                                 │
│                               ▼                                 │
│                      ┌─────────────────┐                        │
│                      │   KNOWLEDGE     │                        │
│                      │     SYSTEM      │                        │
│                      └─────────────────┘                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Ключевые компоненты

| Компонент | Описание |
|-----------|----------|
| **Event Queue** | Min-heap для хранения и быстрого извлечения ближайших событий |
| **Batch Processor** | Группировка событий по времени для синхронной обработки |
| **Environment** | Центральный класс, управляющий симуляцией |
| **Agent** | Интеллектуальный агент со стратегией и базой знаний |
| **House** | Дом с владельцем и списком присутствующих агентов |

---

## Структура проекта

```
Zebra_Puzzle/
├── main.py                    # Точка входа в симуляцию
├── log_analyzer.py            # Анализ логов и построение графиков
├── README.md                  # Документация
├── entities/
│   ├── __init__.py
│   ├── agent.py              # Класс Agent
│   └── house.py              # Класс House
├── events/
│   ├── __init__.py
│   ├── base.py               # Базовый класс Event, константы приоритетов
│   ├── trip.py               # StartTripEvent, FinishTripEvent
│   └── exchange.py           # ChangeHouseEvent, ChangePetEvent
├── simulation/
│   ├── __init__.py
│   └── environment.py        # Environment — главный класс симуляции
├── loaders/
│   ├── __init__.py
│   └── csv_utils.py          # Загрузка CSV данных
├── knowledge_logging/
│   ├── __init__.py
│   └── knowledge_logger.py   # Логирование знаний агентов
└── data/
    ├── input_data/
    │   ├── zebra-01.csv              # Агенты, дома, атрибуты
    │   ├── ZEBRA-geo.csv             # Матрица расстояний
    │   └── ZEBRA-strategies.csv      # Стратегии агентов
    └── output_data/
        ├── logs/
        │   ├── observer.csv          # Главный лог событий
        │   └── agent_*_knowledge.log # Логи знаний агентов
        └── graphs/
            └── cumulative_events_graph.png
```

---

## Входные данные

### zebra-01.csv — Агенты и дома

**Формат:** `id;color;nationality;drink;cigarettes;pet`

| Поле | Описание | Пример |
|------|----------|--------|
| id | ID агента/дома | 1 |
| color | Цвет дома | Red |
| nationality | Национальность агента | Russian |
| drink | Любимый напиток | Water |
| cigarettes | Марка сигарет | Marlboro |
| pet | Домашний питомец | Dog |

**Пример содержимого:**
```
1;Red;Russian;Water;Marlboro;Dog
2;Blue;English;Beer;Pall Mall;Cat
3;Yellow;Chinese;Juice;Dunhill;Zebra
```

### ZEBRA-geo.csv — Матрица расстояний

**Формат:** `id;color;dist1;dist2;...;distN`

Матрица расстояний между домами (время путешествия). `NA` означает недоступный маршрут.

| Поле | Описание |
|------|----------|
| id | ID дома |
| color | Цвет дома |
| dist1...distN | Время путешествия до соответствующего дома |

**Пример содержимого:**
```
1;Red;0;6;8;2;3;1
2;Blue;5;0;4;1;2;10
```

### ZEBRA-strategies.csv — Стратегии агентов

**Формат:** `id;nation;route1;route2;route3;route4;route5;route6;house_exch;pet_exch`

| Поле | Описание | Пример |
|------|----------|--------|
| id | ID агента | 1 |
| nation | Национальность | Russian |
| route1-6 | Веса для выбора маршрутов по цветам | 100, 0, 0... |
| house_exch | Вероятность обмена домом (%) | 70 |
| pet_exch | Вероятность обмена питомцем (%) | 70 |

**Пример содержимого:**
```
1;Russian;100;0;0;0;0;0;70;70
2;English;30;10;10;25;25;0;50;50
```

---

## Выходные данные

### observer.csv — Главный лог событий

**Формат:** `event_num;time;event_type;details...`

| Колонка | Описание | Пример |
|---------|----------|--------|
| event_num | Порядковый номер события | 1 |
| time | Время события | 0 |
| event_type | Тип события | StartTrip |
| details | Дополнительная информация | Russian;1;5 |

**Примеры событий:**

```
1;0;StartTrip;Russian;1;5
2;5;FinishTrip;1;Russian;5
3;5;changeHouse;2;Russian;English;2;1
4;10;ChangePet;3;Chinese;German;French;Zebra;Fish;Humpster
```

### agent_*_knowledge.log — Индивидуальные логи знаний

Каждый агент имеет свой файл лога, где записываются изменения его базы знаний:

```
TIME=0; EVENT=INIT
  Agent 1 knowledge:
  {1: {'pet': 'Dog', 'house': 1, 'location': 1, 't': 0}}

TIME=5; EVENT=FinishTrip
  Agent 1 knowledge:
  {1: {'pet': 'Dog', 'house': 1, 'location': 5, 't': 5},
   2: {'pet': 'Cat', 'house': 2, 'location': 2, 't': 5}}
```

### cumulative_events_graph.png — График событий

Визуализация кумулятивного количества событий по времени симуляции.

---

## Агенты и их характеристики

### Структура класса Agent

```python
class Agent:
    def __init__(self, agent_id: int, nationality: str, drink: str, 
                 cigarettes: str, pet: str, house_id: int,
                 route_probs: Dict[int, int], house_exchange_prob: int, 
                 pet_exchange_prob: int):
        
        # Идентификация
        self.id = agent_id                    # Уникальный ID агента
        self.nationality = nationality        # Национальность
        self.drink = drink                    # Напиток
        self.cigarettes = cigarettes          # Сигареты
        self.pet = pet                        # Питомец
        
        # Местоположение
        self.house_id = house_id              # Постоянный дом (владеет)
        self.location = house_id              # Текущее местоположение
        self.is_travelling = False            # Флаг путешествия
        
        # Стратегия
        self.route_probs = route_probs        # Веса маршрутов по цветам
        self.house_exchange_prob = house_exchange_prob  # % обмена домом
        self.pet_exchange_prob = pet_exchange_prob      # % обмена питомцем
        
        # База знаний
        self.knowledge = {
            self.id: {
                'pet': pet,
                'house': house_id,
                'location': location,
                't': 0                        # Время последнего обновления
            }
        }
```

### Система знаний агента

Каждый агент хранит информацию об известных ему агентах:

```python
knowledge = {
    1: {                    # Агент знает о себе:
        'pet': 'Dog',       # Питомец
        'house': 1,         # Постоянный дом
        'location': 5,      # Текущее местоположение
        't': 120            # Время получения информации
    },
    2: {                    # Агент узнал об агенте 2:
        'pet': 'Cat',
        'house': 2,
        'location': 2,
        't': 125
    }
}
```

### Методы Agent

| Метод | Описание |
|-------|----------|
| `update_knowledge(other_agent, time)` | Обновляет информацию об агенте |
| `choose_trip_target(travel_matrix, houses, color_to_prob_index)` | Выбирает цель путешествия |
| `_get_agent_info()` | Возвращает публичную информацию об агенте |

---

## Типы событий

### Иерархия событий

```
Event (базовый класс)
├── StartTripEvent      — начало путешествия (приоритет: 3)
├── FinishTripEvent     — завершение путешествия (приоритет: 1)
├── ChangeHouseEvent    — обмен домами (приоритет: 2)
└── ChangePetEvent      — обмен питомцами (приоритет: 2)
```

### События путешествий

#### StartTripEvent

Создаётся когда агент решает отправиться в путь.

```python
class StartTripEvent(Event):
    def __init__(self, time: int, agent_id: int, target_house: int):
        self.time = time                    # Время начала
        self.agent_id = agent_id            # ID агента
        self.target_house = target_house    # Целевой дом
```

**Действия при выполнении:**
1. Агент покидает текущий дом (`house.leave()`)
2. Устанавливается флаг `is_travelling = True`
3. В очередь добавляется `FinishTripEvent` с временем прибытия

#### FinishTripEvent

Создаётся автоматически при `StartTripEvent`, срабатывает по прибытии.

```python
class FinishTripEvent(Event):
    def __init__(self, time: int, agent_id: int, target_house: int):
        self.time = time
        self.agent_id = agent_id
        self.target_house = target_house
        self.success = 0                    # 1 — владелец дома дома
```

**Действия при выполнении:**
1. Агент прибывает в целевой дом (`house.enter()`)
2. Проверяется, дома ли владелец дома
3. Если владелец дома — происходит **обмен знаниями** между всеми присутствующими
4. Генерируется `ChangeHouseEvent` при готовности участников

### События обмена

#### ChangeHouseEvent

Обмен постоянными домами между участниками.

```python
class ChangeHouseEvent(Event):
    def __init__(self, time: int, participant_ids: List[int], 
                 houses_after_exchange: List[int]):
        self.time = time
        self.participant_ids = participant_ids  # Список участников
        self.houses_after_exchange = houses_after_exchange  # Новые дома
```

**Действия при выполнении:**
1. Обновляются `house_id` всех участников
2. Обновляются владельцы домов
3. Свидетели обмена обновляют свои знания

#### ChangePetEvent

Обмен питомцами между участниками.

```python
class ChangePetEvent(Event):
    def __init__(self, time: int, participant_ids: List[int], 
                 pets_after_exchange: List[str]):
        self.time = time
        self.participant_ids = participant_ids  # Список участников
        self.pets_after_exchange = pets_after_exchange  # Новые питомцы
```

**Действия при выполнении:**
1. Обновляются `pet` всех участников
2. Обновляются знания участников о себе
3. Свидетели обмена обновляют свои знания

### Жизненный цикл события

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  СОЗДАНИЕ    │────▶│  В ОЧЕРЕДИ   │────▶│   ВЫПОЛНЕНИЕ │
│ (push_event) │     │   (heapq)    │     │    (run)     │
└──────────────┘     └──────────────┘     └──────────────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │  ЛОГИРОВАНИЕ │
                                    │   (log)      │
                                    └──────────────┘
```

---

## Логирование и анализ

### AgentKnowledgeLogger

Отслеживает изменения базы знаний каждого агента.

```python
class AgentKnowledgeLogger:
    def log_knowledge_change(self, time: int, agent_id: int, 
                             event_type: str, knowledge_after: dict):
        """Логирует изменение знаний агента"""
        
    def close_all(self):
        """Закрывает все файлы логов"""
```

### SimulationAnalyzer

Анализирует лог событий и строит графики.

```python
class SimulationAnalyzer:
    def run_complete_analysis(self):
        """Запускает полный анализ логов"""
```

### Формат лога знаний

```
TIME=0; EVENT=INIT
  Agent 1 knowledge:
  {1: {'pet': 'Dog', 'house': 1, 'location': 1, 't': 0}}

TIME=5; EVENT=FinishTrip
  Agent 1 knowledge:
  {1: {'pet': 'Dog', 'house': 1, 'location': 5, 't': 5},
   2: {'pet': 'Cat', 'house': 2, 'location': 2, 't': 5}}
```

---

## Детальное объяснение алгоритмов

### Min-Heap для очереди событий

Очередь событий реализована как **min-heap** с использованием модуля `heapq`. Это обеспечивает O(1) для получения ближайшего события и O(log n) для вставки.


#### Реализация

```python
import heapq

class Event:
    def __lt__(self, other: 'Event') -> bool:
        # Min-heap сортирует по возрастанию времени
        return self.time < other.time

# Добавление события
event = FinishTripEvent(time=5, agent_id=1, target_house=3)
heapq.heappush(event_queue, event)

# Извлечение ближайшего события
next_event = heapq.heappop(event_queue)
```

#### Структура очереди событий

```
event_queue (min-heap):
┌─────────────────────────────────────────────────┐
│                                                 │
│   ┌───┐                                         │
│   │ 0 │ ─── FinishTripEvent(time=5, agent=2)    │
│   ├───┤                                         │
│   │ 1 │ ─── FinishTripEvent(time=5, agent=3)    │
│   ├───┤                                         │
│   │ 2 │ ─── StartTripEvent(time=8, agent=1)     │
│   ├───┤                                         │
│   │ 3 │ ─── FinishTripEvent(time=10, agent=4)   │
│   └───┘                                         │
│                                                 │
│   root = минимальное время (5)                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Batch Processing (Пакетная обработка)

#### Что такое Batch?

**Batch** — это группа всех событий с одинаковым временем `time`. Все события, происходящие в одно и то же время, обрабатываются **вместе**.

```python
while event_queue and self.time <= max_time:
    # 1. Получаем время следующего события
    t = self.event_queue[0].time
    self.time = t
    
    # 2. Извлекаем ВСЕ события с этим временем → BATCH
    batch = []
    while self.event_queue and self.event_queue[0].time == t:
        batch.append(heapq.heappop(self.event_queue))
    
    # 3. Обрабатываем batch
    self._process_batch_events(batch)
```

#### Почему Batch важен?

**Критический пример:**

```
Время t=5 в очереди:
  - Агент 2 завершает путешествие (FinishTrip)
  - Агент 3 завершает путешествие (FinishTrip)
  
После прибытия обоих, в доме 2 находятся: agent=2, agent=3

→ ПРОИСХОДИТ ОБМЕН между всеми присутствующими!

Если бы обрабатывали по отдельности:
  - agent=2 прибыл, в доме никого → обмена нет
  - agent=3 прибыл, в доме только agent=3 → обмена нет
  
Результат: обмен НЕ происходит ❌
```

#### Как работает Batch Processing

```python
def _process_batch_events(self, batch: List[Event]):
    """
    Полный pipeline обработки batch
    
    Batch t=5: [FinishTrip(agent=2), FinishTrip(agent=3)]
    """
    
    # Шаг 1: Сортировка по приоритету
    batch.sort(key=event_priority)
    
    # Шаг 2: Разделение по типам
    finish_events = [e for e in batch if isinstance(e, FinishTripEvent)]
    start_events = [e for e in batch if isinstance(e, StartTripEvent)]
    other_events = [e for e in batch if not isinstance(e, (FinishTripEvent, StartTripEvent))]
    
    # Шаг 3: Выполнение в порядке приоритета
    # 3.1: FinishTrip (прибытие) - проверка, обмен знаниями
    for event in finish_events:
        event.run(self)
    
    # 3.2: Генерация обменов питомцами
    exchange_events = []
    if finish_events:
        exchange_events = self.detect_and_generate_exchanges()
        for event in exchange_events:
            event.run(self)
    
    # 3.3: StartTrip (новые путешествия)
    for event in start_events:
        event.run(self)
    
    # 3.4: Остальные события (обмены домами)
    for event in other_events:
        event.run(self)
```

#### Детальная последовательность обработки batch

```
BATCH t=5: [FinishTrip(agent=1), FinishTrip(agent=2)]

│
├── Фаза 1: FinishTrip
│   │
│   ├── agent=1 прибывает в дом 3
│   │   ├── В доме 3 есть agent=3
│   │   ├── Владелец (agent=3) дома → success=1
│   │   ├── agent=1 и agent=3 обмениваются знаниями
│   │   └── Проверка: хочет ли agent=3 менять дом?
│   │
│   ├── agent=2 прибывает в дом 1
│   │   ├── В доме 1 есть agent=1 (вернулся), agent=2
│   │   ├── Владелец (agent=1) дома → success=1
│   │   └── agent=1 и agent=2 обмениваются знаниями
│   │
│   └── После всех FinishTrip: генерируем ChangePetEvent
│       └── ChangePetEvent запускается для готовых участников
│
├── Фаза 2: StartTrip
│   │
│   ├── agent=3 решает поехать в дом 5
│   │   └── Создаётся FinishTripEvent(time=5+travel_time)
│   │
│   └── agent=4 решает поехать в дом 2
│       └── Создаётся FinishTripEvent(time=5+travel_time)
│
└── Фаза 3: Planning (планирование новых путешествий)
    │
    ├── agent=1 (дома) → выбирает новую цель
    ├── agent=3 (в пути) → ничего
    └── agent=5 (дома) → выбирает новую цель
```

### Приоритеты событий

#### Таблица приоритетов

| Приоритет | Событие | Описание |
|-----------|---------|----------|
| **1** | `FinishTripEvent` | Завершение путешествия |
| **2** | `ChangePetEvent` / `ChangeHouseEvent` | Обмены |
| **3** | `StartTripEvent` | Начало путешествия |

#### Реализация приоритетов

```python
# Константы в events/base.py
EVENT_PRIORITY_FINISH_TRIP = 1
EVENT_PRIORITY_EXCHANGE = 2
EVENT_PRIORITY_START_TRIP = 3

def event_priority(e: Event) -> int:
    """
    Возвращает приоритет события для сортировки
    Меньше = выше приоритет (выполняется раньше)
    """
    if isinstance(e, FinishTripEvent):
        return EVENT_PRIORITY_FINISH_TRIP  # = 1 (высший)
    elif hasattr(e, 'participant_ids'):
        return EVENT_PRIORITY_EXCHANGE     # = 2
    else:
        return EVENT_PRIORITY_START_TRIP   # = 3
```

#### Зачем нужны приоритеты?

**Проблема: что если в batch есть и FinishTrip и StartTrip?**

```python
batch = [FinishTrip(agent=1), StartTrip(agent=2)]
```

**Сценарий 1: БЕЗ приоритетов (произвольный порядок)**

```
Порядок: StartTrip(2), FinishTrip(1)

StartTrip(2): agent=2 уезжает из дома 1
FinishTrip(1): agent=1 прибывает в дом 1
               В доме 1 НЕТ agent=2 (он уехал!)
               → Обмена знаниями НЕ происходит! ❌
```

**Сценарий 2: С ПРИОРИТЕТАМИ (FinishTrip = 1, StartTrip = 3)**

```
Порядок: FinishTrip(1), StartTrip(2)

FinishTrip(1): agent=1 прибывает в дом 1
               В доме 1 есть agent=2
               → agent=1 и agent=2 обмениваются знаниями ✓
StartTrip(2): agent=2 уезжает из дома 1
               → Обмен уже произошёл ✓
```

**Результат:** Приоритеты гарантируют корректный порядок выполнения событий!

### Обмен знаниями

#### Когда происходит обмен знаниями?

**Только при успешном FinishTrip!**

```python
class FinishTripEvent(Event):
    def run(self, env: 'Environment'):
        # ... прибытие агента ...
        
        self.success = 1 if house.is_owner_home() else 0
        
        if self.success == 1:
            # Обмен знаниями между ВСЕМИ присутствующими
            for other_id in list(house.present_agents):
                if other_id != agent.id:
                    other_agent = env.agents[other_id]
                    
                    # Агент узнаёт об other_agent
                    agent.update_knowledge(other_agent, self.time)
                    
                    # other_agent узнаёт об агенте
                    other_agent.update_knowledge(agent, self.time)
```

#### Формат знаний

```python
# Агент 1 знает о себе:
{
    'pet': 'Dog',
    'house': 1,      # Свой постоянный дом
    'location': 5,   # Где находится сейчас
    't': 120         # Время получения информации
}

# Агент 1 узнал об агенте 2:
{
    'pet': 'Cat',
    'house': 2,
    'location': 2,
    't': 125
}
```

#### Обновление знаний

```python
def update_knowledge(self, other_agent: 'Agent', time: int) -> None:
    """
    Обновляет базу знаний информацией об other_agent
    """
    self.knowledge[other_agent.id] = {
        **other_agent._get_agent_info(),  # pet, house, location
        "t": time                          # Время получения
    }
```

#### Свидетели обменов

При обменах (домами/питомцами) **свидетели** тоже обновляют знания:

```python
class ChangeHouseEvent(Event):
    def run(self, env: 'Environment'):
        # ... обмен домами участников ...
        
        # Все свидетели узнают об изменениях
        for witness_id in list(house.present_agents):
            witness = env.agents[witness_id]
            for participant_id in self.participant_ids:
                witness.update_knowledge(
                    env.agents[participant_id], 
                    self.time
                )
```

### Главный цикл симуляции

```python
def run(self, max_time: int) -> List[str]:
    """
    Главный цикл симуляции
    
    Алгоритм:
    1. Пока есть события и time <= max_time:
    2.   Получить текущее время t = min(event_queue)
    3.   Извлечь ВСЕ события с time == t → BATCH
    4.   Обработать BATCH (события сортируются по приоритету)
    5.   Запланировать новые путешествия для завершённых
    """
    
    event_counter = 1
    csv_log = []
    
    while self.event_queue and self.time <= max_time:
        # 1. Получаем время следующего batch
        t = self.event_queue[0].time
        self.time = t
        
        # 2. Извлекаем ВСЕ события с этим временем
        batch = []
        while self.event_queue and self.event_queue[0].time == self.time:
            batch.append(heapq.heappop(self.event_queue))
        
        if not batch:
            break
        
        # 3. Сортируем batch по приоритету
        batch.sort(key=lambda e: (
            EVENT_PRIORITY_FINISH_TRIP if isinstance(e, FinishTripEvent) else
            EVENT_PRIORITY_EXCHANGE if hasattr(e, 'participant_ids') else
            EVENT_PRIORITY_START_TRIP
        ))
        
        # 4. Обрабатываем batch
        finish_events, start_events, other_events, exchange_events = \
            self._process_batch_events(batch)
        
        # 5. Логируем
        event_counter = self._log_events(
            finish_events, exchange_events, 
            self.house_exchange_events, start_events,
            event_counter, csv_log
        )
        self.house_exchange_events.clear()
        
        # 6. Планируем новые путешествия
        self._plan_new_trips(finish_events)
    
    return csv_log
```

---

## Запуск

```bash
# Установка зависимостей
pip install numpy matplotlib

# Запуск симуляции
python main.py

# Или только анализ (если лог уже есть)
python log_analyzer.py
```

### Параметры симуляции

В `main.py` можно настроить:

```python
max_time = 2000  # Максимальное время симуляции
```

---
