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


if __name__ == "__main__":
    # 测试代码
    test_symbol = "AAPL"
    test_date = "2025-10-20"

    signals = get_technical_signals(test_symbol, test_date)
    print(json.dumps(signals, indent=2, ensure_ascii=False))
