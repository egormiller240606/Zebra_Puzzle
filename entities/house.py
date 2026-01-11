class House:
    def __init__(self, house_id: int, color: str, owner_id: int):
        self.id = house_id
        self.color = color
        self.owner_id = owner_id
        self.present_agents = set()

    def enter(self, agent_id: int) -> None:
        self.present_agents.add(agent_id)

    def leave(self, agent_id: int) -> None:
        self.present_agents.discard(agent_id)

    def set_owner(self, new_owner_id: int) -> None:
        self.owner_id = new_owner_id

    def is_owner_home(self) -> bool:
        return self.owner_id in self.present_agents

    def __repr__(self) -> str:
        return (f"House(id={self.id}, color={self.color}, "
                f"owner={self.owner_id}, present={list(self.present_agents)})")

