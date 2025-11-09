#!/usr/bin/env python3
"""只更新指定日期之后的股价数据（追加模式）"""
import requests
import os
from dotenv import load_dotenv
import json
import time
from datetime import datetime

load_dotenv()

# 配置
CUTOFF_DATE = "2025-10-28"  # 只更新这个日期之后的数据
SYMBOLS_TO_UPDATE = ["TSLA", "COST", "ASML", "QQQ"]  # 可以改为 all_nasdaq_100_symbols

# 所有纳斯达克100股票（如果需要全部更新，取消注释）
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

SYMBOLS_TO_UPDATE = all_nasdaq_100_symbols

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
    
    # 统计信息
    old_dates = set(old_time_series.keys())
    new_dates = set(new_time_series.keys())
    
    # 只保留 cutoff_date 之后的新数据
    dates_to_add = {date for date in new_dates if date > cutoff_date}
    
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

def get_and_merge_price(symbol: str, cutoff_date: str):
    """获取股价数据并合并到现有文件"""
    FUNCTION = "TIME_SERIES_DAILY"
    OUTPUTSIZE = 'full'  # 使用 full 确保获取足够的历史数据
    APIKEY = os.getenv("ALPHAADVANTAGE_API_KEY")
    
    print(f"📥 正在获取 {symbol} 的数据...", end=" ")
    url = f'https://www.alphavantage.co/query?function={FUNCTION}&symbol={symbol}&outputsize={OUTPUTSIZE}&apikey={APIKEY}'
    
    try:
        r = requests.get(url, timeout=30)
        data = r.json()
        
        # 检查错误
        if data.get('Note') is not None:
            print(f"❌ API 限流: {data.get('Note')}")
            return None
        if data.get('Information') is not None:
            print(f"❌ API 错误: {data.get('Information')}")
            return None
        if 'Time Series (Daily)' not in data:
            print(f"❌ 数据格式错误")
            return None
        
        # 合并数据
        result = merge_price_data(symbol, data, cutoff_date)
        
        print(f"✅ 新增 {result['added']} 天, 更新 {result['updated']} 天, "
              f"总计 {result['total']} 天, 最新: {result['latest_date']}")
        
        return result
        
    except Exception as e:
        print(f"❌ 异常: {e}")
        return None

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 增量更新股价数据")
    print("=" * 80)
    print(f"📅 只更新 {CUTOFF_DATE} 之后的数据")
    print(f"📊 需要更新的股票: {', '.join(SYMBOLS_TO_UPDATE)}")
    print(f"⏱️  预计耗时: {len(SYMBOLS_TO_UPDATE) * 15 / 60:.1f} 分钟")
    print()
    
    # 如果需要更新所有股票，取消下面的注释
    # SYMBOLS_TO_UPDATE = all_nasdaq_100_symbols
    # print(f"⚠️  已切换为更新所有 {len(all_nasdaq_100_symbols)} 只股票")
    # print(f"⏱️  预计耗时: {len(all_nasdaq_100_symbols) * 15 / 60:.1f} 分钟")
    # print()
    
    success_count = 0
    failed_symbols = []
    total_added = 0
    total_updated = 0
    
    for i, symbol in enumerate(SYMBOLS_TO_UPDATE, 1):
        print(f"[{i:3d}/{len(SYMBOLS_TO_UPDATE)}] ", end="")
        
        result = get_and_merge_price(symbol, CUTOFF_DATE)
        
        if result:
            success_count += 1
            total_added += result['added']
            total_updated += result['updated']
        else:
            failed_symbols.append(symbol)
        
        # Alpha Vantage 免费版限制: 5次/分钟
        # 每次请求后等待 15 秒（安全起见）
        if i < len(SYMBOLS_TO_UPDATE):
            print(f"  ⏳ 等待 15 秒避免 API 限流...")
            time.sleep(15)
        print()
    
    print("=" * 80)
    print(f"✅ 完成!")
    print(f"   成功: {success_count}/{len(SYMBOLS_TO_UPDATE)} 只股票")
    print(f"   新增: {total_added} 天数据")
    print(f"   更新: {total_updated} 天数据")
    if failed_symbols:
        print(f"   ❌ 失败: {', '.join(failed_symbols)}")
    print("=" * 80)
    print()
    print("💡 提示:")
    print(f"   - 如需更新所有股票，编辑脚本取消第 95 行的注释")
    print(f"   - 如需修改截止日期，修改第 11 行的 CUTOFF_DATE")
