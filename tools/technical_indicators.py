"""
技术指标计算工具
提供常用的股票技术分析指标，包括移动平均线、RSI、MACD等
"""

import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def get_historical_prices(
    symbol: str,
    end_date: str,
    days: int = 30,
    merged_path: Optional[str] = None
) -> List[Dict[str, float]]:
    """
    获取指定股票的历史价格数据

    Args:
        symbol: 股票代码
        end_date: 结束日期 (YYYY-MM-DD)
        days: 需要获取的天数
        merged_path: 可选，自定义merged.jsonl路径

    Returns:
        价格数据列表，每个元素包含 {date, open, high, low, close, volume}
    """
    if merged_path is None:
        base_dir = Path(__file__).resolve().parents[1]
        merged_file = base_dir / "data" / "merged.jsonl"
    else:
        merged_file = Path(merged_path)

    if not merged_file.exists():
        return []

    # 生成需要查询的日期列表
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    dates_needed = []
    current_dt = end_dt

    while len(dates_needed) < days:
        # 只添加工作日
        if current_dt.weekday() < 5:  # 0-4 是周一到周五
            dates_needed.append(current_dt.strftime("%Y-%m-%d"))
        current_dt -= timedelta(days=1)

    dates_needed.reverse()  # 按时间顺序排列

    # 从merged.jsonl读取数据
    prices = []

    with merged_file.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
                meta = doc.get("Meta Data", {})
                sym = meta.get("2. Symbol")

                if sym != symbol:
                    continue

                series = doc.get("Time Series (Daily)", {})

                for date in dates_needed:
                    bar = series.get(date)
                    if bar:
                        prices.append({
                            "date": date,
                            "open": float(bar.get("1. buy price", 0)),
                            "high": float(bar.get("2. high", 0)),
                            "low": float(bar.get("3. low", 0)),
                            "close": float(bar.get("4. sell price", 0)),
                            "volume": float(bar.get("5. volume", 0))
                        })
                break  # 找到对应股票后退出

            except Exception as e:
                continue

    return prices


def calculate_sma(prices: List[float], period: int) -> Optional[float]:
    """
    计算简单移动平均线 (Simple Moving Average)

    Args:
        prices: 价格列表
        period: 周期（天数）

    Returns:
        SMA值，如果数据不足返回None
    """
    if len(prices) < period:
        return None

    return sum(prices[-period:]) / period


def calculate_ema(prices: List[float], period: int) -> Optional[float]:
    """
    计算指数移动平均线 (Exponential Moving Average)

    Args:
        prices: 价格列表
        period: 周期（天数）

    Returns:
        EMA值，如果数据不足返回None
    """
    if len(prices) < period:
        return None

    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period  # 初始EMA使用SMA

    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema

    return ema


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """
    计算相对强弱指标 (Relative Strength Index)

    Args:
        prices: 价格列表
        period: 周期（默认14天）

    Returns:
        RSI值 (0-100)，如果数据不足返回None
    """
    if len(prices) < period + 1:
        return None

    # 计算价格变化
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]

    # 分离涨跌
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    # 计算平均涨跌
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(
    prices: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Optional[Tuple[float, float, float]]:
    """
    计算MACD指标 (Moving Average Convergence Divergence)

    Args:
        prices: 价格列表
        fast_period: 快线周期（默认12）
        slow_period: 慢线周期（默认26）
        signal_period: 信号线周期（默认9）

    Returns:
        (MACD值, 信号线值, 柱状图值)，如果数据不足返回None
    """
    if len(prices) < slow_period + signal_period:
        return None

    # 计算快线和慢线EMA
    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)

    if fast_ema is None or slow_ema is None:
        return None

    # MACD线 = 快线EMA - 慢线EMA
    macd_line = fast_ema - slow_ema

    # 计算信号线（MACD的9日EMA）
    # 这里简化处理，实际应该用MACD历史值计算EMA
    macd_values = []
    for i in range(slow_period, len(prices)):
        fast = calculate_ema(prices[:i+1], fast_period)
        slow = calculate_ema(prices[:i+1], slow_period)
        if fast and slow:
            macd_values.append(fast - slow)

    if len(macd_values) < signal_period:
        signal_line = macd_line
    else:
        signal_line = calculate_ema(macd_values, signal_period) or macd_line

    # 柱状图 = MACD线 - 信号线
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    std_dev: float = 2.0
) -> Optional[Tuple[float, float, float]]:
    """
    计算布林带 (Bollinger Bands)

    Args:
        prices: 价格列表
        period: 周期（默认20天）
        std_dev: 标准差倍数（默认2）

    Returns:
        (上轨, 中轨, 下轨)，如果数据不足返回None
    """
    if len(prices) < period:
        return None

    # 中轨 = SMA
    middle_band = calculate_sma(prices, period)
    if middle_band is None:
        return None

    # 计算标准差
    recent_prices = prices[-period:]
    variance = sum((p - middle_band) ** 2 for p in recent_prices) / period
    std = variance ** 0.5

    # 上轨和下轨
    upper_band = middle_band + (std_dev * std)
    lower_band = middle_band - (std_dev * std)

    return upper_band, middle_band, lower_band


