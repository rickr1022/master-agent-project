import unittest
from datetime import datetime
from src.utils.risk_manager import RiskManager, Position

class TestRiskManager(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.config = {
            'max_daily_loss': 2.0,
            'max_drawdown': 15.0,
            'position_sizing': 1.0,
            'max_position_size': 1000,
            'initial_balance': 500
        }
        self.risk_manager = RiskManager(self.config)
    
    def test_initialization(self):
        """Test if risk manager initializes with correct values"""
        self.assertEqual(self.risk_manager.max_daily_loss, 2.0)
        self.assertEqual(self.risk_manager.max_drawdown, 15.0)
        self.assertEqual(self.risk_manager.position_sizing, 1.0)
        self.assertEqual(self.risk_manager.max_position_size, 1000)
        self.assertEqual(self.risk_manager.current_balance, 500)
        
    def test_calculate_position_size(self):
        """Test position size calculation"""
        # Test normal case
        size = self.risk_manager.calculate_position_size(
            account_balance=1000,
            entry_price=50000,
            stop_loss=49000
        )
        self.assertGreater(size, 0)
        self.assertLessEqual(size, self.config['max_position_size'])
        
        # Test zero price risk case
        size = self.risk_manager.calculate_position_size(
            account_balance=1000,
            entry_price=50000,
            stop_loss=50000
        )
        self.assertEqual(size, 0)
        
    def test_validate_trade(self):
        """Test trade validation"""
        # Test valid trade
        trade_params = {
            'account_balance': 1000,
            'entry_price': 50000,
            'stop_loss': 49000
        }
        validation = self.risk_manager.validate_trade(trade_params)
        self.assertTrue(validation['is_valid'])
        self.assertGreater(validation['suggested_size'], 0)
        
        # Test invalid trade (missing parameters)
        invalid_params = {
            'account_balance': 1000
        }
        validation = self.risk_manager.validate_trade(invalid_params)
        self.assertFalse(validation['is_valid'])
        
    def test_update_metrics(self):
        """Test metrics update after trades"""
        # Test profitable trade
        self.risk_manager.update_metrics({'pnl': 50})
        self.assertEqual(self.risk_manager.current_balance, 550)
        self.assertEqual(self.risk_manager.peak_balance, 550)
        
        # Test losing trade
        self.risk_manager.update_metrics({'pnl': -20})
        self.assertEqual(self.risk_manager.current_balance, 530)
        self.assertEqual(self.risk_manager.peak_balance, 550)
        self.assertEqual(self.risk_manager.daily_losses, 20)
        
    def test_drawdown_limit(self):
        """Test drawdown limit enforcement"""
        # Create large loss that exceeds drawdown limit but not daily loss limit
        initial_balance = self.config['initial_balance']
        drawdown_amount = initial_balance * (self.config['max_drawdown'] / 100 + 0.01)  # Just over max drawdown
        
        # Reset daily losses (to ensure drawdown is tested independently)
        self.risk_manager.daily_losses = 0
        
        # Apply the loss
        self.risk_manager.update_metrics({'pnl': -drawdown_amount})
        
        # Try to validate new trade
        trade_params = {
            'account_balance': self.risk_manager.current_balance,
            'entry_price': 50000,
            'stop_loss': 49000
        }
        validation = self.risk_manager.validate_trade(trade_params)
        
        # Verify drawdown limit is enforced
        self.assertFalse(validation['is_valid'])
        self.assertEqual(validation['reason'], 'Maximum drawdown reached')
        
    def test_daily_loss_limit(self):
        """Test daily loss limit enforcement"""
        # Reset the risk manager to ensure clean state
        self.risk_manager = RiskManager(self.config)
        
        # Create losses up to daily limit
        daily_loss_amount = self.config['initial_balance'] * (self.config['max_daily_loss'] / 100 + 0.01)
        self.risk_manager.update_metrics({'pnl': -daily_loss_amount})
        
        # Try to validate new trade
        trade_params = {
            'account_balance': self.risk_manager.current_balance,
            'entry_price': 50000,
            'stop_loss': 49000
        }
        validation = self.risk_manager.validate_trade(trade_params)
        
        # Verify daily loss limit is enforced
        self.assertFalse(validation['is_valid'])
        self.assertEqual(validation['reason'], 'Daily loss limit reached')

if __name__ == '__main__':
    unittest.main()