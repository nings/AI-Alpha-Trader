"""
风险管理模块单元测试
"""

import pytest
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from tools.risk_management import (
    RiskManager,
    create_default_risk_manager,
    create_conservative_risk_manager,
    create_aggressive_risk_manager
)


class TestRiskManagerInit:
    """测试风险管理器初始化"""
    
    def test_default_init(self):
        """测试默认参数初始化"""
        rm = RiskManager()
        assert rm.max_position_pct == 0.25
        assert rm.stop_loss_pct == 0.08
        assert rm.take_profit_pct == 0.20
        assert rm.max_drawdown_pct == 0.15
        assert rm.max_daily_trades == 10
        assert rm.min_cash_reserve_pct == 0.05
    
    def test_custom_init(self):
        """测试自定义参数初始化"""
        rm = RiskManager(
            max_position_pct=0.30,
            stop_loss_pct=0.10,
            take_profit_pct=0.25
        )
        assert rm.max_position_pct == 0.30
        assert rm.stop_loss_pct == 0.10
        assert rm.take_profit_pct == 0.25
    
    def test_factory_functions(self):
        """测试工厂函数"""
        default_rm = create_default_risk_manager()
        assert default_rm.max_position_pct == 0.25
        
        conservative_rm = create_conservative_risk_manager()
        assert conservative_rm.max_position_pct == 0.15
        assert conservative_rm.stop_loss_pct == 0.05
        
        aggressive_rm = create_aggressive_risk_manager()
        assert aggressive_rm.max_position_pct == 0.35
        assert aggressive_rm.stop_loss_pct == 0.12


class TestPositionLimit:
    """测试仓位限制功能"""
    
    def test_position_within_limit(self):
        """测试仓位在限制范围内"""
        rm = RiskManager(max_position_pct=0.25)
        
        allowed, msg = rm.check_position_limit(
            symbol="AAPL",
            current_position_value=1000,
            proposed_buy_value=500,
            total_portfolio_value=10000
        )
        
        assert allowed is True
        assert "通过" in msg
    
    def test_position_exceeds_limit(self):
        """测试仓位超过限制"""
        rm = RiskManager(max_position_pct=0.25)
        
        allowed, msg = rm.check_position_limit(
            symbol="AAPL",
            current_position_value=2000,
            proposed_buy_value=1000,
            total_portfolio_value=10000
        )
        
        assert allowed is False
        assert "超过" in msg or "限制" in msg
    
    def test_position_at_limit(self):
        """测试仓位刚好在限制边界"""
        rm = RiskManager(max_position_pct=0.25)
        
        allowed, msg = rm.check_position_limit(
            symbol="AAPL",
            current_position_value=2000,
            proposed_buy_value=500,
            total_portfolio_value=10000
        )
        
        assert allowed is True
    
    def test_calculate_max_buy_amount(self):
        """测试计算最大可买入数量"""
        rm = RiskManager(max_position_pct=0.25)
        
        max_shares = rm.calculate_max_buy_amount(
            symbol="AAPL",
            current_position_value=1000,
            total_portfolio_value=10000,
            stock_price=100
        )
        
        # 最大仓位 = 10000 * 0.25 = 2500
        # 可用额度 = 2500 - 1000 = 1500
        # 最大股数 = 1500 / 100 = 15
        assert max_shares == 15
    
    def test_invalid_portfolio_value(self):
        """测试无效的组合价值"""
        rm = RiskManager()
        
        allowed, msg = rm.check_position_limit(
            symbol="AAPL",
            current_position_value=1000,
            proposed_buy_value=500,
            total_portfolio_value=0
        )
        
        assert allowed is False