def get_technical_signals(
    symbol: str,
    end_date: str,
    merged_path: Optional[str] = None
) -> Dict[str, any]:
    """
    获取股票的技术分析信号

    Args:
        symbol: 股票代码
        end_date: 结束日期
        merged_path: 可选，自定义merged.jsonl路径

    Returns:
        包含各种技术指标和交易信号的字典
    """
    # 获取历史价格数据
    historical_data = get_historical_prices(symbol, end_date, days=50, merged_path=merged_path)

    if not historical_data:
        return {"error": f"No data found for {symbol}"}

    close_prices = [d["close"] for d in historical_data]

    # 计算各种技术指标
    sma_20 = calculate_sma(close_prices, 20)
    sma_50 = calculate_sma(close_prices, 50)
    ema_12 = calculate_ema(close_prices, 12)
    rsi = calculate_rsi(close_prices, 14)
    macd_result = calculate_macd(close_prices)
    bb_result = calculate_bollinger_bands(close_prices)

    # 生成交易信号
    signals = {
        "symbol": symbol,
        "date": end_date,
        "current_price": close_prices[-1] if close_prices else None,
        "indicators": {
            "sma_20": round(sma_20, 2) if sma_20 else None,
            "sma_50": round(sma_50, 2) if sma_50 else None,
            "ema_12": round(ema_12, 2) if ema_12 else None,
            "rsi": round(rsi, 2) if rsi else None,
        },
        "signals": {}
    }

    # MACD信号
    if macd_result:
        macd_line, signal_line, histogram = macd_result
        signals["indicators"]["macd"] = round(macd_line, 4)
        signals["indicators"]["macd_signal"] = round(signal_line, 4)
        signals["indicators"]["macd_histogram"] = round(histogram, 4)

        # MACD交易信号
        if histogram > 0 and macd_line > signal_line:
            signals["signals"]["macd"] = "买入"
        elif histogram < 0 and macd_line < signal_line:
            signals["signals"]["macd"] = "卖出"
        else:
            signals["signals"]["macd"] = "持有"

    # RSI信号
    if rsi:
        if rsi < 30:
            signals["signals"]["rsi"] = "超卖-买入"
        elif rsi > 70:
            signals["signals"]["rsi"] = "超买-卖出"
        else:
            signals["signals"]["rsi"] = "中性"

    # 移动平均线信号
    if sma_20 and sma_50 and close_prices:
        current_price = close_prices[-1]
        if current_price > sma_20 and sma_20 > sma_50:
            signals["signals"]["ma"] = "强势上涨-买入"
        elif current_price < sma_20 and sma_20 < sma_50:
            signals["signals"]["ma"] = "弱势下跌-卖出"
        else:
            signals["signals"]["ma"] = "震荡"

    # 布林带信号
    if bb_result and close_prices:
        upper, middle, lower = bb_result
        current_price = close_prices[-1]
        signals["indicators"]["bb_upper"] = round(upper, 2)
        signals["indicators"]["bb_middle"] = round(middle, 2)
        signals["indicators"]["bb_lower"] = round(lower, 2)

        if current_price <= lower:
            signals["signals"]["bollinger"] = "触及下轨-买入"
        elif current_price >= upper:
            signals["signals"]["bollinger"] = "触及上轨-卖出"
        else:
            signals["signals"]["bollinger"] = "在通道内"

    # 综合信号
    buy_signals = sum(1 for s in signals["signals"].values() if "买入" in str(s))
    sell_signals = sum(1 for s in signals["signals"].values() if "卖出" in str(s))

    if buy_signals > sell_signals and buy_signals >= 2:
        signals["recommendation"] = "买入"
    elif sell_signals > buy_signals and sell_signals >= 2:
        signals["recommendation"] = "卖出"
    else:
        signals["recommendation"] = "持有"

    return signals


# ==================== 新增技术指标 ====================

