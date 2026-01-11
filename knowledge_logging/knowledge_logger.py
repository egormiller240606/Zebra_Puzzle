import os
from typing import Dict, Any


class AgentKnowledgeLogger:
    def __init__(self, log_dir: str = "data/output_data/logs"):
        self.log_dir = log_dir
        self.log_files: Dict[int, Any] = {}

        # Create directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)

    def _get_log_file(self, agent_id: int):
        """Get or create log file for agent"""
        if agent_id not in self.log_files:
            log_path = os.path.join(self.log_dir, f"agent_{agent_id}_knowledge.log")
            self.log_files[agent_id] = open(log_path, 'w', encoding='utf-8')
            # Write header
            self.log_files[agent_id].write(f"# Agent {agent_id} Knowledge Log\n")
            self.log_files[agent_id].write(f"# Format: time;event_type;knowledge\n")
        return self.log_files[agent_id]

    def log_knowledge_change(self, time: int, agent_id: int, event_type: str,
                             knowledge_after: Dict[int, Dict[str, Any]]) -> None:
        """Write agent knowledge change to CSV format"""
        f = self._get_log_file(agent_id)
        f.write(f"{time};{event_type};{knowledge_after}\n")
        f.flush()

    def close_all(self):
        """Close all open files"""
        for f in self.log_files.values():
            f.close()
        self.log_files.clear()

