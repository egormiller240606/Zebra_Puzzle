from typing import TYPE_CHECKING, Tuple, Optional, List, Any

if TYPE_CHECKING:
    from simulation.environment import Environment


# Constants for event priorities in simulation
EVENT_PRIORITY_FINISH_TRIP = 1
EVENT_PRIORITY_EXCHANGE = 2
EVENT_PRIORITY_START_TRIP = 3


class Event:
    def __init__(self, time: int, agent_id: Optional[int] = None):
        self.time = time
        self.agent_id = agent_id

    def run(self, env: 'Environment') -> Tuple[List[int], List[int]]:
        return ([self.agent_id] if self.agent_id is not None else [], [])

    def __lt__(self, other: 'Event') -> bool:
        return self.time < other.time

