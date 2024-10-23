import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from src.agents.research_agent import ResearchAgent

class MasterAgent:
    def __init__(self):
        self.logger = self._setup_logging()
        self.active_agents: Dict[str, Any] = {}
        self.logger.info("Master Agent initializing...")
        
    def _setup_logging(self) -> logging.Logger:
        os.makedirs('logs', exist_ok=True)
        logger = logging.getLogger('master_agent')
        logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(
            f'logs/master_agent_{datetime.now().strftime("%Y%m%d")}.log'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger
    
    def create_agent(self, agent_type: str, config: Dict[str, Any]) -> Optional[Any]:
        try:
            self.logger.info(f"Creating new agent of type: {agent_type}")
            if agent_type == "research":
                agent = ResearchAgent(config)
                agent_name = config.get('name', 'default_research')
                self.active_agents[agent_name] = agent
                return agent
            return None
        except Exception as e:
            self.logger.error(f"Error creating agent: {str(e)}")
            return None
            
    def get_agent(self, agent_name: str) -> Optional[Any]:
        return self.active_agents.get(agent_name)
        
    def list_agents(self) -> Dict[str, str]:
        return {
            name: agent.__class__.__name__ 
            for name, agent in self.active_agents.items()
        }
        
    def remove_agent(self, agent_name: str) -> bool:
        try:
            if agent_name in self.active_agents:
                del self.active_agents[agent_name]
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error removing agent: {str(e)}")
            return False
            
    def get_system_status(self) -> Dict[str, Any]:
        return {
            "active_agents": len(self.active_agents),
            "agent_types": list(set(agent.__class__.__name__ 
                                  for agent in self.active_agents.values())),
            "timestamp": datetime.now().isoformat(),
            "status": "running"
        }
        
    def execute_task(self, agent_name: str, task_name: str, 
                    task_params: Dict[str, Any]) -> Optional[Any]:
        try:
            agent = self.get_agent(agent_name)
            if agent and hasattr(agent, task_name):
                task_method = getattr(agent, task_name)
                return task_method(**task_params)
            return None
        except Exception as e:
            self.logger.error(f"Error executing task: {str(e)}")
            return None
    
    def start(self):
        self.logger.info("Master Agent starting...")
        
    def stop(self):
        self.logger.info("Master Agent stopping...")