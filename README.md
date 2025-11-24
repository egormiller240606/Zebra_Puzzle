# Zebra Puzzle Simulation

## Описание проекта

Этот проект представляет собой агентную модель симуляции "Zebra Puzzle" (загадки Эйнштейна), где агенты (жители домов) путешествуют между домами, обмениваются питомцами и обновляют свои знания о других агентах. Симуляция основана на дискретно-событийном подходе с приоритетами событий.

## Требования

- Python 3.7+
- Стандартные библиотеки: `random`, `heapq`, `typing`

## Установка и запуск

1. Убедитесь, что файлы данных находятся в той же директории:
   - `zebra-01.csv` - инициализация агентов и домов
   - `ZEBRA-strategies.csv` - стратегии агентов
   - `ZEBRA-geo.csv` - матрица расстояний

2. Запустите симуляцию:
   ```bash
   python Simulation.py
   ```

3. Вывод:
   - CSV-лог событий в stdout
   - Финальные знания агентов

## Структура файлов данных

### zebra-01.csv
Инициализация агентов и домов. Формат:
```
house_id;color;nation;drink;smoke;pet
1;Red;Russian;Water;Marlboro;Dog
2;Green;English;Beer;Pall Mall;Cat
...
```

- `house_id`: уникальный идентификатор дома (1-6)
- `color`: цвет дома
- `nation`: национальность агента
- `drink`: предпочитаемый напиток
- `smoke`: марка сигарет
- `pet`: питомец

### ZEBRA-strategies.csv
Стратегии поведения агентов. Формат:
```
agent_id;nation;route_prob1;route_prob2;route_prob3;route_prob4;route_prob5;route_prob6;house_exch_prob;pet_exch_prob
1;Russian;10;5;0;0;0;0;20;30
...
```

- `route_prob1-6`: вероятности выбора маршрута к домам соответствующих цветов (индексы 1-6)
- `house_exch_prob`: вероятность обмена домами (%)
- `pet_exch_prob`: вероятность обмена питомцами (%)

### ZEBRA-geo.csv
Матрица расстояний между домами. Формат:
```
house_id;color;dist_to_1;dist_to_2;dist_to_3;dist_to_4;dist_to_5;dist_to_6
1;Red;0;4;NA;NA;NA;1
...
```

- `NA`: недоступный маршрут
- Числа: время путешествия в единицах времени

## Архитектура кода

### Основные классы

#### Класс Agent
Представляет агента-жителя.

**Атрибуты:**
- `id`: уникальный идентификатор
- `nationality`: национальность
- `drink`, `cigarettes`, `pet`: характеристики
- `house_id`: дом-владелец
- `location`: текущая локация
- `is_travelling`: флаг путешествия
- `route_probs`: словарь вероятностей маршрутов
- `house_exchange_prob`, `pet_exchange_prob`: вероятности обменов
- `knowledge`: словарь известной информации о других агентах

**Методы:**
- `update_knowledge(other_agent)`: обновляет знания об агенте
- `choose_trip_target()`: выбирает цель путешествия на основе вероятностей и географии

#### Класс House
Представляет дом/локацию.

**Атрибуты:**
- `id`: идентификатор дома
- `color`: цвет дома
- `owner_id`: владелец
- `present_agents`: множество присутствующих агентов

**Методы:**
- `enter(agent_id)`, `leave(agent_id)`: управление присутствием
- `set_owner(new_owner_id)`: смена владельца
- `is_owner_home()`: проверка, дома ли владелец

#### Класс Event (базовый)
Базовый класс для событий симуляции.

**Подклассы:**
- `StartTripEvent`: начало путешествия
- `FinishTripEvent`: завершение путешествия
- `ChangePetEvent`: обмен питомцами
- `ChangeHouseEvent`: обмен домами

#### Класс Environment
Управляет всей симуляцией.

**Атрибуты:**
- `agents`: словарь агентов
- `houses`: словарь домов
- `travel_matrix`: матрица расстояний
- `time`: текущее время
- `event_queue`: очередь событий (heap)
- `log`: список записей лога

**Методы:**
- `push_event(event)`: добавляет событие в очередь
- `run(max_time)`: запускает симуляцию
- `detect_and_generate_exchanges()`: генерирует события обмена питомцами

### Вспомогательные функции

- `parse_csv_line()`: парсит строку CSV
- `log_formatter()`: форматирует запись лога
- `load_strategies()`, `load_initial_data()`, `load_geography()`: загрузка данных
- `build_color_to_prob_index()`: маппинг цветов к индексам вероятностей

## Логика симуляции

### Инициализация
1. Загрузка данных из CSV-файлов
2. Создание агентов и домов
3. Инициализация знаний (каждый знает себя)
4. Планировка первых путешествий для всех агентов

### Цикл симуляции
Пока есть события и время ≤ max_time:
1. Извлечение батча событий на текущем времени
2. Обработка событий по приоритетам:
   - `FinishTrip` (приоритет 1)
   - `Exchange` (приоритет 2)
   - `StartTrip` (приоритет 3)