class TestStopLossTakeProfit:
    """测试止损止盈功能"""
    
    def test_stop_loss_triggered(self):
        """测试止损触发"""
        rm = RiskManager(stop_loss_pct=0.08)
        rm.set_entry_price("AAPL", 100.0)
        
        triggered, loss_pct, msg = rm.check_stop_loss("AAPL", 90.0)
        
        assert triggered is True
        assert loss_pct >= 0.08
        assert "止损" in msg
    
    def test_stop_loss_not_triggered(self):
        """测试止损未触发"""
        rm = RiskManager(stop_loss_pct=0.08)
        rm.set_entry_price("AAPL", 100.0)
        
        triggered, loss_pct, msg = rm.check_stop_loss("AAPL", 95.0)
        
        assert triggered is False
        assert loss_pct < 0.08
    
    def test_take_profit_triggered(self):
        """测试止盈触发"""
        rm = RiskManager(take_profit_pct=0.20)
        rm.set_entry_price("AAPL", 100.0)
        
        triggered, profit_pct, msg = rm.check_take_profit("AAPL", 125.0)
        
        assert triggered is True
        assert profit_pct >= 0.20
        assert "止盈" in msg
    
    def test_take_profit_not_triggered(self):
        """测试止盈未触发"""
        rm = RiskManager(take_profit_pct=0.20)
        rm.set_entry_price("AAPL", 100.0)
        
        triggered, profit_pct, msg = rm.check_take_profit("AAPL", 115.0)
        
        assert triggered is False
        assert profit_pct < 0.20
    
    def test_combined_check(self):
        """测试综合止损止盈检查"""
        rm = RiskManager(stop_loss_pct=0.08, take_profit_pct=0.20)
        rm.set_entry_price("AAPL", 100.0)
        
        # 测试止损
        result = rm.check_stop_loss_take_profit("AAPL", 90.0)
        assert result["should_sell"] is True
        assert result["trigger_type"] == "stop_loss"
        
        # 测试止盈
        result = rm.check_stop_loss_take_profit("AAPL", 125.0)
        assert result["should_sell"] is True
        assert result["trigger_type"] == "take_profit"
        
        # 测试正常
        result = rm.check_stop_loss_take_profit("AAPL", 105.0)
        assert result["should_sell"] is False
        assert result["trigger_type"] is None
    
    def test_entry_price_management(self):
        """测试入场价格管理"""
        rm = RiskManager()
        
        # 设置入场价格
        rm.set_entry_price("AAPL", 150.0)
        assert rm.get_entry_price("AAPL") == 150.0
        
        # 清除入场价格
        rm.clear_entry_price("AAPL")
        assert rm.get_entry_price("AAPL") is None
    
    def test_no_entry_price(self):
        """测试无入场价格记录"""
        rm = RiskManager()
        
        triggered, loss_pct, msg = rm.check_stop_loss("AAPL", 100.0)
        
        assert triggered is False
        assert "无入场价格" in msg


class TestDrawdownControl:
    """测试回撤控制功能"""
    
    def test_update_peak_value(self):
        """测试更新峰值"""
        rm = RiskManager()
        
        rm.update_peak_value(10000)
        assert rm._peak_portfolio_value == 10000
        
        rm.update_peak_value(11000)
        assert rm._peak_portfolio_value == 11000
        
        # 低于峰值不更新
        rm.update_peak_value(10500)
        assert rm._peak_portfolio_value == 11000
    
    def test_calculate_drawdown(self):
        """测试计算回撤"""
        rm = RiskManager()
        rm.update_peak_value(10000)
        
        drawdown = rm.calculate_drawdown(9000)
        assert drawdown == 0.10  # 10% 回撤
        
        drawdown = rm.calculate_drawdown(8500)
        assert drawdown == 0.15  # 15% 回撤
    
    def test_max_drawdown_exceeded(self):
        """测试超过最大回撤"""
        rm = RiskManager(max_drawdown_pct=0.15)
        rm.update_peak_value(10000)
        
        exceeded, drawdown, msg = rm.check_max_drawdown(8400)
        
        assert exceeded is True
        assert drawdown >= 0.15
        assert "超过" in msg or "回撤" in msg
    
    def test_max_drawdown_not_exceeded(self):
        """测试未超过最大回撤"""
        rm = RiskManager(max_drawdown_pct=0.15)
        rm.update_peak_value(10000)
        
        exceeded, drawdown, msg = rm.check_max_drawdown(9000)
        
        assert exceeded is False
        assert drawdown < 0.15