def calculate_atr(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    period: int = 14
) -> Optional[float]:
    """
    计算平均真实波幅 (Average True Range)
    
    ATR 用于衡量市场波动性
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        period: 周期（默认14天）
        
    Returns:
        ATR值，如果数据不足返回None
    """
    if len(high_prices) < period + 1 or len(low_prices) < period + 1 or len(close_prices) < period + 1:
        return None
    
    true_ranges = []
    for i in range(1, len(close_prices)):
        high = high_prices[i]
        low = low_prices[i]
        prev_close = close_prices[i - 1]
        
        # True Range = max(High - Low, |High - Prev Close|, |Low - Prev Close|)
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)
    
    if len(true_ranges) < period:
        return None
    
    # 使用 EMA 计算 ATR
    atr = sum(true_ranges[:period]) / period
    multiplier = 2 / (period + 1)
    
    for tr in true_ranges[period:]:
        atr = (tr - atr) * multiplier + atr
    
    return atr


def calculate_obv(
    close_prices: List[float],
    volumes: List[float]
) -> Optional[List[float]]:
    """
    计算能量潮指标 (On-Balance Volume)
    
    OBV 通过累计成交量来预测价格走势
    
    Args:
        close_prices: 收盘价列表
        volumes: 成交量列表
        
    Returns:
        OBV值列表，如果数据不足返回None
    """
    if len(close_prices) < 2 or len(volumes) < 2:
        return None
    
    if len(close_prices) != len(volumes):
        return None
    
    obv = [0]
    for i in range(1, len(close_prices)):
        if close_prices[i] > close_prices[i - 1]:
            obv.append(obv[-1] + volumes[i])
        elif close_prices[i] < close_prices[i - 1]:
            obv.append(obv[-1] - volumes[i])
        else:
            obv.append(obv[-1])
    
    return obv


def calculate_stochastic(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    k_period: int = 14,
    d_period: int = 3
) -> Optional[Tuple[float, float]]:
    """
    计算随机指标 (Stochastic Oscillator)
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        k_period: %K 周期（默认14）
        d_period: %D 周期（默认3）
        
    Returns:
        (%K, %D) 元组，如果数据不足返回None
    """
    if len(close_prices) < k_period + d_period:
        return None
    
    # 计算 %K 值序列
    k_values = []
    for i in range(k_period - 1, len(close_prices)):
        period_high = max(high_prices[i - k_period + 1:i + 1])
        period_low = min(low_prices[i - k_period + 1:i + 1])
        
        if period_high == period_low:
            k_values.append(50)  # 避免除零
        else:
            k = 100 * (close_prices[i] - period_low) / (period_high - period_low)
            k_values.append(k)
    
    if len(k_values) < d_period:
        return None
    
    # %K 是最新值
    k = k_values[-1]
    
    # %D 是 %K 的移动平均
    d = sum(k_values[-d_period:]) / d_period
    
    return k, d


def calculate_williams_r(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    period: int = 14
) -> Optional[float]:
    """
    计算威廉指标 (Williams %R)
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        period: 周期（默认14）
        
    Returns:
        Williams %R 值 (-100 到 0)
    """
    if len(close_prices) < period:
        return None
    
    period_high = max(high_prices[-period:])
    period_low = min(low_prices[-period:])
    current_close = close_prices[-1]
    
    if period_high == period_low:
        return -50
    
    williams_r = -100 * (period_high - current_close) / (period_high - period_low)
    return williams_r


def calculate_cci(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    period: int = 20
) -> Optional[float]:
    """
    计算商品通道指数 (Commodity Channel Index)
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        period: 周期（默认20）
        
    Returns:
        CCI 值
    """
    if len(close_prices) < period:
        return None
    
    # 计算典型价格 (Typical Price)
    typical_prices = []
    for i in range(len(close_prices)):
        tp = (high_prices[i] + low_prices[i] + close_prices[i]) / 3
        typical_prices.append(tp)
    
    # 计算 SMA
    sma = sum(typical_prices[-period:]) / period
    
    # 计算平均绝对偏差
    mean_deviation = sum(abs(tp - sma) for tp in typical_prices[-period:]) / period
    
    if mean_deviation == 0:
        return 0
    
    current_tp = typical_prices[-1]
    cci = (current_tp - sma) / (0.015 * mean_deviation)
    
    return cci


def calculate_momentum(
    prices: List[float],
    period: int = 10
) -> Optional[float]:
    """
    计算动量指标 (Momentum)
    
    Args:
        prices: 价格列表
        period: 周期（默认10）
        
    Returns:
        动量值
    """
    if len(prices) < period + 1:
        return None
    
    return prices[-1] - prices[-period - 1]


