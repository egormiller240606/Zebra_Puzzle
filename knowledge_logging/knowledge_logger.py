import os
import csv
from collections import defaultdict
from typing import Dict, List, Any, Tuple, Optional

class KnowledgeLogAnalyzer:
    def __init__(self, observer_log_path: str, agents_csv_path: str, output_dir: str = "data/output_data/logs"):
        self.observer_log_path = observer_log_path
        self.agents_csv_path = agents_csv_path
        self.output_dir = output_dir

        os.makedirs(self.output_dir, exist_ok=True)

        self.agents_metadata = self._load_agents_metadata()
        self.agents_knowledge: Dict[int, Dict[int, Dict[str, Any]]] = {}
        self._initialize_knowledge_states()
        self.previous_knowledge_states: Dict[int, Dict[int, Dict[str, Any]]] = {}
        for agent_id in self.agents_metadata.keys():
            self.previous_knowledge_states[agent_id] = {}
        self.events_by_time = self._parse_observer_log()

    def _load_agents_metadata(self) -> Dict[int, Dict[str, str]]:
        metadata = {}
        try:
            with open(self.agents_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                for row in reader:
                    if len(row) < 6:
                        continue
                    agent_id = int(row[0])
                    metadata[agent_id] = {
                        'color': row[1],
                        'nationality': row[2],
                        'drink': row[3],
                        'cigarettes': row[4],
                        'pet': row[5]
                    }
        except Exception:
            pass
        return metadata

    def _initialize_knowledge_states(self) -> None:
        for agent_id, metadata in self.agents_metadata.items():
            self.agents_knowledge[agent_id] = {
                agent_id: {
                    'pet': metadata['pet'],
                    'house': agent_id,
                    'location': agent_id,
                    't': 0
                }
            }

    def _parse_observer_log(self) -> Dict[int, List[Dict[str, Any]]]:
        events_by_time = defaultdict(list)
        try:
            with open(self.observer_log_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                next(reader, None)
                for row in reader:
                    if not row or len(row) < 3:
                        continue
                    try:
                        event_num = int(row[0])
                        time = int(row[1])
                        event_type = row[2].strip()

                        event_data = {
                            'event_num': event_num,
                            'time': time,
                            'event_type': event_type,
                        }

                        if event_type == 'StartTrip':
                            if len(row) >= 6:
                                event_data.update({
                                    'nationality': row[3],
                                    'from_house': int(row[4]),
                                    'to_house': int(row[5])
                                })
                        elif event_type == 'FinishTrip':
                            if len(row) == 6:
                                event_data.update({
                                    'success': int(row[3]),
                                    'nationality': row[4],
                                    'house_id': int(row[5])
                                })
                            elif len(row) >= 5:
                                event_data.update({
                                    'nationality': row[3],
                                    'house_id': int(row[4]),
                                    'success': 1
                                })
                        elif event_type in ['changeHouse', 'ChangePet']:
                            if len(row) >= 4:
                                try:
                                    qty_participants = int(row[3])
                                    event_data['qty_participants'] = qty_participants
                                    event_data['nationalities'] = row[4:4 + qty_participants]
                                    if event_type == 'changeHouse' and len(
                                            row) >= 4 + qty_participants + qty_participants:
                                        event_data['houses_after'] = [int(x) for x in row[4 + qty_participants:4 + qty_participants + qty_participants]]
                                    elif event_type == 'ChangePet' and len(
                                            row) >= 4 + qty_participants + qty_participants:
                                        event_data['pets_after'] = row[4 + qty_participants:4 + qty_participants + qty_participants]
                                except (ValueError, IndexError):
                                    pass

                        events_by_time[time].append(event_data)
                    except (ValueError, IndexError):
                        continue

            return events_by_time
        except Exception:
            return {}

    def _get_agent_id_by_nationality(self, nationality: str) -> Optional[int]:
        nationality_clean = nationality.strip().lower()
        for agent_id, meta in self.agents_metadata.items():
            if meta['nationality'].strip().lower() == nationality_clean:
                return agent_id
        return None

    def _knowledge_changed(self, agent_id: int, current_knowledge: Dict[int, Dict[str, Any]]) -> bool:
        previous_knowledge = self.previous_knowledge_states.get(agent_id, {})
        if not previous_knowledge:
            return True
        if len(previous_knowledge) != len(current_knowledge):
            return True
        for other_agent_id, info in current_knowledge.items():
            if other_agent_id not in previous_knowledge:
                return True
            prev_info = previous_knowledge[other_agent_id]
            fields_to_compare = ['pet', 'house', 'location']
            for field in fields_to_compare:
                current_value = info.get(field)
                prev_value = prev_info.get(field)
                if current_value != prev_value:
                    return True

        return False

    def _process_finish_trips(self, events: List[Dict[str, Any]], time: int) -> None:
        houses_occupants = defaultdict(list)
        for event in events:
            if event['event_type'] == 'FinishTrip' and 'house_id' in event:
                agent_id = self._get_agent_id_by_nationality(event['nationality'])
                success = event.get('success', 1)
                if agent_id:
                    if agent_id in self.agents_knowledge[agent_id]:
                        self.agents_knowledge[agent_id][agent_id]['location'] = event['house_id']
                        self.agents_knowledge[agent_id][agent_id]['t'] = time
                    if success == 1:
                        houses_occupants[event['house_id']].append(agent_id)
        for house_id, occupants in houses_occupants.items():
            if len(occupants) > 1:
                for i, agent1_id in enumerate(occupants):
                    for agent2_id in occupants[i + 1:]:
                        if agent1_id in self.agents_knowledge and agent2_id in self.agents_knowledge:
                            if agent2_id not in self.agents_knowledge[agent1_id]:
                                self.agents_knowledge[agent1_id][agent2_id] = {}
                            if agent2_id in self.agents_knowledge[agent2_id]:
                                self.agents_knowledge[agent1_id][agent2_id].update({
                                    'pet': self.agents_knowledge[agent2_id][agent2_id]['pet'],
                                    'house': self.agents_knowledge[agent2_id][agent2_id]['house'],
                                    'location': self.agents_knowledge[agent2_id][agent2_id]['location'],
                                    't': time
                                })
                            if agent1_id not in self.agents_knowledge[agent2_id]:
                                self.agents_knowledge[agent2_id][agent1_id] = {}
                            if agent1_id in self.agents_knowledge[agent1_id]:
                                self.agents_knowledge[agent2_id][agent1_id].update({
                                    'pet': self.agents_knowledge[agent1_id][agent1_id]['pet'],
                                    'house': self.agents_knowledge[agent1_id][agent1_id]['house'],
                                    'location': self.agents_knowledge[agent1_id][agent1_id]['location'],
                                    't': time
                                })

    def _find_witnesses_for_exchange(self, participants: List[int], time: int) -> List[int]:
        witnesses = []
        participant_locations = set()
        for participant_id in participants:
            if participant_id in self.agents_knowledge[participant_id]:
                location = self.agents_knowledge[participant_id][participant_id]['location']
                participant_locations.add(location)
        for agent_id in self.agents_knowledge:
            if agent_id in participants:
                continue
            if agent_id in self.agents_knowledge[agent_id]:
                agent_location = self.agents_knowledge[agent_id][agent_id]['location']
                if agent_location in participant_locations:
                    witnesses.append(agent_id)

        return witnesses

    def _update_witnesses_knowledge(self, participants: List[int], time: int) -> None:
        witnesses = self._find_witnesses_for_exchange(participants, time)
        for witness_id in witnesses:
            for participant_id in participants:
                if participant_id not in self.agents_knowledge[witness_id]:
                    self.agents_knowledge[witness_id][participant_id] = {}
                if participant_id in self.agents_knowledge[participant_id]:
                    participant_info = self.agents_knowledge[participant_id][participant_id]
                    self.agents_knowledge[witness_id][participant_id].update({
                        'pet': participant_info['pet'],
                        'house': participant_info['house'],
                        'location': participant_info['location'],
                        't': time
                    })

    def _process_change_events(self, events: List[Dict[str, Any]], time: int) -> None:
        for event in events:
            participants = []
            for nationality in event.get('nationalities', []):
                agent_id = self._get_agent_id_by_nationality(nationality)
                if agent_id:
                    participants.append(agent_id)

            if event['event_type'] == 'changeHouse' and 'houses_after' in event:
                self._process_house_exchange(event, time)
            elif event['event_type'] == 'ChangePet' and 'pets_after' in event:
                self._process_pet_exchange(event, time)
            if participants:
                self._update_witnesses_knowledge(participants, time)

    def _process_house_exchange(self, event: Dict[str, Any], time: int) -> None:
        participants = []
        for nationality in event['nationalities']:
            agent_id = self._get_agent_id_by_nationality(nationality)
            if agent_id:
                participants.append(agent_id)

        if not participants or len(participants) != len(event.get('houses_after', [])):
            return

        for i, agent_id in enumerate(participants):
            if agent_id in self.agents_knowledge and agent_id in self.agents_knowledge[agent_id]:
                new_house_id = event['houses_after'][i]
                self.agents_knowledge[agent_id][agent_id]['house'] = new_house_id
                self.agents_knowledge[agent_id][agent_id]['t'] = time

    def _process_pet_exchange(self, event: Dict[str, Any], time: int) -> None:
        participants = []
        for nationality in event['nationalities']:
            agent_id = self._get_agent_id_by_nationality(nationality)
            if agent_id:
                participants.append(agent_id)

        if not participants or len(participants) != event['qty_participants'] or len(participants) != len(
                event.get('pets_after', [])):
            return
        for i, agent_id in enumerate(participants):
            if agent_id in self.agents_knowledge and agent_id in self.agents_knowledge[agent_id]:
                new_pet = event['pets_after'][i]
                self.agents_knowledge[agent_id][agent_id]['pet'] = new_pet
                self.agents_knowledge[agent_id][agent_id]['t'] = time

    def _log_knowledge_state(self, time: int, event_type: str) -> None:
        for agent_id, knowledge in self.agents_knowledge.items():
            if self._knowledge_changed(agent_id, knowledge):
                nationality = self.agents_metadata[agent_id]['nationality']
                filename = os.path.join(self.output_dir, f"agent_{agent_id}_{nationality}_knowledge.log")
                knowledge_str = str(knowledge).replace('\n', ' ').replace('\r', '')
                with open(filename, 'a', encoding='utf-8') as f:
                    f.write(f"{time};{event_type};{knowledge_str}\n")
                self.previous_knowledge_states[agent_id] = {
                    k: {sub_k: sub_v for sub_k, sub_v in v.items()} if isinstance(v, dict) else v
                    for k, v in knowledge.items()
                }

    def generate_knowledge_logs(self) -> None:
        for agent_id in self.agents_knowledge:
            nationality = self.agents_metadata[agent_id]['nationality']
            filename = os.path.join(self.output_dir, f"agent_{agent_id}_{nationality}_knowledge.log")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(
                    f"0;INIT;{{{agent_id}: {{'pet': '{self.agents_metadata[agent_id]['pet']}', 'house': {agent_id}, 'location': {agent_id}, 't': 0}}}}\n")
            self.previous_knowledge_states[agent_id] = {
                k: {sub_k: sub_v for sub_k, sub_v in v.items()} if isinstance(v, dict) else v
                for k, v in self.agents_knowledge[agent_id].items()
            }
        sorted_times = sorted(self.events_by_time.keys())
        for t in sorted_times:
            batch = self.events_by_time[t]
            finish_trips = [e for e in batch if e['event_type'] == 'FinishTrip']
            change_house_events = [e for e in batch if e['event_type'] == 'changeHouse']
            change_pet_events = [e for e in batch if e['event_type'] == 'ChangePet']
            if finish_trips:
                self._process_finish_trips(finish_trips, t)
                self._log_knowledge_state(t, "FinishTrip")
            if change_house_events:
                self._process_change_events(change_house_events, t)
                self._log_knowledge_state(t, "ChangeHouse")
            if change_pet_events:
                self._process_change_events(change_pet_events, t)
                self._log_knowledge_state(t, "ChangePet")