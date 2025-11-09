#!/usr/bin/env python3
"""快速更新当前持仓股票的价格数据"""
import requests
import os
from dotenv import load_dotenv
import json
import time

load_dotenv()

# 只更新当前持仓的股票
SYMBOLS_TO_UPDATE = ["TSLA", "COST", "ASML", "QQQ"]

def get_daily_price(SYMBOL: str):
    FUNCTION = "TIME_SERIES_DAILY"
    OUTPUTSIZE = 'full'  # 使用 full 获取更多历史数据
    APIKEY = os.getenv("ALPHAADVANTAGE_API_KEY")
    
    print(f"📥 正在获取 {SYMBOL} 的数据...")
    url = f'https://www.alphavantage.co/query?function={FUNCTION}&symbol={SYMBOL}&outputsize={OUTPUTSIZE}&apikey={APIKEY}'
    
    r = requests.get(url)
    data = r.json()
    
    # 检查错误
    if data.get('Note') is not None:
        print(f"❌ API 限流: {data.get('Note')}")
        return False
    if data.get('Information') is not None:
        print(f"❌ API 错误: {data.get('Information')}")
        return False
    if 'Time Series (Daily)' not in data:
        print(f"❌ 数据格式错误: {data}")
        return False
    
    # 保存数据
    filename = f'./daily_prices_{SYMBOL}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    # 检查最新日期
    dates = sorted(data['Time Series (Daily)'].keys(), reverse=True)
    latest_date = dates[0] if dates else "未知"
    print(f"✅ {SYMBOL} 更新成功! 最新日期: {latest_date}")
    
    # QQQ 需要额外保存一份
    if SYMBOL == "QQQ":
        with open(f'./Adaily_prices_{SYMBOL}.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 开始更新股价数据")
    print("=" * 60)
    print(f"需要更新的股票: {', '.join(SYMBOLS_TO_UPDATE)}")
    print()
    
    success_count = 0
    for i, symbol in enumerate(SYMBOLS_TO_UPDATE, 1):
        print(f"[{i}/{len(SYMBOLS_TO_UPDATE)}] ", end="")
        
        if get_daily_price(symbol):
            success_count += 1
        
        # Alpha Vantage 免费版限制: 5次/分钟
        # 每次请求后等待 15 秒
        if i < len(SYMBOLS_TO_UPDATE):
            print("⏳ 等待 15 秒避免 API 限流...")
            time.sleep(15)
        print()
    
    print("=" * 60)
    print(f"✅ 完成! 成功更新 {success_count}/{len(SYMBOLS_TO_UPDATE)} 只股票")
    print("=" * 60)
