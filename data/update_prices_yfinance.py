#!/usr/bin/env python3
"""使用 yfinance 更新股价数据（无 API 限制，速度快）"""
import yfinance as yf
import json
import os
from datetime import datetime, timedelta
import time

# 配置
CUTOFF_DATE = "2025-10-28"  # 只更新这个日期之后的数据
START_DATE = "2025-10-29"   # 开始下载的日期
END_DATE = "2025-11-09"     # 结束日期（包含当天）

# 所有纳斯达克100股票
all_nasdaq_100_symbols = [
    "NVDA", "MSFT", "AAPL", "GOOG", "GOOGL", "AMZN", "META", "AVGO", "TSLA",
    "NFLX", "PLTR", "COST", "ASML", "AMD", "CSCO", "AZN", "TMUS", "MU", "LIN",
    "PEP", "SHOP", "APP", "INTU", "AMAT", "LRCX", "PDD", "QCOM", "ARM", "INTC",
    "BKNG", "AMGN", "TXN", "ISRG", "GILD", "KLAC", "PANW", "ADBE", "HON",
    "CRWD", "CEG", "ADI", "ADP", "DASH", "CMCSA", "VRTX", "MELI", "SBUX",
    "CDNS", "ORLY", "SNPS", "MSTR", "MDLZ", "ABNB", "MRVL", "CTAS", "TRI",
    "MAR", "MNST", "CSX", "ADSK", "PYPL", "FTNT", "AEP", "WDAY", "REGN", "ROP",
    "NXPI", "DDOG", "AXON", "ROST", "IDXX", "EA", "PCAR", "FAST", "EXC", "TTWO",
    "XEL", "ZS", "PAYX", "WBD", "BKR", "CPRT", "CCEP", "FANG", "TEAM", "CHTR",
    "KDP", "MCHP", "GEHC", "VRSK", "CTSH", "CSGP", "KHC", "ODFL", "DXCM", "TTD",
    "ON", "BIIB", "LULU", "CDW", "GFS"
]

def convert_to_alpha_vantage_format(df, symbol):
    """将 yfinance 数据转换为 Alpha Vantage 格式"""
    time_series = {}
    
    for date, row in df.iterrows():
        date_str = date.strftime('%Y-%m-%d')
        time_series[date_str] = {
            "1. open": f"{row['Open']:.4f}",
            "2. high": f"{row['High']:.4f}",
            "3. low": f"{row['Low']:.4f}",
            "4. close": f"{row['Close']:.4f}",
            "5. volume": str(int(row['Volume']))
        }
    
    return {
        "Meta Data": {
            "1. Information": "Daily Prices (open, high, low, close) and Volumes",
            "2. Symbol": symbol,
            "3. Last Refreshed": df.index[-1].strftime('%Y-%m-%d') if len(df) > 0 else "",
            "4. Output Size": "Full size",
            "5. Time Zone": "US/Eastern"
        },
        "Time Series (Daily)": time_series
    }

def merge_price_data(symbol: str, new_data: dict, cutoff_date: str):
    """合并新旧数据，只保留 cutoff_date 之后的新数据"""
    filename = f'./daily_prices_{symbol}.json'
    
    # 读取现有数据
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        old_time_series = old_data.get('Time Series (Daily)', {})
    except FileNotFoundError:
        print(f"  ⚠️  未找到旧数据文件，将创建新文件")
        old_time_series = {}
    
    # 获取新数据
    new_time_series = new_data.get('Time Series (Daily)', {})
    
    # 只保留 cutoff_date 之后的新数据
    dates_to_add = {date for date in new_time_series.keys() if date > cutoff_date}
    
    # 合并数据
    merged_time_series = old_time_series.copy()
    added_count = 0
    updated_count = 0
    
    for date in dates_to_add:
        if date in merged_time_series:
            updated_count += 1
        else:
            added_count += 1
        merged_time_series[date] = new_time_series[date]
    
    # 构建完整数据结构
    merged_data = {
        "Meta Data": new_data.get("Meta Data", {}),
        "Time Series (Daily)": merged_time_series
    }
    
    # 保存合并后的数据
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)
    
    # QQQ 需要额外保存一份
    if symbol == "QQQ":
        with open(f'./Adaily_prices_{symbol}.json', 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=4)
    
    # 获取最新日期
    all_dates = sorted(merged_time_series.keys(), reverse=True)
    latest_date = all_dates[0] if all_dates else "未知"
    
    return {
        'added': added_count,
        'updated': updated_count,
        'total': len(merged_time_series),
        'latest_date': latest_date
    }

def get_and_merge_price_yfinance(symbol: str, start_date: str, end_date: str, cutoff_date: str):
    """使用 yfinance 获取股价数据并合并到现有文件"""
    print(f"📥 正在获取 {symbol:6s} 的数据...", end=" ")
    
    try:
        # 下载数据
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"❌ 无数据")
            return None
        
        # 转换为 Alpha Vantage 格式
        data = convert_to_alpha_vantage_format(df, symbol)
        
        # 合并数据
        result = merge_price_data(symbol, data, cutoff_date)
        
        print(f"✅ 新增 {result['added']:2d} 天, 更新 {result['updated']:2d} 天, "
              f"总计 {result['total']:3d} 天, 最新: {result['latest_date']}")
        
        return result
        
    except Exception as e:
        print(f"❌ 异常: {e}")
        return None

if __name__ == "__main__":
    print("=" * 90)
    print("🚀 使用 yfinance 更新股价数据（无 API 限制）")
    print("=" * 90)
    print(f"📅 更新日期范围: {START_DATE} 到 {END_DATE}")
    print(f"📊 需要更新的股票: {len(all_nasdaq_100_symbols)} 只（纳斯达克100 + QQQ）")
    print(f"⏱️  预计耗时: {len(all_nasdaq_100_symbols) * 1 / 60:.1f} 分钟（yfinance 速度很快！）")
    print()
    
    # 添加 QQQ
    symbols_to_update = all_nasdaq_100_symbols + ["QQQ"]
    
    success_count = 0
    failed_symbols = []
    total_added = 0
    total_updated = 0
    
    start_time = time.time()
    
    for i, symbol in enumerate(symbols_to_update, 1):
        print(f"[{i:3d}/{len(symbols_to_update)}] ", end="")
        
        result = get_and_merge_price_yfinance(symbol, START_DATE, END_DATE, CUTOFF_DATE)
        
        if result:
            success_count += 1
            total_added += result['added']
            total_updated += result['updated']
        else:
            failed_symbols.append(symbol)
        
        # yfinance 不需要等待，但为了避免过快请求，稍微延迟一下
        if i % 10 == 0:
            time.sleep(0.5)
    
    elapsed_time = time.time() - start_time
    
    print()
    print("=" * 90)
    print(f"✅ 完成! 耗时: {elapsed_time:.1f} 秒")
    print(f"   成功: {success_count}/{len(symbols_to_update)} 只股票")
    print(f"   新增: {total_added} 天数据")
    print(f"   更新: {total_updated} 天数据")
    if failed_symbols:
        print(f"   ❌ 失败: {', '.join(failed_symbols)}")
    print("=" * 90)
    print()
    print("💡 提示:")
    print(f"   - 如需修改日期范围，编辑第 10-11 行的 START_DATE 和 END_DATE")
    print(f"   - 如需修改截止日期，编辑第 9 行的 CUTOFF_DATE")
    print(f"   - yfinance 无 API 限制，速度快，推荐使用！")
