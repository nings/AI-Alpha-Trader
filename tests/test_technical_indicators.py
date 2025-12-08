"""
技术指标模块单元测试
"""

import pytest
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from tools.technical_indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands
)


class TestSMA:
    """测试简单移动平均线"""
    
    def test_sma_basic(self):
        """测试基本 SMA 计算"""
        prices = [10, 11, 12, 13, 14]
        sma = calculate_sma(prices, 5)
        
        assert sma == 12.0  # (10+11+12+13+14) / 5
    
    def test_sma_insufficient_data(self):
        """测试数据不足"""
        prices = [10, 11, 12]
        sma = calculate_sma(prices, 5)
        
        assert sma is None
    
    def test_sma_uses_last_n_prices(self):
        """测试 SMA 使用最后 N 个价格"""
        prices = [1, 2, 3, 10, 11, 12, 13, 14]
        sma = calculate_sma(prices, 5)
        
        assert sma == 12.0  # (10+11+12+13+14) / 5


class TestEMA:
    """测试指数移动平均线"""
    
    def test_ema_basic(self):
        """测试基本 EMA 计算"""
        prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        ema = calculate_ema(prices, 5)
        
        assert ema is not None
        # EMA 应该比 SMA 更接近最近的价格
        sma = calculate_sma(prices, 5)
        assert ema >= sma  # 上涨趋势中 EMA >= SMA
    
    def test_ema_insufficient_data(self):
        """测试数据不足"""
        prices = [10, 11, 12]
        ema = calculate_ema(prices, 5)
        
        assert ema is None
    
    def test_ema_uptrend(self):
        """测试上涨趋势中的 EMA"""
        # 持续上涨的价格
        prices = list(range(100, 130))
        ema = calculate_ema(prices, 10)
        
        assert ema is not None
        # EMA 应该接近最近的价格
        assert ema > 120


class TestRSI:
    """测试相对强弱指标"""
    
    def test_rsi_overbought(self):
        """测试超买状态"""
        # 持续上涨的价格
        prices = [100 + i * 2 for i in range(20)]
        rsi = calculate_rsi(prices, 14)
        
        assert rsi is not None
        assert rsi > 70  # 超买
    
    def test_rsi_oversold(self):
        """测试超卖状态"""
        # 持续下跌的价格
        prices = [100 - i * 2 for i in range(20)]
        rsi = calculate_rsi(prices, 14)
        
        assert rsi is not None
        assert rsi < 30  # 超卖
    
    def test_rsi_neutral(self):
        """测试中性状态"""
        # 震荡的价格
        prices = [100, 102, 101, 103, 102, 104, 103, 105, 104, 106, 105, 107, 106, 108, 107, 109]
        rsi = calculate_rsi(prices, 14)
        
        assert rsi is not None
        assert 30 < rsi < 70  # 中性区域
    
    def test_rsi_insufficient_data(self):
        """测试数据不足"""
        prices = [100, 101, 102]
        rsi = calculate_rsi(prices, 14)
        
        assert rsi is None
    
    def test_rsi_all_gains(self):
        """测试全部上涨（RSI = 100）"""
        prices = list(range(100, 120))
        rsi = calculate_rsi(prices, 14)
        
        assert rsi == 100


class TestMACD:
    """测试 MACD 指标"""
    
    def test_macd_basic(self):
        """测试基本 MACD 计算"""
        # 需要足够的数据 (26 + 9 = 35 天)
        prices = list(range(100, 150))
        result = calculate_macd(prices)
        
        assert result is not None
        macd_line, signal_line, histogram = result
        assert isinstance(macd_line, float)
        assert isinstance(signal_line, float)
        assert isinstance(histogram, float)
    
    def test_macd_insufficient_data(self):
        """测试数据不足"""
        prices = list(range(100, 120))  # 只有 20 天
        result = calculate_macd(prices)
        
        assert result is None
    
    def test_macd_uptrend(self):
        """测试上涨趋势中的 MACD"""
        # 强劲上涨
        prices = [100 + i * 1.5 for i in range(50)]
        result = calculate_macd(prices)
        
        assert result is not None
        macd_line, signal_line, histogram = result
        # 上涨趋势中 MACD 应该为正
        assert macd_line > 0
    
    def test_macd_downtrend(self):
        """测试下跌趋势中的 MACD"""
        # 持续下跌
        prices = [200 - i * 1.5 for i in range(50)]
        result = calculate_macd(prices)
        
        assert result is not None
        macd_line, signal_line, histogram = result
        # 下跌趋势中 MACD 应该为负
        assert macd_line < 0


class TestBollingerBands:
    """测试布林带"""
    
    def test_bollinger_basic(self):
        """测试基本布林带计算"""
        prices = list(range(100, 130))
        result = calculate_bollinger_bands(prices, 20)
        
        assert result is not None
        upper, middle, lower = result
        
        # 上轨 > 中轨 > 下轨
        assert upper > middle > lower
    
    def test_bollinger_insufficient_data(self):
        """测试数据不足"""
        prices = list(range(100, 110))  # 只有 10 天
        result = calculate_bollinger_bands(prices, 20)
        
        assert result is None
    
    def test_bollinger_middle_is_sma(self):
        """测试中轨等于 SMA"""
        prices = list(range(100, 130))
        result = calculate_bollinger_bands(prices, 20)
        sma = calculate_sma(prices, 20)
        
        assert result is not None
        upper, middle, lower = result
        assert middle == sma
    
    def test_bollinger_width_increases_with_volatility(self):
        """测试波动性增加时布林带宽度增加"""
        # 低波动
        low_vol_prices = [100 + (i % 2) for i in range(30)]
        low_vol_result = calculate_bollinger_bands(low_vol_prices, 20)
        
        # 高波动
        high_vol_prices = [100 + (i % 2) * 10 for i in range(30)]
        high_vol_result = calculate_bollinger_bands(high_vol_prices, 20)
        
        assert low_vol_result is not None
        assert high_vol_result is not None
        
        low_vol_width = low_vol_result[0] - low_vol_result[2]
        high_vol_width = high_vol_result[0] - high_vol_result[2]
        
        assert high_vol_width > low_vol_width


class TestIndicatorEdgeCases:
    """测试边界情况"""
    
    def test_empty_prices(self):
        """测试空价格列表"""
        assert calculate_sma([], 5) is None
        assert calculate_ema([], 5) is None
        assert calculate_rsi([], 14) is None
        assert calculate_macd([]) is None
        assert calculate_bollinger_bands([], 20) is None
    
    def test_single_price(self):
        """测试单个价格"""
        assert calculate_sma([100], 5) is None
        assert calculate_ema([100], 5) is None
        assert calculate_rsi([100], 14) is None
    
    def test_negative_prices(self):
        """测试负价格（虽然不现实但应该能处理）"""
        prices = [-10, -9, -8, -7, -6, -5, -4, -3, -2, -1]
        sma = calculate_sma(prices, 5)
        
        assert sma is not None
        assert sma == -3.0  # (-5-4-3-2-1) / 5
    
    def test_constant_prices(self):
        """测试恒定价格"""
        prices = [100] * 30
        
        sma = calculate_sma(prices, 20)
        assert sma == 100
        
        ema = calculate_ema(prices, 12)
        assert ema == 100
        
        bb_result = calculate_bollinger_bands(prices, 20)
        assert bb_result is not None
        upper, middle, lower = bb_result
        # 恒定价格时，上轨 = 中轨 = 下轨
        assert upper == middle == lower == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