3. Логирование событий
4. Генерация новых событий (обмены, новые путешествия)

### Обработка событий

#### StartTripEvent
- Проверка возможности путешествия
- Установка флага путешествия
- Расчет времени прибытия
- Создание FinishTripEvent

#### FinishTripEvent
- Обновление локации агента
- Проверка успеха (встреча с владельцем дома)
- При успехе: обмен знаниями между присутствующими
- Генерация событий обмена питомцами (если условия выполнены)

#### ChangePetEvent
- Циклический обмен питомцами между участниками
- Обновление знаний всех присутствующих в доме

#### ChangeHouseEvent
- Циклический обмен домами между участниками
- Обновление знаний всех присутствующих в доме
- Обновление владельцев домов

### Планировка путешествий
После FinishTrip:
- Если агент дома: планирует новое путешествие (выбор цели по вероятностям)
- Если не дома: планирует возвращение домой

### Обмен питомцами
- Происходит после успешных прибытий
- Для каждого дома с ≥2 агентами
- Агенты участвуют с вероятностью `pet_exchange_prob`
- Минимум 2 участника, максимум 3
- Циклический обмен: A→B→C→A

### Обмен домами
- Происходит после успешных прибытий в дом прибытия
- Для дома прибытия с ≥2 агентами и владельцем дома
- Агенты участвуют с вероятностью `house_exchange_prob`
- Минимум 2 участника
- Циклический обмен домами: A→B→C→A
- После обмена агенты планируют поездки в новые дома, если location != house_id

## Система знаний

Каждый агент ведет словарь `knowledge`:
```python
{
    agent_id: {
        "nationality": str,
        "drink": str,
        "cigarettes": str,
        "pet": str,
        "house": int,
        "location": int
    }
}
```

- Изначально знает только себя
- Обновляется при встречах с владельцами домов
- Обновляется при обменах питомцами (все присутствующие узнают новые питомцы участников)
- Обновляется при обменах домами (все присутствующие узнают новые дома участников)


### StartTrip
`event_number;time;StartTrip;nationality;from_house;to_house`

### FinishTrip
- Домой: `event_number;time;FinishTrip;nationality;house`
- Не домой: `event_number;time;FinishTrip;success;nationality;house`
  - `success`: 1 (встретил владельца), 0 (не встретил)

### ChangePet
`event_number;time;ChangePet;qty_participants;nat1;nat2;[nat3];pet1;pet2;[pet3]`

### ChangeHouse
`event_number;time;changeHouse;qty_participants;nat1;nat2;[nat3];house1;house2;[house3]`


## Пример и анализ лога

АНАЛИЗ ЛОГА   1;0;StartTrip;Russian;1;6
2;0;StartTrip;Chinese;3;5
3;0;StartTrip;American;6;1
4;0;StartTrip;French;5;6
5;0;StartTrip;English;2;1
6;0;StartTrip;German;4;1
7;1;FinishTrip;0;Russian;6
8;1;StartTrip;Russian;6;1
9;2;FinishTrip;0;American;3
10;2;FinishTrip;0;German;1
11;2;FinishTrip;0;Chinese;5
12;2;StartTrip;German;1;4
13;4;FinishTrip;German;4
14;4;StartTrip;German;4;1
15;5;FinishTrip;Russian;1
16;5;FinishTrip;1;English;1
17;5;FinishTrip;0;French;6
18;5;StartTrip;Russian;1;5
19;5;StartTrip;English;1;2
20;5;StartTrip;French;6;5
21;6;FinishTrip;0;German;1
22;6;StartTrip;German;1;4
23;8;FinishTrip;0;Russian;5
24;8;FinishTrip;1;French;5
25;8;FinishTrip;German;4
26;8;ChangePet;2;Russian;Chinese;Zebra;Dog
27;8;changeHouse;3;Russian;Chinese;French;3;5;1
28;8;StartTrip;German;4;1
29;10;FinishTrip;0;German;1
30;10;ChangePet;2;Russian;French;Humpster;Zebra
31;10;StartTrip;German;1;4
32;11;FinishTrip;English;2
33;11;StartTrip;English;2;1
---- KNOWLEDGE ----
1;{1: {'pet': 'Humpster', 'house': 3, 'location': 5, 't': 10}, 2: {'pet': 'Cat', 'house': 2, 'location': 1, 't': 5}, 5: {'pet': 'Zebra', 'house': 1, 'location': 5, 't': 10}, 3: {'pet': 'Dog', 'house': 5, 'location': 5, 't': 8}}
2;{2: {'pet': 'Cat', 'house': 2, 'location': 2, 't': 0}, 1: {'pet': 'Dog', 'house': 1, 'location': 1, 't': 5}}
3;{3: {'pet': 'Dog', 'house': 5, 'location': 5, 't': 8}, 5: {'pet': 'Zebra', 'house': 1, 'location': 5, 't': 10}, 1: {'pet': 'Humpster', 'house': 3, 'location': 5, 't': 10}}
4;{4: {'pet': 'Fish', 'house': 4, 'location': 4, 't': 0}, 1: {'pet': 'Dog', 'house': 1, 'location': 1, 't': 10}}
5;{5: {'pet': 'Zebra', 'house': 1, 'location': 5, 't': 10}, 1: {'pet': 'Humpster', 'house': 3, 'location': 5, 't': 10}, 3: {'pet': 'Dog', 'house': 5, 'location': 5, 't': 8}}
6;{6: {'pet': 'Bear', 'house': 6, 'location': 6, 't': 0}}

