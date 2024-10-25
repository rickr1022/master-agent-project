import unittest
from datetime import datetime

from src.agents.master_agent import MasterAgent
from src.agents.research_agent import ResearchAgent


class TestMasterAgent(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.master_agent = MasterAgent()
        self.test_config = {"name": "test_research_agent", "symbols": ["bitcoin"]}

    def tearDown(self):
        """Clean up after each test method"""
        self.master_agent.stop()

    def test_initialization(self):
        """Test if master agent initializes properly"""
        self.assertIsNotNone(self.master_agent)
        self.assertIsNotNone(self.master_agent.logger)
        self.assertEqual(type(self.master_agent.active_agents), dict)
        self.assertEqual(len(self.master_agent.active_agents), 0)

    def test_create_agent(self):
        """Test agent creation for different types"""
        # Test creating a research agent
        research_agent = self.master_agent.create_agent("research", self.test_config)
        self.assertIsNotNone(research_agent)
        self.assertIsInstance(research_agent, ResearchAgent)

        # Test creating an unknown agent type
        unknown_agent = self.master_agent.create_agent("unknown", {})
        self.assertIsNone(unknown_agent)

        # Test creating agent with invalid config
        invalid_agent = self.master_agent.create_agent("research", None)
        self.assertIsNone(invalid_agent)

    def test_get_agent(self):
        """Test retrieving agents by name"""
        # Create an agent first
        self.master_agent.create_agent("research", self.test_config)

        # Test getting existing agent
        agent = self.master_agent.get_agent("test_research_agent")
        self.assertIsNotNone(agent)
        self.assertIsInstance(agent, ResearchAgent)

        # Test getting non-existent agent
        non_existent = self.master_agent.get_agent("non_existent")
        self.assertIsNone(non_existent)

    def test_list_agents(self):
        """Test listing all active agents"""
        # Create multiple agents
        self.master_agent.create_agent(
            "research", {"name": "research_1", "symbols": ["bitcoin"]}
        )
        self.master_agent.create_agent(
            "research", {"name": "research_2", "symbols": ["ethereum"]}
        )

        # Test listing agents
        agents = self.master_agent.list_agents()
        self.assertEqual(len(agents), 2)
        self.assertIn("research_1", agents)
        self.assertIn("research_2", agents)
        self.assertEqual(agents["research_1"], "ResearchAgent")

    def test_remove_agent(self):
        """Test removing agents"""
        # Create an agent
        self.master_agent.create_agent("research", self.test_config)

        # Test removing existing agent
        result = self.master_agent.remove_agent("test_research_agent")
        self.assertTrue(result)
        self.assertEqual(len(self.master_agent.active_agents), 0)

        # Test removing non-existent agent
        result = self.master_agent.remove_agent("non_existent")
        self.assertFalse(result)

    def test_system_status(self):
        """Test system status reporting"""
        # Create some agents
        self.master_agent.create_agent(
            "research", {"name": "research_1", "symbols": ["bitcoin"]}
        )

        # Get system status
        status = self.master_agent.get_system_status()

        # Verify status structure
        self.assertIn("active_agents", status)
        self.assertIn("agent_types", status)
        self.assertIn("timestamp", status)
        self.assertIn("status", status)

        # Verify status content
        self.assertEqual(status["active_agents"], 1)
        self.assertIn("ResearchAgent", status["agent_types"])
        self.assertEqual(status["status"], "running")

        # Verify timestamp format
        try:
            datetime.fromisoformat(status["timestamp"])
        except ValueError:
            self.fail("Timestamp is not in ISO format")

    def test_execute_task(self):
        """Test task execution on agents"""
        # Create a research agent
        self.master_agent.create_agent("research", self.test_config)

        # Test executing valid task
        result = self.master_agent.execute_task(
            "test_research_agent", "analyze_market_sentiment", {"symbol": "bitcoin"}
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

        # Test executing task on non-existent agent
        result = self.master_agent.execute_task(
            "non_existent", "analyze_market_sentiment", {"symbol": "bitcoin"}
        )
        self.assertIsNone(result)

        # Test executing non-existent task
        result = self.master_agent.execute_task(
            "test_research_agent", "non_existent_task", {}
        )
        self.assertIsNone(result)

        # Test executing task with invalid parameters
        result = self.master_agent.execute_task(
            "test_research_agent",
            "analyze_market_sentiment",
            {},  # Missing required parameter
        )
        self.assertIsNone(result)

    def test_start_stop(self):
        """Test starting and stopping the master agent"""
        # Create an agent
        self.master_agent.create_agent("research", self.test_config)

        # Test start
        self.master_agent.start()
        status = self.master_agent.get_system_status()
        self.assertEqual(status["status"], "running")

        # Test stop
        self.master_agent.stop()
        # Note: In a real implementation, you might want to check for a "stopped" status


if __name__ == "__main__":
    unittest.main()
