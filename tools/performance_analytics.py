"""
性能分析模块
提供投资组合性能评估指标，包括收益率、风险指标、交易统计等
"""

import json
import math
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class PerformanceAnalyzer:
    """
    性能分析器
    
    提供以下分析功能：
    1. 收益率计算（总收益、年化收益、日收益）
    2. 风险指标（波动率、最大回撤、VaR）
    3. 风险调整收益（夏普比率、索提诺比率、卡尔玛比率）
    4. 交易统计（胜率、盈亏比、平均持仓时间）
    5. 与基准对比分析
    """
    
    def __init__(
        self,
        risk_free_rate: float = 0.05,  # 无风险利率（年化）
        trading_days_per_year: int = 252
    ):
        """
        初始化性能分析器
        
        Args:
            risk_free_rate: 无风险利率（年化），默认 5%
            trading_days_per_year: 每年交易日数量
        """
        self.risk_free_rate = risk_free_rate
        self.trading_days_per_year = trading_days_per_year
        self.daily_risk_free_rate = risk_free_rate / trading_days_per_year
    
    # ==================== 收益率计算 ====================
    
    def calculate_total_return(
        self,
        initial_value: float,
        final_value: float
    ) -> float:
        """
        计算总收益率
        
        Args:
            initial_value: 初始资产价值
            final_value: 最终资产价值
            
        Returns:
            总收益率（小数形式）
        """
        if initial_value <= 0:
            return 0.0
        return (final_value - initial_value) / initial_value
    
    def calculate_annualized_return(
        self,
        total_return: float,
        days: int
    ) -> float:
        """
        计算年化收益率
        
        Args:
            total_return: 总收益率
            days: 投资天数
            
        Returns:
            年化收益率
        """
        if days <= 0:
            return 0.0
        
        years = days / self.trading_days_per_year
        if years <= 0:
            return 0.0
        
        # 复合年化收益率
        return (1 + total_return) ** (1 / years) - 1
    
    def calculate_daily_returns(
        self,
        portfolio_values: List[float]
    ) -> List[float]:
        """
        计算日收益率序列
        
        Args:
            portfolio_values: 每日资产价值列表
            
        Returns:
            日收益率列表
        """
        if len(portfolio_values) < 2:
            return []
        
        returns = []
        for i in range(1, len(portfolio_values)):
            if portfolio_values[i - 1] > 0:
                daily_return = (portfolio_values[i] - portfolio_values[i - 1]) / portfolio_values[i - 1]
                returns.append(daily_return)
        
        return returns
    
    # ==================== 风险指标 ====================
    
    def calculate_volatility(
        self,
        daily_returns: List[float],
        annualize: bool = True
    ) -> float:
        """
        计算波动率（标准差）
        
        Args:
            daily_returns: 日收益率列表
            annualize: 是否年化
            
        Returns:
            波动率
        """
        if len(daily_returns) < 2:
            return 0.0
        
        mean_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_return) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        std_dev = math.sqrt(variance)
        
        if annualize:
            return std_dev * math.sqrt(self.trading_days_per_year)
        return std_dev
    
    def calculate_downside_deviation(
        self,
        daily_returns: List[float],
        target_return: float = 0.0,
        annualize: bool = True
    ) -> float:
        """
        计算下行标准差（只考虑负收益）
        
        Args:
            daily_returns: 日收益率列表
            target_return: 目标收益率
            annualize: 是否年化
            
        Returns:
            下行标准差
        """
        if len(daily_returns) < 2:
            return 0.0
        
        downside_returns = [min(0, r - target_return) for r in daily_returns]
        downside_variance = sum(r ** 2 for r in downside_returns) / len(downside_returns)
        downside_std = math.sqrt(downside_variance)
        
        if annualize:
            return downside_std * math.sqrt(self.trading_days_per_year)
        return downside_std
    
    def calculate_max_drawdown(
        self,
        portfolio_values: List[float]
    ) -> Tuple[float, int, int]:
        """
        计算最大回撤
        
        Args:
            portfolio_values: 每日资产价值列表
            
        Returns:
            (最大回撤, 峰值索引, 谷值索引)
        """
        if len(portfolio_values) < 2:
            return 0.0, 0, 0
        
        max_drawdown = 0.0
        peak_idx = 0
        trough_idx = 0
        peak = portfolio_values[0]
        peak_temp_idx = 0
        
        for i, value in enumerate(portfolio_values):
            if value > peak:
                peak = value
                peak_temp_idx = i
            
            drawdown = (peak - value) / peak if peak > 0 else 0
            
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                peak_idx = peak_temp_idx
                trough_idx = i
        
        return max_drawdown, peak_idx, trough_idx
    
    def calculate_var(
        self,
        daily_returns: List[float],
        confidence: float = 0.95
    ) -> float:
        """
        计算 Value at Risk (历史模拟法)
        
        Args:
            daily_returns: 日收益率列表
            confidence: 置信水平
            
        Returns:
            VaR 值（正数表示损失）
        """
        if len(daily_returns) < 10:
            return 0.0
        
        sorted_returns = sorted(daily_returns)
        index = int((1 - confidence) * len(sorted_returns))
        
        return -sorted_returns[index]
    
    def calculate_cvar(
        self,
        daily_returns: List[float],
        confidence: float = 0.95
    ) -> float:
        """
        计算 Conditional VaR (Expected Shortfall)
        
        Args:
            daily_returns: 日收益率列表
            confidence: 置信水平
            
        Returns:
            CVaR 值
        """
        if len(daily_returns) < 10:
            return 0.0
        
        sorted_returns = sorted(daily_returns)
        index = int((1 - confidence) * len(sorted_returns))
        
        if index == 0:
            return -sorted_returns[0]
        
        tail_returns = sorted_returns[:index]
        return -sum(tail_returns) / len(tail_returns)
    
    # ==================== 风险调整收益 ====================
    
    def calculate_sharpe_ratio(
        self,
        daily_returns: List[float]
    ) -> float:
        """
        计算夏普比率
        
        Args:
            daily_returns: 日收益率列表
            
        Returns:
            夏普比率
        """
        if len(daily_returns) < 2:
            return 0.0
        
        mean_return = sum(daily_returns) / len(daily_returns)
        excess_return = mean_return - self.daily_risk_free_rate
        
        volatility = self.calculate_volatility(daily_returns, annualize=False)
        
        if volatility == 0:
            return 0.0
        
        # 年化夏普比率
        return (excess_return / volatility) * math.sqrt(self.trading_days_per_year)
    
    def calculate_sortino_ratio(
        self,
        daily_returns: List[float]
    ) -> float:
        """
        计算索提诺比率（使用下行标准差）
        
        Args:
            daily_returns: 日收益率列表
            
        Returns:
            索提诺比率
        """
        if len(daily_returns) < 2:
            return 0.0
        
        mean_return = sum(daily_returns) / len(daily_returns)
        excess_return = mean_return - self.daily_risk_free_rate
        
        downside_dev = self.calculate_downside_deviation(daily_returns, annualize=False)
        
        if downside_dev == 0:
            return 0.0
        
        # 年化索提诺比率
        return (excess_return / downside_dev) * math.sqrt(self.trading_days_per_year)
    
    def calculate_calmar_ratio(
        self,
        annualized_return: float,
        max_drawdown: float
    ) -> float:
        """
        计算卡尔玛比率（年化收益 / 最大回撤）
        
        Args:
            annualized_return: 年化收益率
            max_drawdown: 最大回撤
            
        Returns:
            卡尔玛比率
        """
        if max_drawdown == 0:
            return 0.0
        
        return annualized_return / max_drawdown
    
    def calculate_information_ratio(
        self,
        portfolio_returns: List[float],
        benchmark_returns: List[float]
    ) -> float:
        """
        计算信息比率（相对于基准的超额收益 / 跟踪误差）
        
        Args:
            portfolio_returns: 组合日收益率
            benchmark_returns: 基准日收益率
            
        Returns:
            信息比率
        """
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return 0.0
        
        # 计算超额收益
        excess_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        
        mean_excess = sum(excess_returns) / len(excess_returns)
        
        # 计算跟踪误差
        variance = sum((r - mean_excess) ** 2 for r in excess_returns) / (len(excess_returns) - 1)
        tracking_error = math.sqrt(variance) * math.sqrt(self.trading_days_per_year)
        
        if tracking_error == 0:
            return 0.0
        
        return (mean_excess * self.trading_days_per_year) / tracking_error
    
    # ==================== 交易统计 ====================
    
    def analyze_trades(
        self,
        trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析交易记录
        
        Args:
            trades: 交易记录列表，每条记录包含 action, symbol, amount, price, pnl 等
            
        Returns:
            交易统计字典
        """
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "avg_trade_pnl": 0.0
            }
        
        # 分离盈利和亏损交易
        winning_trades = []
        losing_trades = []
        
        for trade in trades:
            pnl = trade.get("pnl_amount", 0)
            if pnl > 0:
                winning_trades.append(pnl)
            elif pnl < 0:
                losing_trades.append(pnl)
        
        total_trades = len(trades)
        num_winners = len(winning_trades)
        num_losers = len(losing_trades)
        
        # 计算统计指标
        win_rate = num_winners / total_trades if total_trades > 0 else 0
        avg_win = sum(winning_trades) / num_winners if num_winners > 0 else 0
        avg_loss = sum(losing_trades) / num_losers if num_losers > 0 else 0
        
        total_wins = sum(winning_trades)
        total_losses = abs(sum(losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        all_pnl = [t.get("pnl_amount", 0) for t in trades]
        avg_trade_pnl = sum(all_pnl) / len(all_pnl) if all_pnl else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": num_winners,
            "losing_trades": num_losers,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "avg_trade_pnl": avg_trade_pnl,
            "total_profit": total_wins,
            "total_loss": total_losses,
            "net_profit": total_wins - total_losses
        }
    
    def calculate_holding_period(
        self,
        trades: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        计算平均持仓时间
        
        Args:
            trades: 交易记录（需要包含 date 和 symbol）
            
        Returns:
            各股票的平均持仓天数
        """
        # 按股票分组
        symbol_trades = defaultdict(list)
        for trade in trades:
            symbol = trade.get("symbol")
            if symbol:
                symbol_trades[symbol].append(trade)
        
        holding_periods = {}
        
        for symbol, sym_trades in symbol_trades.items():
            # 简化计算：买入到卖出的时间差
            buy_dates = []
            sell_dates = []
            
            for trade in sym_trades:
                action = trade.get("action")
                date_str = trade.get("date")
                if date_str:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    if action == "buy":
                        buy_dates.append(date)
                    elif action == "sell":
                        sell_dates.append(date)
            
            if buy_dates and sell_dates:
                # 简化：最后卖出 - 第一次买入
                avg_days = (max(sell_dates) - min(buy_dates)).days
                holding_periods[symbol] = avg_days
        
        return holding_periods
    
    # ==================== 综合分析 ====================
    
    def generate_performance_report(
        self,
        portfolio_values: List[float],
        trades: List[Dict[str, Any]] = None,
        benchmark_values: List[float] = None,
        initial_cash: float = 10000.0
    ) -> Dict[str, Any]:
        """
        生成综合性能报告
        
        Args:
            portfolio_values: 每日资产价值列表
            trades: 交易记录列表
            benchmark_values: 基准每日价值列表
            initial_cash: 初始资金
            
        Returns:
            综合性能报告
        """
        if not portfolio_values:
            return {"error": "No portfolio data"}
        
        # 基础收益计算
        initial_value = portfolio_values[0]
        final_value = portfolio_values[-1]
        total_return = self.calculate_total_return(initial_value, final_value)
        days = len(portfolio_values)
        annualized_return = self.calculate_annualized_return(total_return, days)
        
        # 日收益率
        daily_returns = self.calculate_daily_returns(portfolio_values)
        
        # 风险指标
        volatility = self.calculate_volatility(daily_returns)
        max_dd, peak_idx, trough_idx = self.calculate_max_drawdown(portfolio_values)
        var_95 = self.calculate_var(daily_returns, 0.95)
        cvar_95 = self.calculate_cvar(daily_returns, 0.95)
        
        # 风险调整收益
        sharpe = self.calculate_sharpe_ratio(daily_returns)
        sortino = self.calculate_sortino_ratio(daily_returns)
        calmar = self.calculate_calmar_ratio(annualized_return, max_dd)
        
        report = {
            "summary": {
                "initial_value": initial_value,
                "final_value": final_value,
                "total_return": f"{total_return:.2%}",
                "annualized_return": f"{annualized_return:.2%}",
                "trading_days": days
            },
            "risk_metrics": {
                "volatility": f"{volatility:.2%}",
                "max_drawdown": f"{max_dd:.2%}",
                "var_95": f"{var_95:.2%}",
                "cvar_95": f"{cvar_95:.2%}"
            },
            "risk_adjusted_returns": {
                "sharpe_ratio": round(sharpe, 3),
                "sortino_ratio": round(sortino, 3),
                "calmar_ratio": round(calmar, 3)
            }
        }
        
        # 交易统计
        if trades:
            trade_stats = self.analyze_trades(trades)
            report["trade_statistics"] = {
                "total_trades": trade_stats["total_trades"],
                "win_rate": f"{trade_stats['win_rate']:.1%}",
                "profit_factor": round(trade_stats["profit_factor"], 2),
                "avg_trade_pnl": f"${trade_stats['avg_trade_pnl']:.2f}",
                "net_profit": f"${trade_stats['net_profit']:.2f}"
            }
        
        # 基准对比
        if benchmark_values and len(benchmark_values) == len(portfolio_values):
            benchmark_returns = self.calculate_daily_returns(benchmark_values)
            info_ratio = self.calculate_information_ratio(daily_returns, benchmark_returns)
            
            benchmark_total_return = self.calculate_total_return(
                benchmark_values[0], benchmark_values[-1]
            )
            alpha = total_return - benchmark_total_return
            
            report["benchmark_comparison"] = {
                "benchmark_return": f"{benchmark_total_return:.2%}",
                "alpha": f"{alpha:.2%}",
                "information_ratio": round(info_ratio, 3)
            }
        
        return report


# ==================== 便捷函数 ====================

def load_position_history(
    signature: str,
    data_path: str = "./data/agent_data"
) -> Tuple[List[Dict], List[float]]:
    """
    从持仓文件加载历史数据
    
    Args:
        signature: Agent 签名
        data_path: 数据路径
        
    Returns:
        (交易记录列表, 每日资产价值列表)
    """
    position_file = Path(data_path) / signature / "position" / "position.jsonl"
    
    if not position_file.exists():
        return [], []
    
    trades = []
    daily_values = []
    
    with open(position_file, "r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                
                # 提取交易信息
                action = record.get("this_action", {})
                if action.get("action") in ["buy", "sell"]:
                    trades.append({
                        "date": record.get("date"),
                        "action": action.get("action"),
                        "symbol": action.get("symbol"),
                        "amount": action.get("amount"),
                        "price": action.get("price"),
                        "pnl_amount": action.get("pnl_amount", 0)
                    })
                
                # 计算资产价值（简化：只用现金，实际应该加上持仓市值）
                positions = record.get("positions", {})
                cash = positions.get("CASH", 0)
                daily_values.append(cash)  # 简化版本
                
            except Exception:
                continue
    
    return trades, daily_values


def quick_performance_summary(
    signature: str,
    data_path: str = "./data/agent_data"
) -> Dict[str, Any]:
    """
    快速生成性能摘要
    
    Args:
        signature: Agent 签名
        data_path: 数据路径
        
    Returns:
        性能摘要
    """
    trades, values = load_position_history(signature, data_path)
    
    if not values:
        return {"error": f"No data found for {signature}"}
    
    analyzer = PerformanceAnalyzer()
    return analyzer.generate_performance_report(values, trades)


if __name__ == "__main__":
    # 测试代码
    analyzer = PerformanceAnalyzer()
    
    # 模拟数据
    portfolio_values = [10000]
    for i in range(100):
        change = portfolio_values[-1] * (0.001 + 0.02 * (0.5 - (i % 10) / 10))
        portfolio_values.append(portfolio_values[-1] + change)
    
    # 生成报告
    report = analyzer.generate_performance_report(portfolio_values)
    print(json.dumps(report, indent=2, ensure_ascii=False))
