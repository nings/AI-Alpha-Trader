"""
TradingAgentBase - 所有交易代理的抽象基类

提取所有 Agent 的公共功能：
1. 持仓管理（注册、读取、更新）
2. 交易日期管理
3. 日志记录
4. 位置摘要
"""

import os
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 导入项目工具
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general_tools import write_config_value, get_config_value
from tools.price_tools import get_latest_position, add_no_trade_record
from tools.trading_calendar import get_trading_calendar, is_trading_day


class TradingAgentBase(ABC):
    """
    交易代理抽象基类
    
    所有交易代理（BaseAgent、TraditionalAgent、MomentumAgent 等）的公共基类。
    提供以下公共功能：
    - 持仓文件管理
    - 交易日期计算
    - 日志记录
    - 持仓摘要
    
    子类需要实现：
    - initialize(): 初始化代理
    - run_trading_session(): 运行单日交易会话
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
        use_trading_calendar: bool = True
    ):
        """
        初始化交易代理基类
        
        Args:
            signature: 代理签名/名称，用于标识数据存储路径
            stock_symbols: 股票代码列表，默认使用纳斯达克100
            log_path: 日志路径，默认 ./data/agent_data
            initial_cash: 初始资金
            init_date: 初始化日期
            use_trading_calendar: 是否使用交易日历（考虑节假日）
        """
        self.signature = signature
        self.stock_symbols = stock_symbols or self.DEFAULT_STOCK_SYMBOLS
        self.initial_cash = initial_cash
        self.init_date = init_date
        self.use_trading_calendar = use_trading_calendar
        
        # 设置路径
        self.base_log_path = log_path or "./data/agent_data"
        self.data_path = os.path.join(self.base_log_path, self.signature)
        self.position_file = os.path.join(self.data_path, "position", "position.jsonl")
        
        # 交易日历
        if use_trading_calendar:
            self._calendar = get_trading_calendar()
        else:
            self._calendar = None
    
    # ==================== 抽象方法（子类必须实现） ====================
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化代理
        
        子类应在此方法中完成：
        - AI 模型连接（如果需要）
        - MCP 工具加载（如果需要）
        - 策略参数初始化
        """
        pass
    
    @abstractmethod
    async def run_trading_session(self, today_date: str) -> None:
        """
        运行单日交易会话
        
        Args:
            today_date: 交易日期，格式 "YYYY-MM-DD"
            
        子类应在此方法中完成：
        - 获取市场数据
        - 分析和决策
        - 执行交易
        - 记录日志
        """
        pass
    
    # ==================== 日志管理 ====================
    
    def _setup_logging(self, today_date: str) -> str:
        """
        设置日志文件路径
        
        Args:
            today_date: 交易日期
            
        Returns:
            日志文件完整路径
        """
        log_path = os.path.join(self.base_log_path, self.signature, 'log', today_date)
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        return os.path.join(log_path, "log.jsonl")
    
    def _log_message(
        self,
        log_file: str,
        message: Any,
        data: Optional[Dict] = None
    ) -> None:
        """
        记录日志消息
        
        Args:
            log_file: 日志文件路径
            message: 日志消息（字符串或字典）
            data: 附加数据
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "signature": self.signature,
        }
        
        if isinstance(message, dict):
            log_entry["new_messages"] = message
        else:
            log_entry["message"] = message
            if data:
                log_entry["data"] = data
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    # ==================== 持仓管理 ====================
    
    def register_agent(self) -> None:
        """
        注册新代理，创建初始持仓文件
        
        如果持仓文件已存在，则跳过注册。
        """
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
        print(f"📊 股票数量: {len(self.stock_symbols)}")
    
    def get_position_summary(self) -> Dict[str, Any]:
        """
        获取持仓摘要
        
        Returns:
            包含最新持仓信息的字典
        """
        if not os.path.exists(self.position_file):
            return {"error": "持仓文件不存在"}
        
        positions = []
        with open(self.position_file, "r") as f:
            for line in f:
                if line.strip():
                    positions.append(json.loads(line))
        
        if not positions:
            return {"error": "没有持仓记录"}
        
        latest_position = positions[-1]
        
        # 计算持仓统计
        pos = latest_position.get("positions", {})
        cash = pos.get("CASH", 0)
        held_stocks = {k: v for k, v in pos.items() if k != "CASH" and v > 0}
        
        return {
            "signature": self.signature,
            "latest_date": latest_position.get("date"),
            "positions": pos,
            "cash": cash,
            "held_stocks_count": len(held_stocks),
            "total_records": len(positions)
        }
    
    # ==================== 交易日期管理 ====================
    
    def _is_trading_day(self, date: datetime) -> bool:
        """
        判断是否为交易日
        
        Args:
            date: 日期
            
        Returns:
            是否为交易日
        """
        if self._calendar:
            return self._calendar.is_trading_day(date)
        else:
            # 简单判断：工作日
            return date.weekday() < 5
    
    def get_trading_dates(self, init_date: str, end_date: str) -> List[str]:
        """
        获取需要处理的交易日期列表
        
        从持仓文件中找到最新日期，返回该日期之后到 end_date 之间的所有交易日。
        
        Args:
            init_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易日期字符串列表
        """
        max_date = None
        
        if not os.path.exists(self.position_file):
            self.register_agent()
            max_date = init_date
        else:
            # 读取已有持仓文件，找到最新日期
            with open(self.position_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    doc = json.loads(line)
                    current_date = doc.get('date')
                    if current_date:
                        if max_date is None:
                            max_date = current_date
                        else:
                            current_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
                            max_date_obj = datetime.strptime(max_date, "%Y-%m-%d")
                            if current_date_obj > max_date_obj:
                                max_date = current_date
        
        if max_date is None:
            max_date = init_date
        
        # 检查是否需要处理新日期
        max_date_obj = datetime.strptime(max_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        
        if end_date_obj <= max_date_obj:
            return []
        
        # 生成交易日期列表
        trading_dates = []
        current_date = max_date_obj + timedelta(days=1)
        
        while current_date <= end_date_obj:
            if self._is_trading_day(current_date):
                trading_dates.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)
        
        return trading_dates
    
    # ==================== 运行控制 ====================
    
    async def run_with_retry(
        self,
        today_date: str,
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> None:
        """
        带重试的运行方法
        
        Args:
            today_date: 交易日期
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
        """
        import asyncio
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"🔄 尝试运行 {self.signature} - {today_date} (第 {attempt} 次)")
                await self.run_trading_session(today_date)
                print(f"✅ {self.signature} - {today_date} 运行成功")
                return
            except Exception as e:
                print(f"❌ 第 {attempt} 次尝试失败: {str(e)}")
                if attempt == max_retries:
                    print(f"💥 {self.signature} - {today_date} 所有重试均失败")
                    raise
                else:
                    wait_time = base_delay * attempt
                    print(f"⏳ 等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
    
    async def run_date_range(
        self,
        init_date: str,
        end_date: str,
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> None:
        """
        运行日期范围内的所有交易日
        
        Args:
            init_date: 开始日期
            end_date: 结束日期
            max_retries: 每日最大重试次数
            base_delay: 重试基础延迟
        """
        print(f"📅 运行日期范围: {init_date} 到 {end_date}")
        
        # 获取交易日期列表
        trading_dates = self.get_trading_dates(init_date, end_date)
        
        if not trading_dates:
            print(f"ℹ️ 没有需要处理的交易日")
            return
        
        print(f"📊 需要处理的交易日: {len(trading_dates)} 天")
        if len(trading_dates) <= 10:
            print(f"   {trading_dates}")
        else:
            print(f"   {trading_dates[:5]} ... {trading_dates[-3:]}")
        
        # 处理每个交易日
        for date in trading_dates:
            print(f"\n🔄 处理 {self.signature} - 日期: {date}")
            
            # 设置配置
            write_config_value("TODAY_DATE", date)
            write_config_value("SIGNATURE", self.signature)
            
            try:
                await self.run_with_retry(date, max_retries, base_delay)
            except Exception as e:
                print(f"❌ 处理 {self.signature} - 日期 {date} 时出错: {e}")
                raise
        
        print(f"\n✅ {self.signature} 处理完成")
    
    # ==================== 辅助方法 ====================
    
    def _handle_no_trade(self, today_date: str) -> None:
        """
        处理无交易情况
        
        Args:
            today_date: 交易日期
        """
        add_no_trade_record(today_date, self.signature)
        write_config_value("IF_TRADE", False)
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(signature='{self.signature}', stocks={len(self.stock_symbols)})"
    
    def __repr__(self) -> str:
        return self.__str__()


# ==================== 辅助函数 ====================

def get_agent_type(agent_instance) -> str:
    """获取代理类型名称"""
    return agent_instance.__class__.__name__