def calculate_roc(
    prices: List[float],
    period: int = 10
) -> Optional[float]:
    """
    计算变动率指标 (Rate of Change)
    
    Args:
        prices: 价格列表
        period: 周期（默认10）
        
    Returns:
        ROC 值（百分比）
    """
    if len(prices) < period + 1:
        return None
    
    prev_price = prices[-period - 1]
    if prev_price == 0:
        return 0
    
    return ((prices[-1] - prev_price) / prev_price) * 100


def calculate_adx(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    period: int = 14
) -> Optional[Tuple[float, float, float]]:
    """
    计算平均趋向指数 (Average Directional Index)
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        period: 周期（默认14）
        
    Returns:
        (ADX, +DI, -DI) 元组
    """
    if len(close_prices) < period * 2:
        return None
    
    # 计算 +DM 和 -DM
    plus_dm = []
    minus_dm = []
    tr_list = []
    
    for i in range(1, len(close_prices)):
        high_diff = high_prices[i] - high_prices[i - 1]
        low_diff = low_prices[i - 1] - low_prices[i]
        
        if high_diff > low_diff and high_diff > 0:
            plus_dm.append(high_diff)
        else:
            plus_dm.append(0)
        
        if low_diff > high_diff and low_diff > 0:
            minus_dm.append(low_diff)
        else:
            minus_dm.append(0)
        
        # True Range
        tr = max(
            high_prices[i] - low_prices[i],
            abs(high_prices[i] - close_prices[i - 1]),
            abs(low_prices[i] - close_prices[i - 1])
        )
        tr_list.append(tr)
    
    if len(tr_list) < period:
        return None
    
    # 平滑计算
    smoothed_plus_dm = sum(plus_dm[:period])
    smoothed_minus_dm = sum(minus_dm[:period])
    smoothed_tr = sum(tr_list[:period])
    
    for i in range(period, len(tr_list)):
        smoothed_plus_dm = smoothed_plus_dm - (smoothed_plus_dm / period) + plus_dm[i]
        smoothed_minus_dm = smoothed_minus_dm - (smoothed_minus_dm / period) + minus_dm[i]
        smoothed_tr = smoothed_tr - (smoothed_tr / period) + tr_list[i]
    
    if smoothed_tr == 0:
        return 0, 0, 0
    
    plus_di = 100 * smoothed_plus_dm / smoothed_tr
    minus_di = 100 * smoothed_minus_dm / smoothed_tr
    
    di_sum = plus_di + minus_di
    if di_sum == 0:
        dx = 0
    else:
        dx = 100 * abs(plus_di - minus_di) / di_sum
    
    # ADX 是 DX 的平滑平均
    adx = dx  # 简化版本
    
    return adx, plus_di, minus_di


def calculate_fibonacci_retracement(
    high: float,
    low: float
) -> Dict[str, float]:
    """
    计算斐波那契回撤位
    
    Args:
        high: 最高价
        low: 最低价
        
    Returns:
        各回撤位价格
    """
    diff = high - low
    
    return {
        "0.0%": high,
        "23.6%": high - diff * 0.236,
        "38.2%": high - diff * 0.382,
        "50.0%": high - diff * 0.500,
        "61.8%": high - diff * 0.618,
        "78.6%": high - diff * 0.786,
        "100.0%": low
    }


def calculate_pivot_points(
    high: float,
    low: float,
    close: float
) -> Dict[str, float]:
    """
    计算枢轴点 (Pivot Points)
    
    Args:
        high: 最高价
        low: 最低价
        close: 收盘价
        
    Returns:
        枢轴点和支撑/阻力位
    """
    pivot = (high + low + close) / 3
    
    return {
        "pivot": pivot,
        "r1": 2 * pivot - low,
        "r2": pivot + (high - low),
        "r3": high + 2 * (pivot - low),
        "s1": 2 * pivot - high,
        "s2": pivot - (high - low),
        "s3": low - 2 * (high - pivot)
    }


