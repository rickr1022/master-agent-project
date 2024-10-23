import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Project settings
    PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'master-agent-project-2024')
    
    # Trading settings
    INITIAL_INVESTMENT = 500.0
    MAX_RISK_PER_TRADE = 0.02  # 2% max risk per trade
    
    # Agent settings
    AGENT_TYPES = ['research', 'analysis', 'trading', 'risk']