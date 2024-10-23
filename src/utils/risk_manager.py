# src/risk_manager.py
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Position:
    symbol: str
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    current_price: float = 0.0
    unrealized_pnl: float = 0.0

class RiskManager:
    def __init__(self, config: Dict[str, Any]):
        self.max_daily_loss = config.get('max_daily_loss', 2.0)  # 2% max daily loss
        self.max_drawdown = config.get('max_drawdown', 15.0)     # 15% max drawdown
        self.position_sizing = config.get('position_sizing', 1.0) # 1% risk per trade
        self.max_position_size = config.get('max_position_size', 1000)
        self.logger = self._setup_logging()
        self.daily_losses = 0
        self.peak_balance = config.get('initial_balance', 500)
        self.current_balance = self.peak_balance

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('risk_manager')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(f'logs/risk_manager_{datetime.now().strftime("%Y%m%d")}.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def calculate_position_size(self, account_balance: float, entry_price: float, 
                                stop_loss: float) -> float:
        """Calculate safe position size using Kelly Criterion"""
        # Calculate risk amount based on account balance
        risk_amount = account_balance * (self.position_sizing / 100)

        # Calculate price risk
        price_risk = abs(entry_price - stop_loss)
        if price_risk == 0:
            return 0

        # Calculate base position size
        position_size = risk_amount / price_risk

        # Apply Kelly Criterion
        kelly_percentage = self.calculate_kelly_criterion()
        position_size *= kelly_percentage

        # Apply maximum position size limit
        position_size = min(position_size, self.max_position_size)

        self.logger.info(f"Calculated position size: {position_size}")
        return position_size

    def calculate_kelly_criterion(self) -> float:
        """Calculate Kelly Criterion for position sizing"""
        win_rate = 0.55  # Example: 55% win rate
        win_loss_ratio = 1.5  # Example: Average win / Average loss

        # Kelly Formula: f = (p*b - q)/b
        # where: p = win rate, q = loss rate, b = win/loss ratio
        kelly_percentage = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio

        # Use half-Kelly for more conservative sizing
        kelly_percentage *= 0.5

        return max(0, min(kelly_percentage, 1))  # Bound between 0 and 1

    def validate_trade(self, trade_params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if a trade meets risk management criteria"""
        validation = {
            "is_valid": False,
            "reason": "",
            "suggested_size": 0
        }

        # Calculate current drawdown
        current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance * 100

        # Check drawdown first (this is a more critical limit)
        if current_drawdown >= self.max_drawdown:
            validation["reason"] = "Maximum drawdown reached"
            self.logger.warning(f"Drawdown limit reached: {current_drawdown}%")
            return validation

        # Then check daily loss limit
        if self.daily_losses >= (self.peak_balance * self.max_daily_loss / 100):
            validation["reason"] = "Daily loss limit reached"
            self.logger.warning(f"Daily loss limit reached: {self.daily_losses}")
            return validation

        # Calculate position size
        account_balance = trade_params.get('account_balance', 0)
        entry_price = trade_params.get('entry_price', 0)
        stop_loss = trade_params.get('stop_loss', 0)

        if not all([account_balance, entry_price, stop_loss]):
            validation["reason"] = "Missing required parameters"
            return validation

        suggested_size = self.calculate_position_size(
            account_balance, 
            entry_price, 
            stop_loss
        )

        if suggested_size <= 0:
            validation["reason"] = "Invalid position size calculated"
            return validation

        validation["is_valid"] = True
        validation["suggested_size"] = suggested_size
        return validation

    def update_metrics(self, trade_result: Dict[str, Any]) -> None:
        """Update risk metrics after a trade"""
        pnl = trade_result.get('pnl', 0)
        self.current_balance += pnl

        if pnl < 0:
            self.daily_losses += abs(pnl)

        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance

        self.logger.info(f"Updated metrics - Balance: {self.current_balance}, "
                         f"Daily Losses: {self.daily_losses}")