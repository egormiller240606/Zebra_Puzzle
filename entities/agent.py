from typing import Dict, Any


class Agent:
    def __init__(self, agent_id: int, nationality: str, drink: str, cigarettes: str, pet: str,
                 house_id: int, route_probs: Dict[int, int], house_exchange_prob: int, pet_exchange_prob: int):
        self.id = agent_id
        self.nationality = nationality
        self.drink = drink
        self.cigarettes = cigarettes
        self.pet = pet

        self.house_id = house_id
        self.location = house_id
        self.is_travelling = False

        self.route_probs = route_probs
        self.house_exchange_prob = house_exchange_prob
        self.pet_exchange_prob = pet_exchange_prob
        self.last_update_time = 0

        self.knowledge = {
            self.id: {
                # "nationality": self.nationality,
                # "drink": self.drink,
                # "cigarettes": self.cigarettes,
                "pet": self.pet,
                "house": self.house_id,
                "location": self.location,
                "t": 0
            }
        }

    def _get_agent_info(self) -> Dict[str, Any]:
        return {
            # "nationality": self.nationality,
            # "drink": self.drink,
            # "cigarettes": self.cigarettes,
            "pet": self.pet,
            "house": self.house_id,
            "location": self.location
        }

    def update_knowledge(self, other_agent: 'Agent', time: int) -> None:
        self.knowledge[other_agent.id] = {**other_agent._get_agent_info(), "t": time}

    def choose_trip_target(self, travel_matrix, houses, color_to_prob_index):
        import random
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

    def __repr__(self) -> str:
        loc = self.location if self.location == self.house_id else f"travel→{self.location}"
        return (f"Agent(id={self.id}, nat={self.nationality}, "
                f"drink={self.drink}, cig={self.cigarettes}, pet={self.pet}, "
                f"home={self.house_id}, loc={loc})")

