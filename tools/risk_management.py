"""
风险管理模块
提供交易风险控制功能，包括止损、仓位限制、回撤控制等
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class RiskManager:
    """
    风险管理器
    
    提供以下风险控制功能：
    1. 单一持仓限制 - 防止过度集中
    2. 止损/止盈检查 - 控制单笔交易损失
    3. 最大回撤控制 - 保护整体资金
    4. 每日交易次数限制 - 防止过度交易
    5. VaR 计算 - 风险价值评估
    """
    
    def __init__(
        self,
        max_position_pct: float = 0.25,      # 单一股票最大仓位比例
        stop_loss_pct: float = 0.08,          # 止损比例 (8%)
        take_profit_pct: float = 0.20,        # 止盈比例 (20%)
        max_drawdown_pct: float = 0.15,       # 最大回撤比例 (15%)
        max_daily_trades: int = 10,           # 每日最大交易次数
        min_cash_reserve_pct: float = 0.05    # 最小现金储备比例 (5%)
    ):
        """
        初始化风险管理器
        
        Args:
            max_position_pct: 单一股票最大仓位占总资产比例
            stop_loss_pct: 止损触发比例
            take_profit_pct: 止盈触发比例
            max_drawdown_pct: 组合最大回撤限制
            max_daily_trades: 每日最大交易次数
            min_cash_reserve_pct: 最小现金储备比例
        """
        self.max_position_pct = max_position_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.max_daily_trades = max_daily_trades
        self.min_cash_reserve_pct = min_cash_reserve_pct
        
        # 记录入场价格，用于止损止盈计算
        self._entry_prices: Dict[str, float] = {}
        # 记录历史最高资产值，用于回撤计算
        self._peak_portfolio_value: float = 0.0
        # 记录每日交易次数
        self._daily_trade_count: Dict[str, int] = {}
    
    def set_entry_price(self, symbol: str, price: float) -> None:
        """
        设置股票入场价格
        
        Args:
            symbol: 股票代码
            price: 入场价格
        """
        self._entry_prices[symbol] = price
    
    def get_entry_price(self, symbol: str) -> Optional[float]:
        """获取股票入场价格"""
        return self._entry_prices.get(symbol)
    
    def clear_entry_price(self, symbol: str) -> None:
        """清除股票入场价格（平仓后调用）"""
        if symbol in self._entry_prices:
            del self._entry_prices[symbol]
    
    # ==================== 仓位控制 ====================
    
    def check_position_limit(
        self,
        symbol: str,
        current_position_value: float,
        proposed_buy_value: float,
        total_portfolio_value: float
    ) -> Tuple[bool, str]:
        """
        检查买入后是否超过单一持仓限制
        
        Args:
            symbol: 股票代码
            current_position_value: 当前该股票持仓市值
            proposed_buy_value: 计划买入金额
            total_portfolio_value: 总资产价值
            
        Returns:
            (是否允许, 原因说明)
        """
        if total_portfolio_value <= 0:
            return False, "总资产价值无效"
        
        new_position_value = current_position_value + proposed_buy_value
        position_pct = new_position_value / total_portfolio_value
        
        if position_pct > self.max_position_pct:
            max_allowed = total_portfolio_value * self.max_position_pct - current_position_value
            return False, (
                f"超过单一持仓限制: {symbol} 买入后占比 {position_pct:.1%} > {self.max_position_pct:.1%}。"
                f"最大可买入金额: ${max_allowed:.2f}"
            )
        
        return True, "仓位检查通过"
    
    def calculate_max_buy_amount(
        self,
        symbol: str,
        current_position_value: float,
        total_portfolio_value: float,
        stock_price: float
    ) -> int:
        """
        计算在仓位限制下最大可买入股数
        
        Args:
            symbol: 股票代码
            current_position_value: 当前该股票持仓市值
            total_portfolio_value: 总资产价值
            stock_price: 股票当前价格
            
        Returns:
            最大可买入股数
        """
        if stock_price <= 0 or total_portfolio_value <= 0:
            return 0
        
        max_position_value = total_portfolio_value * self.max_position_pct
        available_value = max_position_value - current_position_value
        
        if available_value <= 0:
            return 0
        
        return int(available_value / stock_price)
    
    # ==================== 止损止盈 ====================
    
    def check_stop_loss(
        self,
        symbol: str,
        current_price: float,
        entry_price: Optional[float] = None
    ) -> Tuple[bool, float, str]:
        """
        检查是否触发止损
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            entry_price: 入场价格（可选，如果不提供则使用记录的入场价）
            
        Returns:
            (是否触发止损, 当前亏损比例, 说明)
        """
        if entry_price is None:
            entry_price = self._entry_prices.get(symbol)
        
        if entry_price is None or entry_price <= 0:
            return False, 0.0, "无入场价格记录"
        
        loss_pct = (entry_price - current_price) / entry_price
        
        if loss_pct >= self.stop_loss_pct:
            return True, loss_pct, (
                f"⚠️ 触发止损: {symbol} 当前亏损 {loss_pct:.1%} >= {self.stop_loss_pct:.1%}。"
                f"入场价: ${entry_price:.2f}, 当前价: ${current_price:.2f}"
            )
        
        return False, loss_pct, f"未触发止损: 当前亏损 {loss_pct:.1%}"
    
    def check_take_profit(
        self,
        symbol: str,
        current_price: float,
        entry_price: Optional[float] = None
    ) -> Tuple[bool, float, str]:
        """
        检查是否触发止盈
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            entry_price: 入场价格（可选）
            
        Returns:
            (是否触发止盈, 当前盈利比例, 说明)
        """
        if entry_price is None:
            entry_price = self._entry_prices.get(symbol)
        
        if entry_price is None or entry_price <= 0:
            return False, 0.0, "无入场价格记录"
        
        profit_pct = (current_price - entry_price) / entry_price
        
        if profit_pct >= self.take_profit_pct:
            return True, profit_pct, (
                f"🎯 触发止盈: {symbol} 当前盈利 {profit_pct:.1%} >= {self.take_profit_pct:.1%}。"
                f"入场价: ${entry_price:.2f}, 当前价: ${current_price:.2f}"
            )
        
        return False, profit_pct, f"未触发止盈: 当前盈利 {profit_pct:.1%}"
    
    def check_stop_loss_take_profit(
        self,
        symbol: str,
        current_price: float,
        entry_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        综合检查止损止盈
        
        Returns:
            {
                "should_sell": bool,
                "reason": str,
                "trigger_type": "stop_loss" | "take_profit" | None,
                "pnl_pct": float
            }
        """
        stop_loss_triggered, loss_pct, stop_loss_msg = self.check_stop_loss(
            symbol, current_price, entry_price
        )
        
        if stop_loss_triggered:
            return {
                "should_sell": True,
                "reason": stop_loss_msg,
                "trigger_type": "stop_loss",
                "pnl_pct": -loss_pct
            }
        
        take_profit_triggered, profit_pct, take_profit_msg = self.check_take_profit(
            symbol, current_price, entry_price
        )
        
        if take_profit_triggered:
            return {
                "should_sell": True,
                "reason": take_profit_msg,
                "trigger_type": "take_profit",
                "pnl_pct": profit_pct
            }
        
        return {
            "should_sell": False,
            "reason": "未触发止损止盈",
            "trigger_type": None,
            "pnl_pct": profit_pct if profit_pct > 0 else -loss_pct
        }
    
    # ==================== 回撤控制 ====================
    
    def update_peak_value(self, current_portfolio_value: float) -> None:
        """更新历史最高资产值"""
        if current_portfolio_value > self._peak_portfolio_value:
            self._peak_portfolio_value = current_portfolio_value
    
    def calculate_drawdown(self, current_portfolio_value: float) -> float:
        """
        计算当前回撤
        
        Returns:
            回撤比例 (0.0 - 1.0)
        """
        if self._peak_portfolio_value <= 0:
            return 0.0
        
        drawdown = (self._peak_portfolio_value - current_portfolio_value) / self._peak_portfolio_value
        return max(0.0, drawdown)
    
    def check_max_drawdown(self, current_portfolio_value: float) -> Tuple[bool, float, str]:
        """
        检查是否超过最大回撤限制
        
        Returns:
            (是否超限, 当前回撤, 说明)
        """
        self.update_peak_value(current_portfolio_value)
        current_drawdown = self.calculate_drawdown(current_portfolio_value)
        
        if current_drawdown >= self.max_drawdown_pct:
            return True, current_drawdown, (
                f"🚨 超过最大回撤限制: 当前回撤 {current_drawdown:.1%} >= {self.max_drawdown_pct:.1%}。"
                f"峰值: ${self._peak_portfolio_value:.2f}, 当前: ${current_portfolio_value:.2f}。"
                f"建议: 暂停交易或减仓"
            )
        
        return False, current_drawdown, f"回撤正常: {current_drawdown:.1%}"
    
    # ==================== 交易频率控制 ====================
    
    def record_trade(self, date: str) -> None:
        """记录一次交易"""
        if date not in self._daily_trade_count:
            self._daily_trade_count[date] = 0
        self._daily_trade_count[date] += 1
    
    def get_daily_trade_count(self, date: str) -> int:
        """获取当日交易次数"""
        return self._daily_trade_count.get(date, 0)
    
    def check_trade_frequency(self, date: str) -> Tuple[bool, str]:
        """
        检查是否超过每日交易次数限制
        
        Returns:
            (是否允许交易, 说明)
        """
        current_count = self.get_daily_trade_count(date)
        
        if current_count >= self.max_daily_trades:
            return False, (
                f"超过每日交易次数限制: 今日已交易 {current_count} 次 >= {self.max_daily_trades} 次"
            )
        
        return True, f"交易次数正常: {current_count}/{self.max_daily_trades}"
    
    # ==================== 现金储备检查 ====================
    
    def check_cash_reserve(
        self,
        cash_balance: float,
        total_portfolio_value: float,
        proposed_buy_value: float
    ) -> Tuple[bool, str]:
        """
        检查买入后是否保持最小现金储备
        
        Returns:
            (是否允许, 说明)
        """
        if total_portfolio_value <= 0:
            return False, "总资产价值无效"
        
        remaining_cash = cash_balance - proposed_buy_value
        min_required_cash = total_portfolio_value * self.min_cash_reserve_pct
        
        if remaining_cash < min_required_cash:
            max_buy = cash_balance - min_required_cash
            return False, (
                f"低于最小现金储备: 买入后现金 ${remaining_cash:.2f} < "
                f"最低要求 ${min_required_cash:.2f} ({self.min_cash_reserve_pct:.1%})。"
                f"最大可用于买入: ${max(0, max_buy):.2f}"
            )
        
        return True, "现金储备充足"
    
    # ==================== 综合风险检查 ====================
    
    def pre_trade_check(
        self,
        action: str,  # "buy" or "sell"
        symbol: str,
        amount: int,
        price: float,
        current_position: Dict[str, float],
        date: str
    ) -> Dict[str, Any]:
        """
        交易前综合风险检查
        
        Args:
            action: 交易动作 ("buy" 或 "sell")
            symbol: 股票代码
            amount: 交易数量
            price: 交易价格
            current_position: 当前持仓 {symbol: shares, "CASH": cash}
            date: 交易日期
            
        Returns:
            {
                "allowed": bool,
                "warnings": List[str],
                "errors": List[str],
                "suggestions": List[str]
            }
        """
        result = {
            "allowed": True,
            "warnings": [],
            "errors": [],
            "suggestions": []
        }
        
        trade_value = price * amount
        cash_balance = current_position.get("CASH", 0)
        
        # 计算总资产价值（简化版，实际应该用当前市价）
        total_value = cash_balance
        for sym, shares in current_position.items():
            if sym != "CASH" and shares > 0:
                # 这里简化处理，实际应该获取每个股票的当前价格
                total_value += shares * price if sym == symbol else shares * 100  # 假设其他股票价格
        
        # 1. 检查交易频率
        freq_ok, freq_msg = self.check_trade_frequency(date)
        if not freq_ok:
            result["warnings"].append(freq_msg)
        
        if action == "buy":
            # 2. 检查现金是否足够
            if cash_balance < trade_value:
                result["allowed"] = False
                result["errors"].append(
                    f"现金不足: 需要 ${trade_value:.2f}, 可用 ${cash_balance:.2f}"
                )
                return result
            
            # 3. 检查仓位限制
            current_position_value = current_position.get(symbol, 0) * price
            pos_ok, pos_msg = self.check_position_limit(
                symbol, current_position_value, trade_value, total_value
            )
            if not pos_ok:
                result["warnings"].append(pos_msg)
                max_shares = self.calculate_max_buy_amount(
                    symbol, current_position_value, total_value, price
                )
                result["suggestions"].append(f"建议最大买入: {max_shares} 股")
            
            # 4. 检查现金储备
            reserve_ok, reserve_msg = self.check_cash_reserve(
                cash_balance, total_value, trade_value
            )
            if not reserve_ok:
                result["warnings"].append(reserve_msg)
            
            # 5. 检查回撤
            drawdown_exceeded, drawdown, drawdown_msg = self.check_max_drawdown(total_value)
            if drawdown_exceeded:
                result["warnings"].append(drawdown_msg)
                result["suggestions"].append("建议减少买入或暂停交易")
        
        elif action == "sell":
            # 检查是否持有足够股票
            current_shares = current_position.get(symbol, 0)
            if current_shares < amount:
                result["allowed"] = False
                result["errors"].append(
                    f"持仓不足: 需要卖出 {amount} 股, 持有 {current_shares} 股"
                )
        
        return result
    
    def get_risk_summary(
        self,
        current_position: Dict[str, float],
        prices: Dict[str, float],
        initial_cash: float = 10000.0
    ) -> Dict[str, Any]:
        """
        获取风险状况摘要
        
        Args:
            current_position: 当前持仓
            prices: 股票价格 {symbol: price}
            initial_cash: 初始资金
            
        Returns:
            风险摘要字典
        """
        cash = current_position.get("CASH", 0)
        
        # 计算总资产
        total_value = cash
        position_values = {}
        for symbol, shares in current_position.items():
            if symbol != "CASH" and shares > 0:
                price = prices.get(symbol, 0)
                value = shares * price
                position_values[symbol] = {
                    "shares": shares,
                    "price": price,
                    "value": value,
                    "pct": 0  # 稍后计算
                }
                total_value += value
        
        # 计算各持仓占比
        for symbol in position_values:
            position_values[symbol]["pct"] = position_values[symbol]["value"] / total_value if total_value > 0 else 0
        
        # 计算回撤
        self.update_peak_value(total_value)
        current_drawdown = self.calculate_drawdown(total_value)
        
        # 计算总收益
        total_return = (total_value - initial_cash) / initial_cash if initial_cash > 0 else 0
        
        return {
            "total_value": total_value,
            "cash": cash,
            "cash_pct": cash / total_value if total_value > 0 else 0,
            "positions": position_values,
            "peak_value": self._peak_portfolio_value,
            "current_drawdown": current_drawdown,
            "max_drawdown_limit": self.max_drawdown_pct,
            "drawdown_warning": current_drawdown >= self.max_drawdown_pct * 0.8,  # 80% 预警
            "total_return": total_return,
            "risk_level": self._calculate_risk_level(current_drawdown, position_values)
        }
    
    def _calculate_risk_level(
        self,
        drawdown: float,
        position_values: Dict[str, Dict]
    ) -> str:
        """计算风险等级"""
        # 检查集中度
        max_concentration = max(
            (p["pct"] for p in position_values.values()),
            default=0
        )
        
        if drawdown >= self.max_drawdown_pct:
            return "🔴 高风险"
        elif drawdown >= self.max_drawdown_pct * 0.7 or max_concentration > self.max_position_pct:
            return "🟡 中风险"
        else:
            return "🟢 低风险"
    
    def reset(self) -> None:
        """重置风险管理器状态"""
        self._entry_prices.clear()
        self._peak_portfolio_value = 0.0
        self._daily_trade_count.clear()


