import heapq
from typing import Dict, List, Optional, Any, Tuple

from loaders.csv_utils import build_color_to_prob_index
from events.base import Event
from events.trip import FinishTripEvent, StartTripEvent
from events.exchange import ChangePetEvent, ChangeHouseEvent


class Environment:
    def __init__(self, agents: Dict[int, 'Agent'], houses: Dict[int, 'House'], travel_matrix: List[List[Optional[int]]], max_time: int):
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
        from events.base import EVENT_PRIORITY_EXCHANGE

        exchange_events = []

        for house_id, house in self.houses.items():
            # Only allow pet exchanges when owner is present (same as house exchanges)
            if not house.is_owner_home():
                continue

            present_agents = sorted(list(house.present_agents))
            if len(present_agents) < 2:
                continue

            ready_participants = []
            for agent_id in present_agents:
                agent = self.agents[agent_id]
                if __import__('random').randint(1, 100) <= agent.pet_exchange_prob:
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
        from events.base import EVENT_PRIORITY_FINISH_TRIP, EVENT_PRIORITY_EXCHANGE, EVENT_PRIORITY_START_TRIP

        def event_priority(e: Event) -> Tuple[int, bool]:
            if isinstance(e, FinishTripEvent):
                # Хозяева (возвращающиеся домой) обрабатываются раньше туристов
                # is_return_home=True -> (0, True) - обрабатывается первым
                # is_return_home=False -> (0, False) - обрабатывается вторым
                return (EVENT_PRIORITY_FINISH_TRIP, not e.is_return_home)
            elif hasattr(e, 'participant_ids'):
                return (EVENT_PRIORITY_EXCHANGE, False)
            else:
                return (EVENT_PRIORITY_START_TRIP, False)

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
        from loaders.csv_utils import log_formatter

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
                continue
            if agent.location == agent.house_id:
                new_target = agent.choose_trip_target(self.travel_matrix, self.houses, self.color_to_prob_index)
                if new_target is not None:
                    travel_time = self.travel_matrix[agent.location][new_target]
                    if travel_time is not None and travel_time >= 0:
                        start_time = self.time
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
        from events.base import EVENT_PRIORITY_FINISH_TRIP, EVENT_PRIORITY_EXCHANGE, EVENT_PRIORITY_START_TRIP

        event_counter = 1
        csv_log = []

        while self.event_queue and self.time <= max_time:
            t = self.event_queue[0].time
            self.time = t

            while self.event_queue and self.event_queue[0].time == self.time:
                batch = []
                while self.event_queue and self.event_queue[0].time == self.time:
                    batch.append(heapq.heappop(self.event_queue))

                if not batch:
                    break

                batch.sort(key=lambda e: (EVENT_PRIORITY_FINISH_TRIP,
                                          not e.is_return_home if isinstance(e, FinishTripEvent) else False) if isinstance(e, FinishTripEvent) else
                                          (EVENT_PRIORITY_EXCHANGE, False) if hasattr(e, 'participant_ids') else
                                          (EVENT_PRIORITY_START_TRIP, False))

                finish_events, start_events, other_events, exchange_events = self._process_batch_events(batch)
                event_counter = self._log_events(finish_events, exchange_events, self.house_exchange_events, start_events, event_counter, csv_log)
                self.house_exchange_events.clear()

                self._plan_new_trips(finish_events)

        return csv_log

