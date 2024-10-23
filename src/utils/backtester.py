import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import os
from src.utils.market_analyzer import MarketAnalyzer
from src.utils.risk_manager import RiskManager
from dataclasses import dataclass

@dataclass
class TradePosition:
    """Class for tracking trade positions"""
    type: str  # 'LONG' or 'SHORT'
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    entry_capital: float
    metadata: Dict = None

class Backtester:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.initial_capital = config.get('initial_capital', 500)
        self.current_capital = self.initial_capital
        self.risk_per_trade = config.get('risk_per_trade', 0.01)
        self.market_analyzer = MarketAnalyzer(config)
        self.risk_manager = RiskManager(config)
        self.positions: List[TradePosition] = []
        self.trades_history: List[Dict] = []
        self.equity_curve = [self.initial_capital]
        self.drawdowns = []
        self.logger = self._setup_logging()
        self.max_positions = config.get('max_positions', 5)
        
    def _setup_logging(self) -> logging.Logger:
        """Configure logging for the backtester"""
        logger = logging.getLogger('backtester')
        logger.setLevel(logging.INFO)
        os.makedirs('logs', exist_ok=True)
        handler = logging.FileHandler(
            f'logs/backtester_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _log_progress(self, current_bar: int, total_bars: int):
        """Log backtesting progress"""
        if current_bar % 100 == 0:
            progress = (current_bar / total_bars) * 100
            self.logger.info(f"Backtest progress: {progress:.2f}% complete")
            self.logger.info(f"Current capital: {self.current_capital:.2f}")

    def run_backtest(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Run complete backtest on historical data"""
        self.logger.info(f"Starting backtest with {len(data)} data points")
        
        try:
            # Reset state for new backtest
            self._reset_state()
            
            # Main backtest loop
            for i in range(len(data)-1):
                current_data = data.iloc[:i+1]
                next_bar = data.iloc[i+1]
                
                # Process existing positions
                self._process_open_positions(next_bar)
                
                # Get new signals
                analysis = self.market_analyzer.analyze_market(current_data)
                
                # Execute new trades if conditions met
                if self._should_execute_trade(analysis):
                    self._execute_trade(analysis, next_bar)
                
                # Update equity and drawdown
                self._update_metrics(next_bar)
                
                # Log progress periodically
                self._log_progress(i, len(data))
            
            # Generate final results
            return self._generate_backtest_report()
            
        except Exception as e:
            self.logger.error(f"Error in backtest: {str(e)}")
            raise

    def _reset_state(self):
        """Reset backtester state for new run"""
        self.current_capital = self.initial_capital
        self.positions = []
        self.trades_history = []
        self.equity_curve = [self.initial_capital]
        self.drawdowns = []

    def _should_execute_trade(self, analysis: Dict[str, Any]) -> bool:
        """Determine if we should execute a trade"""
        if len(self.positions) >= self.max_positions:
            self.logger.info(f"Max positions ({self.max_positions}) reached")
            return False
        
        return (
            analysis.get('signal') in ['BUY', 'SELL'] and 
            analysis.get('confidence', 0) > self.config.get('min_confidence', 0.7)
        )

    def _execute_trade(self, analysis: Dict[str, Any], current_bar: pd.Series):
        """Execute a new trade based on analysis"""
        # Calculate position size
        risk_amount = self.current_capital * self.risk_per_trade
        stop_loss = self._calculate_stop_loss(analysis['signal'], current_bar['close'])
        
        position_size = self.risk_manager.calculate_position_size(
            account_balance=self.current_capital,
            entry_price=current_bar['close'],
            stop_loss=stop_loss
        )
        
        take_profit = self._calculate_take_profit(analysis['signal'], current_bar['close'])
        
        position = TradePosition(
            type=analysis['signal'],
            entry_price=current_bar['close'],
            size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=current_bar.name,
            entry_capital=self.current_capital,
            metadata={'analysis': analysis}
        )
        
        self.positions.append(position)
        self.logger.info(f"Opened {position.type} position: {position}")

    def _process_open_positions(self, current_bar: pd.Series):
        """Process all open positions"""
        for position in self.positions[:]:
            if self._hit_stop_loss(position, current_bar):
                self._close_position(position, position.stop_loss, 'Stop Loss')
            elif self._hit_take_profit(position, current_bar):
                self._close_position(position, position.take_profit, 'Take Profit')

    def _close_position(self, position: TradePosition, exit_price: float, reason: str):
        """Close a position and record the trade"""
        if position.type == 'LONG':
            pnl = (exit_price - position.entry_price) * position.size
        else:  # SHORT
            pnl = (position.entry_price - exit_price) * position.size
        
        self.current_capital += pnl
        
        trade_record = {
            'type': position.type,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'size': position.size,
            'pnl': pnl,
            'return_pct': (pnl / position.entry_capital) * 100,
            'entry_time': position.entry_time,
            'exit_time': datetime.now(),
            'exit_reason': reason,
            'metadata': position.metadata
        }
        
        self.trades_history.append(trade_record)
        self.positions.remove(position)
        
        self.logger.info(
            f"Closed position: {trade_record['type']} | "
            f"PNL: {pnl:.2f} | Reason: {reason}"
        )

    def _hit_stop_loss(self, position: TradePosition, current_bar: pd.Series) -> bool:
        """Check if position hit stop loss"""
        if position.type == 'LONG':
            return current_bar['low'] <= position.stop_loss
        return current_bar['high'] >= position.stop_loss

    def _hit_take_profit(self, position: TradePosition, current_bar: pd.Series) -> bool:
        """Check if position hit take profit"""
        if position.type == 'LONG':
            return current_bar['high'] >= position.take_profit
        return current_bar['low'] <= position.take_profit

    def _calculate_stop_loss(self, signal: str, entry_price: float) -> float:
        """Calculate stop loss price"""
        stop_percentage = self.config.get('stop_loss_percentage', 0.02)
        return entry_price * (1 - stop_percentage) if signal == 'LONG' else entry_price * (1 + stop_percentage)

    def _calculate_take_profit(self, signal: str, entry_price: float) -> float:
        """Calculate take profit price"""
        profit_percentage = self.config.get('take_profit_percentage', 0.03)
        return entry_price * (1 + profit_percentage) if signal == 'LONG' else entry_price * (1 - profit_percentage)

    def _update_metrics(self, current_bar: pd.Series):
        """Update equity curve and drawdown metrics"""
        self.equity_curve.append(self.current_capital)
        
        peak_capital = max(self.equity_curve)
        current_drawdown = (peak_capital - self.current_capital) / peak_capital
        self.drawdowns.append(current_drawdown)

    def _calculate_trade_metrics(self) -> Dict[str, Any]:
        """Calculate trade-related metrics"""
        if not self.trades_history:
            return {
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "largest_win": 0,
                "largest_loss": 0
            }
        
        winning_trades = [t for t in self.trades_history if t['pnl'] > 0]
        losing_trades = [t for t in self.trades_history if t['pnl'] < 0]
        
        return {
            "win_rate": len(winning_trades) / len(self.trades_history) if self.trades_history else 0,
            "avg_win": np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0,
            "avg_loss": np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0,
            "largest_win": max([t['pnl'] for t in self.trades_history]) if self.trades_history else 0,
            "largest_loss": min([t['pnl'] for t in self.trades_history]) if self.trades_history else 0
        }

    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe Ratio"""
        if len(returns) == 0:
            return 0.0
        excess_returns = returns - (risk_free_rate / 252)
        if np.std(excess_returns) == 0:
            return 0.0
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)

    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino Ratio"""
        if len(returns) == 0:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / 252)
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            return np.inf
            
        downside_std = np.std(downside_returns)
        if downside_std == 0:
            return np.inf
            
        return np.mean(excess_returns) / downside_std * np.sqrt(252)

    def _calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Value at Risk"""
        if len(returns) == 0:
            return 0.0
        return np.percentile(returns, (1 - confidence) * 100)

    def _calculate_expected_shortfall(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Expected Shortfall (CVaR)"""
        if len(returns) == 0:
            return 0.0
        var = self._calculate_var(returns, confidence)
        return np.mean(returns[returns <= var])

    def _generate_backtest_report(self) -> Dict[str, Any]:
        """Generate final backtest report"""
        returns = pd.Series([t['return_pct'] for t in self.trades_history])
        
        report = {
            'overview': {
                'initial_capital': self.initial_capital,
                'final_capital': self.current_capital,
                'total_return_pct': ((self.current_capital / self.initial_capital) - 1) * 100,
                'total_trades': len(self.trades_history),
                'winning_trades': len([t for t in self.trades_history if t['pnl'] > 0])
            },
            'risk_metrics': {
                'sharpe_ratio': self._calculate_sharpe_ratio(returns),
                'sortino_ratio': self._calculate_sortino_ratio(returns),
                'max_drawdown': max(self.drawdowns) if self.drawdowns else 0,
                'var': self._calculate_var(returns),
                'expected_shortfall': self._calculate_expected_shortfall(returns)
            },
            'trade_metrics': self._calculate_trade_metrics(),
            'equity_curve': self.equity_curve,
            'drawdowns': self.drawdowns,
            'trades': self.trades_history
        }
        
        return report