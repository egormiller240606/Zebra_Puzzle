# Refactoring Plan

## Goal: Split Simulation.py into modules without breaking logic

## Structure
```
Zebra_Puzzle/
├── data/
├── log_analyzer.py
├── README.md
├── main.py
├── entities/
│   ├── __init__.py
│   ├── agent.py
│   └── house.py
├── events/
│   ├── __init__.py
│   ├── base.py
│   ├── trip.py
│   └── exchange.py
├── logging/
│   ├── __init__.py
│   └── knowledge_logger.py
├── loaders/
│   ├── __init__.py
│   └── csv_utils.py
└── simulation/
    ├── __init__.py
    └── environment.py
```

## Steps
- [ ] Create folders: entities/, events/, logging/, loaders/, simulation/
- [ ] Create __init__.py files
- [ ] Create entities/agent.py (Agent class)
- [ ] Create entities/house.py (House class)
- [ ] Create events/base.py (Event class + priorities)
- [ ] Create events/trip.py (StartTripEvent, FinishTripEvent)
- [ ] Create events/exchange.py (ChangeHouseEvent, ChangePetEvent)
- [ ] Create logging/knowledge_logger.py (AgentKnowledgeLogger)
- [ ] Create loaders/csv_utils.py (loaders + utils)
- [ ] Create simulation/environment.py (Environment class)
- [ ] Create main.py (entry point)
- [ ] Create Zebra_Puzzle/__init__.py with public exports
- [ ] Test that imports work
- [ ] Test that simulation runs correctly

