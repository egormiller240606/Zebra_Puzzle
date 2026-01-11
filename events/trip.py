import random
from typing import TYPE_CHECKING, Tuple, Optional, List, Any

from .base import Event, EVENT_PRIORITY_FINISH_TRIP, EVENT_PRIORITY_EXCHANGE, EVENT_PRIORITY_START_TRIP

if TYPE_CHECKING:
    from simulation.environment import Environment
    from entities.house import House


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
        if travel_time is None or travel_time < 0:
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

                    # Log knowledge changes
                    env.agent_knowledge_logger.log_knowledge_change(
                        time=self.time,
                        agent_id=agent.id,
                        event_type="FinishTrip",
                        knowledge_after=agent.knowledge.copy()
                    )
                    env.agent_knowledge_logger.log_knowledge_change(
                        time=self.time,
                        agent_id=other_id,
                        event_type="FinishTrip",
                        knowledge_after=other_agent.knowledge.copy()
                    )

            # Detect and execute house exchange
            house_exchange_event = self.detect_house_exchange(env, house)
            if house_exchange_event:
                house_exchange_event.run(env)
                env.house_exchange_events.append(house_exchange_event)

        return [agent.id], [self.target_house]

    def detect_house_exchange(self, env: 'Environment', house: 'House') -> Optional['ChangeHouseEvent']:
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


# Import ChangeHouseEvent at the end to avoid circular import
from .exchange import ChangeHouseEvent