* Russian (дом 1 → после обмена дом 3):
* 1;0;StartTrip;Russian;1;6 (начало).
* 15;5;FinishTrip;Russian;1 (вернулся домой).
* 18;5;StartTrip;Russian;1;5 (новая поездка).
* 23;8;FinishTrip;0;Russian;5 (прибыл в 5, success=0).
* 27;8;changeHouse;3;Russian;Chinese;French;3;5;1 (обмен: Russian получает дом 3).
* После обмена: location=5, house=3 → планирует поездку в 3 (но лог обрывается).
* Знания: знает house=3 (себя), house=1 (French), house=5 (Chinese).

* English (дом 2):
* 5;0;StartTrip;English;2;1 (начало).
* 16;5;FinishTrip;1;English;1 (прибыл в 1, success=1, встретил Russian).
* 19;5;StartTrip;English;1;2 (новая).
* 32;11;FinishTrip;English;2 (вернулся домой).

* Chinese (дом 3 → после обмена дом 5):
* 2;0;StartTrip;Chinese;3;5 (начало).
* 11;2;FinishTrip;0;Chinese;5 (прибыл в 5).
* 27;8;changeHouse;3;Russian;Chinese;French;3;5;1 (обмен: Chinese получает дом 5).
* Знания: знает house=5 (себя), house=1 (French), house=3 (Russian).

* German (дом 4):
* 6;0;StartTrip;German;4;1 (начало).
* 10;2;FinishTrip;0;German;1 (прибыл в 1).
* 12;2;StartTrip;German;1;4 (возвращение).
* 13;4;FinishTrip;German;4 (вернулся домой).
* 14;4;StartTrip;German;4;1 (новая).
* 21;6;FinishTrip;0;German;1 (прибыл в 1).
* 22;6;StartTrip;German;1;4 (возвращение).
* 25;8;FinishTrip;German;4 (вернулся домой).
* 28;8;StartTrip;German;4;1 (новая).
* 29;10;FinishTrip;0;German;1 (прибыл в 1).
* 31;10;StartTrip;German;1;4 (возвращение).

* French (дом 5 → после обмена дом 1):
* 4;0;StartTrip;French;5;6 (начало).
* 17;5;FinishTrip;0;French;6 (прибыл в 6).
* 20;5;StartTrip;French;6;5 (возвращение).
* 24;8;FinishTrip;1;French;5 (прибыл в 5, success=1).
* 27;8;changeHouse;3;Russian;Chinese;French;3;5;1 (обмен: French получает дом 1).
* Знания: знает house=1 (себя), house=3 (Russian), house=5 (Chinese).

* American (дом 6):
* 3;0;StartTrip;American;6;1 (начало).
* 9;2;FinishTrip;0;American;3 (прибыл в 3).

## Детали реализации

### Приоритеты событий
- `EVENT_PRIORITY_FINISH_TRIP = 1`
- `EVENT_PRIORITY_EXCHANGE = 2`
- `EVENT_PRIORITY_START_TRIP = 3`

### Обработка батчей
События на одном времени обрабатываются в порядке приоритетов для корректного моделирования последовательности.

### Генерация обменов питомцами
- Только после `FinishTrip` событий
- Для каждого дома отдельно
- **Случайный выбор участников:**
  - Для каждого агента в доме генерируется случайное число от 1 до 100
  - Если число ≤ `pet_exchange_prob` агента, он добавляется в список готовых к обмену
  - Минимум 2 участника для обмена, максимум 3 (берутся первые 3 из отсортированного списка)
- Циклический сдвиг питомцев: A→B→C→A (где A, B, C - участники)

### Генерация обменов домами
- Только после успешных `FinishTrip` событий (success=1) в дом прибытия
- Для дома прибытия с ≥2 агентами и владельцем дома
- **Случайный выбор участников:**
  - Для каждого агента в доме генерируется случайное число от 1 до 100
  - Если число ≤ `house_exchange_prob` агента, он добавляется в список готовых к обмену
  - Минимум 2 участника для обмена
- Циклический сдвиг домов: A→B→C→A (где A, B, C - участники)
- После обмена планируются поездки участников в новые дома, если location != house_id

### Выбор маршрутов
- Исключение текущей локации
- Взвешенный случайный выбор по `route_probs`
- При нулевых весах: равномерный случайный выбор

