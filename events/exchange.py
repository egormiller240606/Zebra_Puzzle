from typing import TYPE_CHECKING, Tuple, Optional, List, Any

from .base import Event

if TYPE_CHECKING:
    from simulation.environment import Environment


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

        if not house.is_owner_home():
            return [], []

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
        for witness_id in list(house.present_agents):
            witness = env.agents[witness_id]
            for participant_id in self.participant_ids:
                witness.update_knowledge(env.agents[participant_id], self.time)

        return self.participant_ids, []

    def get_log_data(self, env: 'Environment') -> Tuple[str, List[Any]]:
        nationalities = [env.agents[agent_id].nationality for agent_id in self.participant_ids]
        extra = [self.qty_participants] + nationalities + list(map(str, self.houses_after_exchange))
        return "changeHouse", extra


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

        if not house.is_owner_home():
            return [], []

        for agent_id, new_pet in zip(self.participant_ids, self.pets_after_exchange):
            agent = env.agents[agent_id]
            agent.pet = new_pet
            agent.knowledge[agent_id] = {**agent._get_agent_info(), "t": self.time}
            agent.last_update_time = self.time

        for witness_id in list(house.present_agents):
            witness = env.agents[witness_id]
            for participant_id in self.participant_ids:
                witness.update_knowledge(env.agents[participant_id], self.time)

        return self.participant_ids, []

    def get_log_data(self, env: 'Environment') -> Tuple[str, List[Any]]:
        nationalities = [env.agents[agent_id].nationality for agent_id in self.participant_ids]
        extra = [self.qty_participants] + nationalities + self.pets_after_exchange
        return "ChangePet", extra

