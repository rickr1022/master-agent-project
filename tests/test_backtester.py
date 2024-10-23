import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.utils.backtester import Backtester, TradePosition

class TestBacktester(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'initial_capital': 500,
            'risk_per_trade': 0.01,
            'stop_loss_percentage': 0.02,
            'take_profit_percentage': 0.03,
            'max_positions': 5,
            'min_confidence': 0.7
        }
        self.backtester = Backtester(self.config)
        
        # Create sample price data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        self.sample_data = pd.DataFrame({
            'open': np.linspace(100, 200, 100) + np.random.normal(0, 5, 100),
            'high': np.linspace(102, 202, 100) + np.random.normal(0, 5, 100),
            'low': np.linspace(98, 198, 100) + np.random.normal(0, 5, 100),
            'close': np.linspace(100, 200, 100) + np.random.normal(0, 5, 100),
            'volume': np.random.randint(1000, 5000, 100)
        }, index=dates)
        
    def test_initialization(self):
        """Test backtester initialization"""
        self.assertEqual(self.backtester.initial_capital, 500)
        self.assertEqual(self.backtester.current_capital, 500)
        self.assertEqual(len(self.backtester.positions), 0)
        self.assertEqual(len(self.backtester.trades_history), 0)
        self.assertEqual(len(self.backtester.equity_curve), 1)
        self.assertEqual(self.backtester.equity_curve[0], 500)
        
    def test_position_creation(self):
        """Test creating a new position"""
        # Create a sample analysis result
        analysis = {
            'signal': 'LONG',
            'confidence': 0.8
        }
        
        # Get current bar data
        current_bar = pd.Series({
            'open': 100,
            'high': 102,
            'low': 98,
            'close': 101,
            'volume': 1000
        }, name=datetime.now())
        
        # Execute trade
        self.backtester._execute_trade(analysis, current_bar)
        
        # Verify position was created
        self.assertEqual(len(self.backtester.positions), 1)
        position = self.backtester.positions[0]
        self.assertEqual(position.type, 'LONG')
        self.assertEqual(position.entry_price, 101)
        self.assertLess(position.stop_loss, position.entry_price)
        self.assertGreater(position.take_profit, position.entry_price)
        
    def test_position_closing(self):
        """Test closing a position"""
        # Create a position
        position = TradePosition(
            type='LONG',
            entry_price=100,
            size=1,
            stop_loss=98,
            take_profit=103,
            entry_time=datetime.now(),
            entry_capital=self.backtester.current_capital
        )
        self.backtester.positions.append(position)
        
        # Close position with profit
        self.backtester._close_position(position, 102, 'Take Profit')
        
        # Verify position was closed correctly
        self.assertEqual(len(self.backtester.positions), 0)
        self.assertEqual(len(self.backtester.trades_history), 1)
        self.assertGreater(self.backtester.current_capital, 500)  # Should have profit
        
    def test_run_backtest(self):
        """Test running a complete backtest"""
        # Run backtest
        results = self.backtester.run_backtest(self.sample_data)
        
        # Verify results structure
        self.assertIn('overview', results)
        self.assertIn('risk_metrics', results)
        self.assertIn('trade_metrics', results)
        self.assertIn('equity_curve', results)
        
        # Verify metrics
        self.assertEqual(results['overview']['initial_capital'], 500)
        self.assertIsInstance(results['overview']['final_capital'], float)
        self.assertIsInstance(results['overview']['total_return_pct'], float)
        
    def test_risk_management(self):
        """Test risk management rules"""
        # Create a position that would exceed max positions
        for _ in range(self.config['max_positions'] + 1):
            analysis = {
                'signal': 'LONG',
                'confidence': 0.8
            }
            current_bar = pd.Series({
                'open': 100,
                'high': 102,
                'low': 98,
                'close': 101,
                'volume': 1000
            }, name=datetime.now())
            
            self.backtester._execute_trade(analysis, current_bar)
            
        # Verify max positions limit is enforced
        self.assertLessEqual(len(self.backtester.positions), self.config['max_positions'])
        
    def test_metrics_calculation(self):
        """Test calculation of performance metrics"""
        # Create some sample trades
        self.backtester.trades_history = [
            {
                'type': 'LONG',
                'entry_price': 100,
                'exit_price': 105,
                'size': 1,
                'pnl': 5,
                'return_pct': 5,
                'entry_time': datetime.now(),
                'exit_time': datetime.now() + timedelta(hours=1),
                'exit_reason': 'Take Profit'
            },
            {
                'type': 'LONG',
                'entry_price': 100,
                'exit_price': 98,
                'size': 1,
                'pnl': -2,
                'return_pct': -2,
                'entry_time': datetime.now(),
                'exit_time': datetime.now() + timedelta(hours=1),
                'exit_reason': 'Stop Loss'
            }
        ]
        
        metrics = self.backtester._calculate_trade_metrics()
        
        # Verify metrics
        self.assertEqual(metrics['win_rate'], 0.5)  # 1 win, 1 loss
        self.assertEqual(metrics['avg_win'], 5)
        self.assertEqual(metrics['avg_loss'], -2)
        self.assertEqual(metrics['largest_win'], 5)
        self.assertEqual(metrics['largest_loss'], -2)
        
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test with empty dataset
        empty_data = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
        results = self.backtester.run_backtest(empty_data)
        self.assertEqual(results['overview']['total_trades'], 0)
        
        # Test with single data point
        single_data = pd.DataFrame({
            'open': [100],
            'high': [102],
            'low': [98],
            'close': [101],
            'volume': [1000]
        }, index=[datetime.now()])
        results = self.backtester.run_backtest(single_data)
        self.assertEqual(results['overview']['total_trades'], 0)

if __name__ == '__main__':
    unittest.main()