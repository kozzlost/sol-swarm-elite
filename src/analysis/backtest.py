"""
Backtesting Engine - Historical Strategy Replay
"""
import pandas as pd
from typing import List, Tuple
from datetime import datetime

class BacktestEngine:
    """Replay trades against historical data"""
    
    def __init__(self, starting_balance: float = 25.0):
        self.starting_balance = starting_balance
        self.current_balance = starting_balance
        self.trades = []
        self.positions = []
    
    def execute_backtest(
        self,
        historical_data: pd.DataFrame,
        strategy_func,
        max_position_size: float = 0.05
    ) -> Dict[str, Any]:
        """Run backtest simulation"""
        
        results = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "final_balance": self.starting_balance
        }
        
        # Iterate through historical candles
        for idx, candle in historical_data.iterrows():
            signal = strategy_func(historical_data[:idx])
            
            if signal == "BUY":
                position = {
                    "entry_price": candle['close'],
                    "entry_time": candle['timestamp'],
                    "amount_sol": max_position_size,
                    "status": "OPEN"
                }
                self.positions.append(position)
            
            elif signal == "SELL" and self.positions:
                position = self.positions.pop()
                exit_price = candle['close']
                pnl = position['amount_sol'] * (exit_price - position['entry_price'])
                
                self.trades.append({
                    "entry": position['entry_price'],
                    "exit": exit_price,
                    "pnl": pnl,
                    "duration": candle['timestamp'] - position['entry_time']
                })
                
                self.current_balance += pnl
                
                if pnl > 0:
                    results["winning_trades"] += 1
                else:
                    results["losing_trades"] += 1
                
                results["total_trades"] += 1
        
        # Calculate metrics
        if results["total_trades"] > 0:
            results["win_rate"] = results["winning_trades"] / results["total_trades"]
        
        results["total_pnl"] = self.current_balance - self.starting_balance
        results["final_balance"] = self.current_balance
        
        return results

backtest_engine = BacktestEngine()