def get_extended_technical_signals(
    symbol: str,
    end_date: str,
    merged_path: Optional[str] = None
) -> Dict[str, any]:
    """
    获取扩展的技术分析信号（包含更多指标）
    
    Args:
        symbol: 股票代码
        end_date: 结束日期
        merged_path: 可选，自定义merged.jsonl路径
        
    Returns:
        包含扩展技术指标和交易信号的字典
    """
    # 获取基础信号
    signals = get_technical_signals(symbol, end_date, merged_path)
    
    if "error" in signals:
        return signals
    
    # 获取历史价格数据
    historical_data = get_historical_prices(symbol, end_date, days=50, merged_path=merged_path)
    
    if not historical_data:
        return signals
    
    close_prices = [d["close"] for d in historical_data]
    high_prices = [d["high"] for d in historical_data]
    low_prices = [d["low"] for d in historical_data]
    volumes = [d["volume"] for d in historical_data]
    
    # 添加扩展指标
    extended_indicators = {}
    extended_signals = {}
    
    # ATR
    atr = calculate_atr(high_prices, low_prices, close_prices)
    if atr:
        extended_indicators["atr"] = round(atr, 2)
    
    # Stochastic
    stoch = calculate_stochastic(high_prices, low_prices, close_prices)
    if stoch:
        k, d = stoch
        extended_indicators["stoch_k"] = round(k, 2)
        extended_indicators["stoch_d"] = round(d, 2)
        
        if k < 20 and d < 20:
            extended_signals["stochastic"] = "超卖-买入"
        elif k > 80 and d > 80:
            extended_signals["stochastic"] = "超买-卖出"
        else:
            extended_signals["stochastic"] = "中性"
    
    # Williams %R
    williams = calculate_williams_r(high_prices, low_prices, close_prices)
    if williams:
        extended_indicators["williams_r"] = round(williams, 2)
        
        if williams < -80:
            extended_signals["williams"] = "超卖-买入"
        elif williams > -20:
            extended_signals["williams"] = "超买-卖出"
        else:
            extended_signals["williams"] = "中性"
    
    # CCI
    cci = calculate_cci(high_prices, low_prices, close_prices)
    if cci:
        extended_indicators["cci"] = round(cci, 2)
        
        if cci < -100:
            extended_signals["cci"] = "超卖-买入"
        elif cci > 100:
            extended_signals["cci"] = "超买-卖出"
        else:
            extended_signals["cci"] = "中性"
    
    # Momentum
    momentum = calculate_momentum(close_prices)
    if momentum:
        extended_indicators["momentum"] = round(momentum, 2)
        
        if momentum > 0:
            extended_signals["momentum"] = "上涨动能"
        else:
            extended_signals["momentum"] = "下跌动能"
    
    # ROC
    roc = calculate_roc(close_prices)
    if roc:
        extended_indicators["roc"] = round(roc, 2)
    
    # ADX
    adx_result = calculate_adx(high_prices, low_prices, close_prices)
    if adx_result:
        adx, plus_di, minus_di = adx_result
        extended_indicators["adx"] = round(adx, 2)
        extended_indicators["plus_di"] = round(plus_di, 2)
        extended_indicators["minus_di"] = round(minus_di, 2)
        
        if adx > 25:
            if plus_di > minus_di:
                extended_signals["adx"] = "强势上涨趋势"
            else:
                extended_signals["adx"] = "强势下跌趋势"
        else:
            extended_signals["adx"] = "无明显趋势"
    
    # Pivot Points
    if historical_data:
        last_day = historical_data[-1]
        pivots = calculate_pivot_points(last_day["high"], last_day["low"], last_day["close"])
        extended_indicators["pivot_points"] = {k: round(v, 2) for k, v in pivots.items()}
    
    # 合并到原始信号
    signals["indicators"].update(extended_indicators)
    signals["signals"].update(extended_signals)
    
    # 重新计算综合信号
    buy_signals = sum(1 for s in signals["signals"].values() if "买入" in str(s))
    sell_signals = sum(1 for s in signals["signals"].values() if "卖出" in str(s))
    
    if buy_signals > sell_signals and buy_signals >= 3:
        signals["recommendation"] = "强烈买入"
    elif buy_signals > sell_signals and buy_signals >= 2:
        signals["recommendation"] = "买入"
    elif sell_signals > buy_signals and sell_signals >= 3:
        signals["recommendation"] = "强烈卖出"
    elif sell_signals > buy_signals and sell_signals >= 2:
        signals["recommendation"] = "卖出"
    else:
        signals["recommendation"] = "持有"
    
    signals["signal_count"] = {
        "buy": buy_signals,
        "sell": sell_signals,
        "total": len(signals["signals"])
    }
    
    return signals


if __name__ == "__main__":
    # 测试代码
    test_symbol = "AAPL"
    test_date = "2025-10-20"

    # 测试基础信号
    signals = get_technical_signals(test_symbol, test_date)
    print("基础信号:")
    print(json.dumps(signals, indent=2, ensure_ascii=False))
    
    # 测试扩展信号
    print("\n扩展信号:")
    extended = get_extended_technical_signals(test_symbol, test_date)
    print(json.dumps(extended, indent=2, ensure_ascii=False))
