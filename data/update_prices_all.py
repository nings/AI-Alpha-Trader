#!/usr/bin/env python3
"""更新所有纳斯达克100股票的价格数据（带限流控制）"""
import requests
import os
from dotenv import load_dotenv
import json
import time

load_dotenv()

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
    "ON", "BIIB", "LULU", "CDW", "GFS", "QQQ"
]

def get_daily_price(SYMBOL: str):
    FUNCTION = "TIME_SERIES_DAILY"
    OUTPUTSIZE = 'full'  # 获取完整历史数据
    APIKEY = os.getenv("ALPHAADVANTAGE_API_KEY")
    
    print(f"📥 正在获取 {SYMBOL} 的数据...", end=" ")
    url = f'https://www.alphavantage.co/query?function={FUNCTION}&symbol={SYMBOL}&outputsize={OUTPUTSIZE}&apikey={APIKEY}'
    
    try:
        r = requests.get(url, timeout=30)
        data = r.json()
        
        # 检查错误
        if data.get('Note') is not None:
            print(f"❌ API 限流")
            return False
        if data.get('Information') is not None:
            print(f"❌ API 错误")
            return False
        if 'Time Series (Daily)' not in data:
            print(f"❌ 数据格式错误")
            return False
        
        # 保存数据
        filename = f'./daily_prices_{SYMBOL}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        # 检查最新日期
        dates = sorted(data['Time Series (Daily)'].keys(), reverse=True)
        latest_date = dates[0] if dates else "未知"
        print(f"✅ 最新: {latest_date}")
        
        # QQQ 需要额外保存一份
        if SYMBOL == "QQQ":
            with open(f'./Adaily_prices_{SYMBOL}.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        
        return True
        
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 开始更新所有纳斯达克100股票价格数据")
    print("=" * 70)
    print(f"总共需要更新: {len(all_nasdaq_100_symbols)} 只股票")
    print(f"预计耗时: {len(all_nasdaq_100_symbols) * 15 / 60:.1f} 分钟")
    print("Alpha Vantage 免费 API 限制: 5次/分钟")
    print()
    
    success_count = 0
    failed_symbols = []
    
    for i, symbol in enumerate(all_nasdaq_100_symbols, 1):
        print(f"[{i:3d}/{len(all_nasdaq_100_symbols)}] ", end="")
        
        if get_daily_price(symbol):
            success_count += 1
        else:
            failed_symbols.append(symbol)
        
        # Alpha Vantage 免费版限制: 5次/分钟
        # 每次请求后等待 15 秒（安全起见）
        if i < len(all_nasdaq_100_symbols):
            if i % 5 == 0:
                print(f"⏳ 已完成 {i} 个，等待 15 秒...")
            time.sleep(15)
    
    print()
    print("=" * 70)
    print(f"✅ 完成! 成功: {success_count}/{len(all_nasdaq_100_symbols)}")
    if failed_symbols:
        print(f"❌ 失败的股票: {', '.join(failed_symbols)}")
    print("=" * 70)
