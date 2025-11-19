"""
TraditionalAgent - 基于传统技术指标的交易代理

这个代理不使用AI模型，而是使用经典的技术分析指标（如MA、RSI、MACD等）
来做出交易决策，提供一个传统量化策略的对比基准。
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# 导入项目工具
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from tools.general_tools import write_config_value, get_config_value
from tools.price_tools import get_latest_position, get_open_prices, add_no_trade_record, get_yesterday_date
from tools.technical_indicators import get_technical_signals


class TraditionalAgent:
    """
    传统技术分析交易代理

    使用经典技术指标进行交易决策：
    - 移动平均线 (MA)
    - 相对强弱指标 (RSI)
    - MACD
    - 布林带

    策略逻辑：
    1. 综合多个技术指标的信号
    2. 当多数指标发出买入信号时买入
    3. 当多数指标发出卖出信号时卖出
    4. 采用资金管理策略控制仓位
    """

    # 默认纳斯达克100股票代码
    DEFAULT_STOCK_SYMBOLS = [
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

    def __init__(
        self,
        signature: str,
        stock_symbols: Optional[List[str]] = None,
        log_path: Optional[str] = None,
        initial_cash: float = 10000.0,
        init_date: str = "2025-10-01",
        max_position_pct: float = 0.15,  # 单个股票最大仓位比例
        top_n_stocks: int = 10,  # 每次交易选择信号最强的N只股票
        strategy: str = "multi_indicator"  # 策略类型
    ):
        """
        初始化TraditionalAgent

        Args:
            signature: 代理签名/名称
            stock_symbols: 股票代码列表
            log_path: 日志路径
            initial_cash: 初始资金
            init_date: 初始化日期
            max_position_pct: 单个股票最大仓位比例
            top_n_stocks: 每次选择信号最强的N只股票
            strategy: 策略类型 (multi_indicator, ma_cross, rsi, macd)
        """
        self.signature = signature
        self.stock_symbols = stock_symbols or self.DEFAULT_STOCK_SYMBOLS
        self.initial_cash = initial_cash
        self.init_date = init_date
        self.max_position_pct = max_position_pct
        self.top_n_stocks = top_n_stocks
        self.strategy = strategy

        # 设置日志路径
        self.base_log_path = log_path or "./data/agent_data"
        self.data_path = os.path.join(self.base_log_path, self.signature)
        self.position_file = os.path.join(self.data_path, "position", "position.jsonl")

    async def initialize(self) -> None:
        """初始化代理（传统策略不需要连接AI模型）"""
        print(f"🚀 初始化传统交易代理: {self.signature}")
        print(f"📊 策略类型: {self.strategy}")
        print(f"✅ 传统代理初始化完成")

    def _setup_logging(self, today_date: str) -> str:
        """设置日志文件路径"""
        log_path = os.path.join(self.base_log_path, self.signature, 'log', today_date)
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        return os.path.join(log_path, "log.jsonl")

    def _log_message(self, log_file: str, message: str, data: Optional[Dict] = None) -> None:
        """记录日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "signature": self.signature,
            "message": message,
            "data": data or {}
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def _analyze_stock(self, symbol: str, today_date: str) -> Dict[str, Any]:
        """分析单只股票的技术指标"""
        signals = get_technical_signals(symbol, today_date)
        return signals

    def _get_trading_candidates(self, today_date: str) -> List[Dict[str, Any]]:
        """获取交易候选股票（根据技术指标排序）"""
        candidates = []

        print(f"📊 分析 {len(self.stock_symbols)} 只股票的技术指标...")

        for symbol in self.stock_symbols:
            try:
                signals = self._analyze_stock(symbol, today_date)

                if "error" not in signals:
                    # 计算综合评分
                    score = 0
                    recommendation = signals.get("recommendation", "持有")

                    if recommendation == "买入":
                        score = 1
                    elif recommendation == "卖出":
                        score = -1

                    signals["score"] = score
                    candidates.append(signals)

            except Exception as e:
                print(f"⚠️ 分析 {symbol} 时出错: {e}")
                continue

        # 按评分排序
        candidates.sort(key=lambda x: x.get("score", 0), reverse=True)

        return candidates

    def _execute_trades(
        self,
        today_date: str,
        candidates: List[Dict[str, Any]],
        current_position: Dict[str, float],
        log_file: str
    ) -> bool:
        """执行交易决策"""
        has_trade = False

        # 获取当前可用现金
        cash_available = current_position.get("CASH", 0)

        # 获取今日价格
        buy_signals = [c for c in candidates if c.get("score", 0) > 0][:self.top_n_stocks]
        sell_signals = [c for c in candidates if c.get("score", 0) < 0]

        # 1. 先执行卖出操作
        for signal in sell_signals:
            symbol = signal["symbol"]
            current_shares = current_position.get(symbol, 0)

            if current_shares > 0:
                # 卖出全部持仓
                sell_amount = current_shares
                has_trade = self._sell_stock(
                    symbol, sell_amount, today_date, signal, log_file
                ) or has_trade

        # 2. 执行买入操作
        if buy_signals and cash_available > 0:
            # 重新获取最新持仓（卖出后可能有更多现金）
            current_position, _ = get_latest_position(today_date, self.signature)
            cash_available = current_position.get("CASH", 0)

            # 为每个买入候选分配资金
            allocation_per_stock = cash_available * self.max_position_pct

            for signal in buy_signals:
                symbol = signal["symbol"]
                current_price = signal.get("current_price")

                if not current_price or current_price <= 0:
                    continue

                # 计算可以买入的股数
                shares_to_buy = int(allocation_per_stock / current_price)

                if shares_to_buy > 0:
                    has_trade = self._buy_stock(
                        symbol, shares_to_buy, today_date, signal, log_file
                    ) or has_trade

        return has_trade

    def _buy_stock(
        self,
        symbol: str,
        amount: int,
        today_date: str,
        signal: Dict,
        log_file: str
    ) -> bool:
        """买入股票"""
        try:
            # 获取当前持仓
            current_position, current_action_id = get_latest_position(today_date, self.signature)

            # 获取价格
            prices = get_open_prices(today_date, [symbol])
            price = prices.get(f'{symbol}_price')

            if not price:
                self._log_message(log_file, f"❌ 无法获取 {symbol} 的价格", {"symbol": symbol})
                return False

            # 检查现金是否足够
            total_cost = price * amount
            cash_left = current_position.get("CASH", 0) - total_cost

            if cash_left < 0:
                self._log_message(log_file, f"❌ 现金不足，无法买入 {symbol}", {
                    "symbol": symbol,
                    "required": total_cost,
                    "available": current_position.get("CASH", 0)
                })
                return False

            # 执行买入
            new_position = current_position.copy()
            new_position["CASH"] = cash_left
            new_position[symbol] = new_position.get(symbol, 0) + amount

            # 记录到文件
            position_file_path = self.position_file
            with open(position_file_path, "a") as f:
                f.write(json.dumps({
                    "date": today_date,
                    "id": current_action_id + 1,
                    "this_action": {
                        "action": "buy",
                        "symbol": symbol,
                        "amount": amount,
                        "price": price,
                        "reason": signal.get("recommendation", "技术指标买入")
                    },
                    "positions": new_position
                }) + "\n")

            print(f"✅ 买入 {symbol}: {amount}股 @ ${price:.2f}")
            self._log_message(log_file, f"买入 {symbol}", {
                "symbol": symbol,
                "amount": amount,
                "price": price,
                "signals": signal.get("signals", {})
            })

            write_config_value("IF_TRADE", True)
            return True

        except Exception as e:
            print(f"❌ 买入 {symbol} 时出错: {e}")
            return False

    def _sell_stock(
        self,
        symbol: str,
        amount: int,
        today_date: str,
        signal: Dict,
        log_file: str
    ) -> bool:
        """卖出股票"""
        try:
            # 获取当前持仓
            current_position, current_action_id = get_latest_position(today_date, self.signature)

            # 检查是否持有
            if symbol not in current_position or current_position[symbol] < amount:
                return False

            # 获取价格
            prices = get_open_prices(today_date, [symbol])
            price = prices.get(f'{symbol}_price')

            if not price:
                return False

            # 执行卖出
            new_position = current_position.copy()
            new_position[symbol] -= amount
            new_position["CASH"] = new_position.get("CASH", 0) + (price * amount)

            # 记录到文件
            position_file_path = self.position_file
            with open(position_file_path, "a") as f:
                f.write(json.dumps({
                    "date": today_date,
                    "id": current_action_id + 1,
                    "this_action": {
                        "action": "sell",
                        "symbol": symbol,
                        "amount": amount,
                        "price": price,
                        "reason": signal.get("recommendation", "技术指标卖出")
                    },
                    "positions": new_position
                }) + "\n")

            print(f"✅ 卖出 {symbol}: {amount}股 @ ${price:.2f}")
            self._log_message(log_file, f"卖出 {symbol}", {
                "symbol": symbol,
                "amount": amount,
                "price": price,
                "signals": signal.get("signals", {})
            })

            write_config_value("IF_TRADE", True)
            return True

        except Exception as e:
            print(f"❌ 卖出 {symbol} 时出错: {e}")
            return False

    async def run_trading_session(self, today_date: str) -> None:
        """运行单日交易会话"""
        print(f"📈 开始交易会话: {today_date}")

        # 设置日志
        log_file = self._setup_logging(today_date)
        self._log_message(log_file, f"开始 {today_date} 交易", {"strategy": self.strategy})

        try:
            # 获取当前持仓
            current_position, _ = get_latest_position(today_date, self.signature)

            # 获取交易候选
            candidates = self._get_trading_candidates(today_date)

            if not candidates:
                print("⚠️ 没有找到可交易的股票")
                self._log_message(log_file, "没有交易候选", {})
                add_no_trade_record(today_date, self.signature)
                write_config_value("IF_TRADE", False)
                return

            # 记录分析结果
            top_buy = [c for c in candidates if c.get("score", 0) > 0][:5]
            top_sell = [c for c in candidates if c.get("score", 0) < 0][:5]

            self._log_message(log_file, "技术分析完成", {
                "top_buy_candidates": [
                    {"symbol": c["symbol"], "score": c.get("score"), "signals": c.get("signals")}
                    for c in top_buy
                ],
                "top_sell_candidates": [
                    {"symbol": c["symbol"], "score": c.get("score"), "signals": c.get("signals")}
                    for c in top_sell
                ]
            })

            # 执行交易
            has_trade = self._execute_trades(today_date, candidates, current_position, log_file)

            if not has_trade:
                print("📊 今日无交易，保持持仓")
                add_no_trade_record(today_date, self.signature)
                write_config_value("IF_TRADE", False)
            else:
                print("✅ 交易完成")

            self._log_message(log_file, "交易会话结束", {"has_trade": has_trade})

        except Exception as e:
            print(f"❌ 交易会话错误: {str(e)}")
            self._log_message(log_file, f"错误: {str(e)}", {})
            raise

    def register_agent(self) -> None:
        """注册新代理，创建初始持仓"""
        if os.path.exists(self.position_file):
            print(f"⚠️ 持仓文件 {self.position_file} 已存在，跳过注册")
            return

        # 确保目录结构存在
        position_dir = os.path.join(self.data_path, "position")
        if not os.path.exists(position_dir):
            os.makedirs(position_dir)
            print(f"📁 创建持仓目录: {position_dir}")

        # 创建初始持仓
        init_position = {symbol: 0 for symbol in self.stock_symbols}
        init_position['CASH'] = self.initial_cash

        with open(self.position_file, "w") as f:
            f.write(json.dumps({
                "date": self.init_date,
                "id": 0,
                "positions": init_position
            }) + "\n")

        print(f"✅ 代理 {self.signature} 注册完成")
        print(f"📁 持仓文件: {self.position_file}")
        print(f"💰 初始现金: ${self.initial_cash}")

    def get_trading_dates(self, init_date: str, end_date: str) -> List[str]:
        """获取交易日期列表"""
        dates = []
        max_date = None

        if not os.path.exists(self.position_file):
            self.register_agent()
            max_date = init_date
        else:
            # 读取已有持仓文件，找到最新日期
            with open(self.position_file, "r") as f:
                for line in f:
                    doc = json.loads(line)
                    current_date = doc['date']
                    if max_date is None:
                        max_date = current_date
                    else:
                        current_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
                        max_date_obj = datetime.strptime(max_date, "%Y-%m-%d")
                        if current_date_obj > max_date_obj:
                            max_date = current_date

        # 检查是否需要处理新日期
        max_date_obj = datetime.strptime(max_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

        if end_date_obj <= max_date_obj:
            return []

        # 生成交易日期列表
        trading_dates = []
        current_date = max_date_obj + timedelta(days=1)

        while current_date <= end_date_obj:
            if current_date.weekday() < 5:  # 工作日
                trading_dates.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)

        return trading_dates

    async def run_date_range(self, init_date: str, end_date: str) -> None:
        """运行日期范围内的所有交易日"""
        print(f"📅 运行日期范围: {init_date} 到 {end_date}")

        # 获取交易日期列表
        trading_dates = self.get_trading_dates(init_date, end_date)

        if not trading_dates:
            print(f"ℹ️ 没有需要处理的交易日")
            return

        print(f"📊 需要处理的交易日: {trading_dates}")

        # 处理每个交易日
        for date in trading_dates:
            print(f"🔄 处理 {self.signature} - 日期: {date}")

            # 设置配置
            write_config_value("TODAY_DATE", date)
            write_config_value("SIGNATURE", self.signature)

            try:
                await self.run_trading_session(date)
            except Exception as e:
                print(f"❌ 处理 {self.signature} - 日期 {date} 时出错")
                print(e)
                raise

        print(f"✅ {self.signature} 处理完成")

    def get_position_summary(self) -> Dict[str, Any]:
        """获取持仓摘要"""
        if not os.path.exists(self.position_file):
            return {"error": "持仓文件不存在"}

        positions = []
        with open(self.position_file, "r") as f:
            for line in f:
                positions.append(json.loads(line))

        if not positions:
            return {"error": "没有持仓记录"}

        latest_position = positions[-1]
        return {
            "signature": self.signature,
            "latest_date": latest_position.get("date"),
            "positions": latest_position.get("positions", {}),
            "total_records": len(positions)
        }

    def __str__(self) -> str:
        return f"TraditionalAgent(signature='{self.signature}', strategy='{self.strategy}', stocks={len(self.stock_symbols)})"

    def __repr__(self) -> str:
        return self.__str__()