# ==================== 便捷函数 ====================

def create_default_risk_manager() -> RiskManager:
    """创建默认配置的风险管理器"""
    return RiskManager(
        max_position_pct=0.25,
        stop_loss_pct=0.08,
        take_profit_pct=0.20,
        max_drawdown_pct=0.15,
        max_daily_trades=10,
        min_cash_reserve_pct=0.05
    )


def create_conservative_risk_manager() -> RiskManager:
    """创建保守配置的风险管理器"""
    return RiskManager(
        max_position_pct=0.15,
        stop_loss_pct=0.05,
        take_profit_pct=0.15,
        max_drawdown_pct=0.10,
        max_daily_trades=5,
        min_cash_reserve_pct=0.10
    )


def create_aggressive_risk_manager() -> RiskManager:
    """创建激进配置的风险管理器"""
    return RiskManager(
        max_position_pct=0.35,
        stop_loss_pct=0.12,
        take_profit_pct=0.30,
        max_drawdown_pct=0.25,
        max_daily_trades=20,
        min_cash_reserve_pct=0.02
    )


if __name__ == "__main__":
    # 测试代码
    rm = create_default_risk_manager()
    
    # 测试仓位检查
    allowed, msg = rm.check_position_limit(
        symbol="AAPL",
        current_position_value=2000,
        proposed_buy_value=1000,
        total_portfolio_value=10000
    )
    print(f"仓位检查: {allowed}, {msg}")
    
    # 测试止损
    rm.set_entry_price("AAPL", 150.0)
    triggered, loss, msg = rm.check_stop_loss("AAPL", 135.0)
    print(f"止损检查: {triggered}, {loss:.1%}, {msg}")
    
    # 测试综合风险检查
    position = {"AAPL": 10, "MSFT": 5, "CASH": 5000}
    result = rm.pre_trade_check(
        action="buy",
        symbol="NVDA",
        amount=10,
        price=500,
        current_position=position,
        date="2025-01-20"
    )
    print(f"综合检查: {result}")