class TestTradeFrequency:
    """测试交易频率控制"""
    
    def test_record_trade(self):
        """测试记录交易"""
        rm = RiskManager()
        
        rm.record_trade("2025-01-20")
        assert rm.get_daily_trade_count("2025-01-20") == 1
        
        rm.record_trade("2025-01-20")
        assert rm.get_daily_trade_count("2025-01-20") == 2
    
    def test_trade_frequency_within_limit(self):
        """测试交易频率在限制内"""
        rm = RiskManager(max_daily_trades=10)
        
        for _ in range(5):
            rm.record_trade("2025-01-20")
        
        allowed, msg = rm.check_trade_frequency("2025-01-20")
        assert allowed is True
    
    def test_trade_frequency_exceeded(self):
        """测试交易频率超限"""
        rm = RiskManager(max_daily_trades=10)
        
        for _ in range(10):
            rm.record_trade("2025-01-20")
        
        allowed, msg = rm.check_trade_frequency("2025-01-20")
        assert allowed is False
        assert "超过" in msg or "限制" in msg


class TestCashReserve:
    """测试现金储备检查"""
    
    def test_cash_reserve_sufficient(self):
        """测试现金储备充足"""
        rm = RiskManager(min_cash_reserve_pct=0.05)
        
        allowed, msg = rm.check_cash_reserve(
            cash_balance=2000,
            total_portfolio_value=10000,
            proposed_buy_value=1000
        )
        
        assert allowed is True
    
    def test_cash_reserve_insufficient(self):
        """测试现金储备不足"""
        rm = RiskManager(min_cash_reserve_pct=0.05)
        
        allowed, msg = rm.check_cash_reserve(
            cash_balance=600,
            total_portfolio_value=10000,
            proposed_buy_value=500
        )
        
        # 买入后剩余 100，低于 10000 * 0.05 = 500
        assert allowed is False
        assert "储备" in msg or "现金" in msg


class TestPreTradeCheck:
    """测试交易前综合检查"""
    
    def test_buy_check_pass(self, sample_position):
        """测试买入检查通过"""
        rm = RiskManager()
        
        result = rm.pre_trade_check(
            action="buy",
            symbol="NVDA",
            amount=5,
            price=500,
            current_position=sample_position,
            date="2025-01-20"
        )
        
        assert result["allowed"] is True
        assert len(result["errors"]) == 0
    
    def test_buy_check_insufficient_cash(self, sample_position):
        """测试买入现金不足"""
        rm = RiskManager()
        
        result = rm.pre_trade_check(
            action="buy",
            symbol="NVDA",
            amount=20,  # 20 * 500 = 10000 > 5000 现金
            price=500,
            current_position=sample_position,
            date="2025-01-20"
        )
        
        assert result["allowed"] is False
        assert len(result["errors"]) > 0
    
    def test_sell_check_pass(self, sample_position):
        """测试卖出检查通过"""
        rm = RiskManager()
        
        result = rm.pre_trade_check(
            action="sell",
            symbol="AAPL",
            amount=5,
            price=150,
            current_position=sample_position,
            date="2025-01-20"
        )
        
        assert result["allowed"] is True
    
    def test_sell_check_insufficient_shares(self, sample_position):
        """测试卖出股票不足"""
        rm = RiskManager()
        
        result = rm.pre_trade_check(
            action="sell",
            symbol="AAPL",
            amount=20,  # 只有 10 股
            price=150,
            current_position=sample_position,
            date="2025-01-20"
        )
        
        assert result["allowed"] is False


class TestRiskSummary:
    """测试风险摘要"""
    
    def test_get_risk_summary(self, sample_position, sample_prices):
        """测试获取风险摘要"""
        rm = RiskManager()
        rm.update_peak_value(10000)
        
        summary = rm.get_risk_summary(
            current_position=sample_position,
            prices=sample_prices,
            initial_cash=10000
        )
        
        assert "total_value" in summary
        assert "cash" in summary
        assert "positions" in summary
        assert "current_drawdown" in summary
        assert "risk_level" in summary
    
    def test_reset(self):
        """测试重置风险管理器"""
        rm = RiskManager()
        
        rm.set_entry_price("AAPL", 150.0)
        rm.update_peak_value(10000)
        rm.record_trade("2025-01-20")
        
        rm.reset()
        
        assert rm.get_entry_price("AAPL") is None
        assert rm._peak_portfolio_value == 0.0
        assert rm.get_daily_trade_count("2025-01-20") == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
