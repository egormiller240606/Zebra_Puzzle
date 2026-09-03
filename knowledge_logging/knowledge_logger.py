import os
import csv
from collections import defaultdict
from typing import Dict, List, Set, Optional, Any, Tuple


class KnowledgeLogAnalyzer:

    def __init__(
        self,
        observer_log_path: str,
        agents_csv_path: str,
        output_dir: str = "data/output_data/logs"
    ):
        self.observer_log_path = observer_log_path
        self.agents_csv_path = agents_csv_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.agents_meta: Dict[int, Dict[str, str]] = self._load_agents_metadata()
        self._nat_to_id: Dict[str, int] = {
            m["nationality"].strip().lower(): aid
            for aid, m in self.agents_meta.items()
        }

        self.location: Dict[int, Optional[int]] = {}  
        self.agent_house: Dict[int, int] = {}          
        self.pet: Dict[int, str] = {}                   
        self.owner_of: Dict[int, int] = {}             

        self.knowledge: Dict[int, Dict[int, Dict[str, Any]]] = {}
        self._prev: Dict[int, Dict[int, Dict[str, Any]]] = {}


    def _load_agents_metadata(self) -> Dict[int, Dict[str, str]]:
        meta: Dict[int, Dict[str, str]] = {}
        with open(self.agents_csv_path, encoding="utf-8") as f:
            for row in csv.reader(f, delimiter=";"):
                if len(row) < 6:
                    continue
                aid = int(row[0])
                meta[aid] = {
                    "color": row[1], "nationality": row[2],
                    "drink": row[3], "cigarettes": row[4], "pet": row[5].strip()
                }
        return meta

    def _nationality_to_id(self, nat: str) -> int:
        return self._nat_to_id.get(nat.strip().lower(), -1)

    def _parse_observer_log(self) -> Dict[int, List[Dict[str, Any]]]:

        by_time: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        with open(self.observer_log_path, encoding="utf-8") as f:
            for row in csv.reader(f, delimiter=";"):
                if len(row) < 3:
                    continue
                try:
                    event_num, t = int(row[0]), int(row[1])
                except ValueError:
                    continue
                et = row[2].strip()
                et_low = et.lower()
                base: Dict[str, Any] = {"event_num": event_num, "time": t, "event_type": et}

                if et_low == "starttrip" and len(row) >= 6:
                    base["agent_id"] = self._nationality_to_id(row[3])
                    by_time[t].append(base)

                elif et_low == "finishtrip":
                    if len(row) == 5:
                        base["agent_id"] = self._nationality_to_id(row[3])
                        base["house"] = int(row[4])
                        by_time[t].append(base)
                    elif len(row) >= 6:
                        base["agent_id"] = self._nationality_to_id(row[4])
                        base["house"] = int(row[5])
                        by_time[t].append(base)

                elif et_low == "changehouse" and len(row) >= 4:
                    qty = int(row[3])
                    nats = row[4:4 + qty]
                    houses = row[4 + qty:4 + 2 * qty]
                    base["assignments"] = [
                        (self._nationality_to_id(n), int(h))
                        for n, h in zip(nats, houses)
                    ]
                    by_time[t].append(base)

                elif et_low == "changepet" and len(row) >= 4:
                    qty = int(row[3])
                    nats = row[4:4 + qty]
                    pets = row[4 + qty:4 + 2 * qty]
                    base["assignments"] = [
                        (self._nationality_to_id(n), p.strip())
                        for n, p in zip(nats, pets)
                    ]
                    by_time[t].append(base)

        return by_time


    def _init_world_state(self) -> None:
        for aid, meta in self.agents_meta.items():
            self.location[aid] = aid
            self.agent_house[aid] = aid
            self.pet[aid] = meta["pet"]
            self.owner_of[aid] = aid

    def _init_knowledge(self) -> None:
        for aid in self.agents_meta:
            self.knowledge[aid] = {
                aid: {
                    "pet": self.pet[aid],
                    "house": aid,
                    "location": aid,
                    "t": 0,
                }
            }
            self._prev[aid] = {}


    def _process_finish_trip(self, ev: Dict[str, Any], t: int) -> None:
        aid = ev.get("agent_id", -1)
        if aid == -1:
            return
        house = ev["house"]
        self.location[aid] = house
        self.knowledge[aid][aid]["location"] = house
        self.knowledge[aid][aid]["t"] = t

    def _process_change_house(self, ev: Dict[str, Any], t: int) -> None:
        assignments: List[Tuple[int, int]] = ev.get("assignments", [])
        if not assignments or any(aid == -1 for aid, _ in assignments):
            return

        participants = [aid for aid, _ in assignments]
        locs = {self.location[p] for p in participants if self.location[p] is not None}
        exchange_house: Optional[int] = locs.pop() if len(locs) == 1 else None

        for aid, new_house in assignments:
            self.agent_house[aid] = new_house
            self.owner_of[new_house] = aid
            self.knowledge[aid][aid]["house"] = new_house
            self.knowledge[aid][aid]["t"] = t

        if exchange_house is None:
            return

        witnesses = {a for a, loc in self.location.items() if loc == exchange_house}
        for w in witnesses:
            for aid, new_house in assignments:
                if w == aid:
                    continue 
                if aid in self.knowledge[w]:
                    self.knowledge[w][aid]["house"] = new_house
                    self.knowledge[w][aid]["t"] = t
                else:
                    self.knowledge[w][aid] = {
                        "pet":      self.pet[aid],
                        "house":    self.agent_house[aid],
                        "location": exchange_house,
                        "t":        t,
                    }

    def _process_change_pet(self, ev: Dict[str, Any], t: int) -> None:
        assignments: List[Tuple[int, str]] = ev.get("assignments", [])
        if not assignments or any(aid == -1 for aid, _ in assignments):
            return

        participants = [aid for aid, _ in assignments]
        locs = {self.location[p] for p in participants if self.location[p] is not None}
        exchange_house: Optional[int] = locs.pop() if len(locs) == 1 else None

        for aid, new_pet in assignments:
            self.pet[aid] = new_pet
            self.knowledge[aid][aid]["pet"] = new_pet
            self.knowledge[aid][aid]["t"] = t

        if exchange_house is None:
            return

        witnesses = {a for a, loc in self.location.items() if loc == exchange_house}
        for w in witnesses:
            for aid, new_pet in assignments:
                if w == aid:
                    continue  
                if aid in self.knowledge[w]:
                    self.knowledge[w][aid]["pet"] = new_pet
                    self.knowledge[w][aid]["t"] = t
                else:
                    self.knowledge[w][aid] = {
                        "pet":      self.pet[aid],
                        "house":    self.agent_house[aid],
                        "location": exchange_house,
                        "t":        t,
                    }

    def _process_start_trip(self, ev: Dict[str, Any], t: int) -> None:
        aid = ev.get("agent_id", -1)
        if aid == -1:
            return
        
        self.location[aid] = None


    def _propagate_copresence(self, t: int) -> None:
        """After all FinishTrips in a tick, agents co-located at a house exchange
        full state — but only when the house owner is currently present."""
        house_to_agents: Dict[int, Set[int]] = defaultdict(set)
        for aid, loc in self.location.items():
            if loc is not None:
                house_to_agents[loc].add(aid)

        for h, agents in house_to_agents.items():
            if self.owner_of.get(h) not in agents:
                continue  
            agents_list = sorted(agents)
            for i, a in enumerate(agents_list):
                for b in agents_list[i + 1:]:
                    self.knowledge[a][b] = {
                        "pet": self.pet[b],
                        "house": self.agent_house[b],
                        "location": self.location[b],  
                        "t": t,
                    }
                    self.knowledge[b][a] = {
                        "pet": self.pet[a],
                        "house": self.agent_house[a],
                        "location": self.location[a],
                        "t": t,
                    }


    def _snapshot(self, aid: int) -> Dict[int, Dict[str, Any]]:
        return {k: dict(v) for k, v in self.knowledge[aid].items()}

    def _knowledge_changed(self, aid: int) -> bool:
        prev = self._prev.get(aid, {})
        curr = self.knowledge[aid]
        if set(prev) != set(curr):
            return True
        return any(prev[k] != curr[k] for k in curr)

    def _log_phase(self, t: int, label: str) -> None:
        for aid in self.knowledge:
            if self._knowledge_changed(aid):
                path = os.path.join(self.output_dir, f"agent_{aid}_knowledge.log")
                with open(path, "a", encoding="utf-8") as f:
                    f.write(f"{t};{label};{self.knowledge[aid]}\n")
                self._prev[aid] = self._snapshot(aid)


    def generate_knowledge_logs(self) -> None:
        self._init_world_state()
        self._init_knowledge()

        for aid in self.knowledge:
            path = os.path.join(self.output_dir, f"agent_{aid}_knowledge.log")
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"0;INIT;{self.knowledge[aid]}\n")
            self._prev[aid] = self._snapshot(aid)

        events_by_time = self._parse_observer_log()

        for t in sorted(events_by_time):
            batch = events_by_time[t]

            finish = sorted(
                [e for e in batch if e["event_type"].lower() == "finishtrip"],
                key=lambda e: e["event_num"],
            )
            house_ex = sorted(
                [e for e in batch if e["event_type"].lower() == "changehouse"],
                key=lambda e: e["event_num"],
            )
            pet_ex = sorted(
                [e for e in batch if e["event_type"].lower() == "changepet"],
                key=lambda e: e["event_num"],
            )
            starts = sorted(
                [e for e in batch if e["event_type"].lower() == "starttrip"],
                key=lambda e: e["event_num"],
            )

            for ev in finish:
                self._process_finish_trip(ev, t)
            if finish:
                self._propagate_copresence(t)
                self._log_phase(t, "FinishTrip")

            for ev in house_ex:
                self._process_change_house(ev, t)
            if house_ex:
                self._log_phase(t, "ChangeHouse")

            for ev in pet_ex:
                self._process_change_pet(ev, t)
            if pet_ex:
                self._log_phase(t, "ChangePet")

            for ev in starts:
                self._process_start_trip(ev, t)
            if starts:
                self._log_phase(t, "StartTrip")
