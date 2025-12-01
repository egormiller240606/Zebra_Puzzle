import numpy as np
import matplotlib.pyplot as plt

class SimulationAnalyzer:
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self.events_data = None
        self.knowledge_data = None
        self.load_data()

    def load_data(self):
        """Загружает и парсит лог-файл симуляции"""
        events = []
        knowledge_section = False
        knowledge_data = []

        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                if line == "---- KNOWLEDGE ----":
                    knowledge_section = True
                    continue

                if knowledge_section:
                    if ';' in line:
                        agent_id, knowledge_str = line.split(';', 1)
                        knowledge_data.append({
                            'agent_id': int(agent_id),
                            'knowledge': knowledge_str
                        })
                else:
                    if line and ';' in line:
                        parts = line.split(';')
                        if len(parts) >= 3:
                            event_data = {
                                'event_number': int(parts[0]),
                                'time': int(parts[1]),
                                'event_type': parts[2]
                            }

                            # Парсинг специфичных данных для каждого типа события
                            if event_data['event_type'] == 'StartTrip':
                                event_data.update({
                                    'nationality': parts[3],
                                    'from_house': int(parts[4]),
                                    'to_house': int(parts[5])
                                })
                            elif event_data['event_type'] == 'FinishTrip':
                                if len(parts) == 6:  # Поездка с результатом (успех/неуспех)
                                    event_data.update({
                                        'success': int(parts[3]),
                                        'nationality': parts[4],
                                        'house_id': int(parts[5])
                                    })
                                else:  # Возвращение домой
                                    event_data.update({
                                        'nationality': parts[3],
                                        'house_id': int(parts[4])
                                    })
                            elif event_data['event_type'] == 'changeHouse':
                                event_data.update({
                                    'qty_participants': int(parts[3]),
                                    'nationalities': parts[4:4+int(parts[3])],
                                    'houses_after': [int(x) for x in parts[4+int(parts[3]):]]
                                })
                            elif event_data['event_type'] == 'ChangePet':
                                event_data.update({
                                    'qty_participants': int(parts[3]),
                                    'nationalities': parts[4:4+int(parts[3])],
                                    'pets_after': parts[4+int(parts[3]):]
                                })

                            events.append(event_data)

        self.events_data = events
        self.knowledge_data = knowledge_data
    
    
    def plot_cumulative_events_by_type(self):
        """Создает график нарастающего итога количества событий по типам"""
        plt.figure(figsize=(14, 8))

        event_types = ['StartTrip', 'changeHouse', 'ChangePet']
        colors = ['purple', 'darkblue', 'darkred']
        labels = ['Start Trips', 'House Exchanges', 'Pet Exchanges']

        times = np.array([event['time'] for event in self.events_data])
        time_range = range(int(np.min(times)), int(np.max(times)) + 1)

        line_styles = ['-', '-', '-']

        for i, (event_type, color, label) in enumerate(zip(event_types, colors, labels)):
            cumulative = []
            current_sum = 0

            for t in time_range:
                # Считаем события этого типа в данный момент времени
                count_at_time = sum(1 for event in self.events_data
                                   if event['event_type'] == event_type and event['time'] == t)
                current_sum += count_at_time
                cumulative.append(current_sum)

            plt.step(time_range, cumulative, color=color, linewidth=1, linestyle=line_styles[i],
                    where='post', label=label, alpha=1.0)

        # Общий кумулятивный итог всех событий - используем полный временной диапазон
        total_cumulative = []
        current_total = 0

        for t in time_range:
            # Считаем все события в данный момент времени
            count_at_time = sum(1 for event in self.events_data if event['time'] == t)
            current_total += count_at_time
            total_cumulative.append(current_total)

        plt.step(time_range, total_cumulative, color='darkgreen', linewidth=1,
                linestyle='-', where='post', label='All Events', alpha=1.0)

        plt.xlabel('Time', fontsize=14)
        plt.ylabel('Cumulative Number of Events', fontsize=14)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=12)
        plt.grid(True, alpha=0.3)

        # Для больших временных диапазонов показываем только точки с событиями
        unique_times = sorted(list(set(times)))
        if len(unique_times) <= 20:  # Если мало уникальных времен, показываем все
            plt.xticks(unique_times)
        else:  # Если много времен, показываем каждое 5-е или адаптивно
            step = max(1, len(unique_times) // 10)
            plt.xticks(unique_times[::step])

        plt.xlim(left=0)
        plt.ylim(bottom=0)
        plt.tight_layout()
        plt.savefig('data/cumulative_events_gpaph.png', dpi=300, bbox_inches='tight')
    
    def create_summary_report(self):
        """Создает сводный отчет по симуляции"""
        print()
        print("=" * 50)
        print("СВОДНЫЙ ОТЧЕТ ПО СИМУЛЯЦИИ")
        print("=" * 50)
        print()

        print(f"Общее количество событий: {len(self.events_data)}")

        # Получаем временной диапазон
        times = np.array([event['time'] for event in self.events_data])
        print(f"Временной диапазон: от {int(np.min(times))} до {int(np.max(times))}")

        print("\nРаспределение по типам событий:")
        event_types = [event['event_type'] for event in self.events_data]
        unique_types, counts = np.unique(event_types, return_counts=True)
        for event_type, count in zip(unique_types, counts):
            percentage = count / len(self.events_data) * 100
            print(f"  {event_type}: {count} событий ({percentage:.1f}%)")

        start_trips = [event for event in self.events_data if event['event_type'] == 'StartTrip']
        finish_trips = [event for event in self.events_data if event['event_type'] == 'FinishTrip']

        if start_trips:
            print(f"\nАнализ поездок:")
            print(f"  Начато поездок: {len(start_trips)}")
            print(f"  Завершено поездок: {len(finish_trips)}")

            successful_trips = [event for event in finish_trips if 'success' in event]
            successful_count = sum(event['success'] for event in successful_trips)
            total_with_success = len(successful_trips)

            if total_with_success > 0:
                success_rate = successful_count / total_with_success * 100
                print(f"  Успешных поездок: {successful_count} ({success_rate:.1f}%)")
                print(f"  Поездок с результатом (успех/неуспех): {total_with_success}")

        exchanges = [event for event in self.events_data if event['event_type'] in ['changeHouse', 'ChangePet']]
        if exchanges:
            print(f"\nАнализ обменов:")
            house_exchanges = [event for event in exchanges if event['event_type'] == 'changeHouse']
            pet_exchanges = [event for event in exchanges if event['event_type'] == 'ChangePet']
            print(f"  Обменов домами: {len(house_exchanges)}")
            print(f"  Обменов питомцами: {len(pet_exchanges)}")

            if exchanges and 'qty_participants' in exchanges[0]:
                participants = [event['qty_participants'] for event in exchanges if 'qty_participants' in event]
                if participants:
                    avg_participants = np.mean(participants)
                    print(f"  Среднее количество участников в обменах: {avg_participants:.1f}")
    
    def analyze_knowledge_evolution(self):
        """Анализирует эволюцию знаний агентов (если данные доступны)"""
        if self.knowledge_data:
            print("\nЗнания агентов:")            
            print()

            total_known_others = 0
            total_knowledge_entries = 0
            agents_knowing_self = 0

            for knowledge_entry in self.knowledge_data:
                agent_id = knowledge_entry['agent_id']
                knowledge_str = knowledge_entry['knowledge']

                try:
                    knowledge_dict = eval(knowledge_str)

                    knows_self = agent_id in knowledge_dict
                    if knows_self:
                        agents_knowing_self += 1
                        self_info = knowledge_dict[agent_id]
                        if isinstance(self_info, dict):
                            pet = self_info.get('pet', 'unknown')
                            house = self_info.get('house', 'unknown')
                            location = self_info.get('location', 'unknown')
                            timestamp = self_info.get('t', 'unknown')
                            other_known = [(k, v) for k, v in knowledge_dict.items() if k != agent_id]
                            suffix = "\nДругие известные островитяне:" if other_known else ""
                            print(f"Агент {agent_id} знает о себе: pet={pet}, house={house}, location={location}, t={timestamp}{suffix}")

                    # Считаем сколько других агентов знает этот агент
                    known_others = len(knowledge_dict) - (1 if knows_self else 0)
                    total_known_others += known_others
                    total_knowledge_entries += sum(len(info) for info in knowledge_dict.values()
                                                  if isinstance(info, dict))

                
                    # Показываем детали для всех известных агентов (исключая себя)
                    for known_agent_id, info in other_known:
                        if isinstance(info, dict):
                            pet = info.get('pet', 'unknown')
                            house = info.get('house', 'unknown')
                            location = info.get('location', 'unknown')
                            timestamp = info.get('t', 'unknown')
                            print(f"  Агент {known_agent_id}: pet={pet}, house={house}, location={location}, t={timestamp}")

                except (SyntaxError, ValueError) as e:
                    print(f"Агент {agent_id}: ошибка парсинга знаний - {e}")

            # Общая статистика
            if self.knowledge_data:
                avg_known_others = total_known_others / len(self.knowledge_data)
                print(f"\nСреднее количество известных других агентов на агента: {avg_known_others:.1f}")
                print()
    def run_complete_analysis(self):
        """Запускает полный анализ и создает график нарастающего итога"""
        
        # Создаем отчет
        self.create_summary_report()

        # Создаем только график нарастающего итога
        self.plot_cumulative_events_by_type()

        # Анализ знаний
        self.analyze_knowledge_evolution()


# Основная функция для запуска анализа
def main():
    log_file_path = "data/simulation_log.csv"  # Укажите путь к вашему лог-файлу
    
    try:
        # Создаем анализатор
        analyzer = SimulationAnalyzer(log_file_path)
        
        # Запускаем полный анализ
        analyzer.run_complete_analysis()
        
    except FileNotFoundError:
        print(f"Файл {log_file_path} не найден!")
    except Exception as e:
        print(f"Произошла ошибка при анализе: {e}")

if __name__ == "__main__":
    main()
