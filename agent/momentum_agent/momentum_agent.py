"""
MomentumAgent - 基于动量策略的交易代理

动量策略核心思想：
- 买入近期表现强势的股票（价格上涨动量）
- 卖出近期表现弱势的股票（价格下跌动量）
- 利用市场趋势的持续性获利
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 导入项目工具
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from tools.general_tools import write_config_value, get_config_value
from tools.price_tools import get_latest_position, get_open_prices, add_no_trade_record, get_yesterday_date
from tools.technical_indicators import (
    get_historical_prices,
    calculate_roc,
    calculate_rsi,
    calculate_momentum,
    calculate_ema,
    calculate_sma,
    calculate_adx
)
from tools.risk_management import RiskManager, create_default_risk_manager
from agent.agent_base import TradingAgentBase


class MomentumAgent(TradingAgentBase):
    """
    动量策略交易代理
    
    策略逻辑：
    1. 计算所有股票的动量得分（基于价格变化率、RSI、趋势强度）
    2. 选择动量得分最高的 N 只股票买入
    3. 卖出动量得分转负或低于阈值的持仓
    4. 结合风险管理控制仓位和止损
    
    动量因子：
    - ROC (Rate of Change): 价格变化率
    - RSI: 相对强弱
    - 价格相对于均线位置
    - ADX: 趋势强度
    """
    
    def __init__(
        self,
        signature: str,
        stock_symbols: Optional[List[str]] = None,
        log_path: Optional[str] = None,
        initial_cash: float = 10000.0,
        init_date: str = "2025-10-01",
        # 动量策略参数
        lookback_period: int = 20,          # 动量计算回溯期
        top_n_stocks: int = 10,             # 持有股票数量
        rebalance_threshold: float = 0.3,   # 再平衡阈值
        momentum_threshold: float = 0.0,    # 最低动量阈值
        # 风险管理参数
        max_position_pct: float = 0.15,     # 单一股票最大仓位
        stop_loss_pct: float = 0.08,        # 止损比例
        use_risk_management: bool = True    # 是否启用风险管理
    ):
        """
        初始化 MomentumAgent
        
        Args:
            signature: 代理签名/名称
            stock_symbols: 股票代码列表
            log_path: 日志路径
            initial_cash: 初始资金
            init_date: 初始化日期
            lookback_period: 动量计算回溯期（天）
            top_n_stocks: 持有的股票数量
            rebalance_threshold: 触发再平衡的动量变化阈值
            momentum_threshold: 买入的最低动量得分
            max_position_pct: 单一股票最大仓位比例
            stop_loss_pct: 止损比例
            use_risk_management: 是否启用风险管理
        """
        # 调用父类初始化
        super().__init__(
            signature=signature,
            stock_symbols=stock_symbols,
            log_path=log_path,
            initial_cash=initial_cash,
            init_date=init_date,
            use_trading_calendar=True
        )
        
        # 动量策略参数
        self.lookback_period = lookback_period
        self.top_n_stocks = top_n_stocks
        self.rebalance_threshold = rebalance_threshold
        self.momentum_threshold = momentum_threshold
        
        # 风险管理
        self.use_risk_management = use_risk_management
        self.max_position_pct = max_position_pct
        self.stop_loss_pct = stop_loss_pct
        
        if use_risk_management:
            self.risk_manager = RiskManager(
                max_position_pct=max_position_pct,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=0.25,
                max_drawdown_pct=0.15
            )
        else:
            self.risk_manager = None
        
        # 缓存动量得分
        self._momentum_cache: Dict[str, float] = {}
    
    async def initialize(self) -> None:
        """初始化代理"""
        print(f"🚀 初始化动量策略代理: {self.signature}")
        print(f"📊 策略参数:")
        print(f"   - 回溯期: {self.lookback_period} 天")
        print(f"   - 持仓数量: {self.top_n_stocks} 只")
        print(f"   - 动量阈值: {self.momentum_threshold}")
        print(f"   - 风险管理: {'启用' if self.use_risk_management else '禁用'}")
        print(f"✅ 动量代理初始化完成")
    
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
    
    # ==================== 动量计算 ====================
    
    def calculate_momentum_score(
        self,
        symbol: str,
        today_date: str
    ) -> Optional[Dict[str, Any]]:
        """
        计算单只股票的动量得分
        
        综合以下因子：
        1. ROC (价格变化率) - 权重 40%
        2. RSI 位置 - 权重 20%
        3. 价格相对均线位置 - 权重 25%
        4. 趋势强度 (ADX) - 权重 15%
        
        Args:
            symbol: 股票代码
            today_date: 日期
            
        Returns:
            包含动量得分和各因子的字典
        """
        # 获取历史价格
        historical = get_historical_prices(symbol, today_date, days=self.lookback_period + 10)
        
        if not historical or len(historical) < self.lookback_period:
            return None
        
        close_prices = [d["close"] for d in historical]
        high_prices = [d["high"] for d in historical]
        low_prices = [d["low"] for d in historical]
        
        # 1. ROC (价格变化率)
        roc = calculate_roc(close_prices, self.lookback_period)
        roc_score = 0
        if roc is not None:
            # 归一化 ROC 到 -1 到 1 范围
            roc_score = max(-1, min(1, roc / 20))  # 假设 ±20% 为极值
        
        # 2. RSI
        rsi = calculate_rsi(close_prices, 14)
        rsi_score = 0
        if rsi is not None:
            # RSI 50-70 为正向动量，70+ 可能超买
            if 50 <= rsi <= 70:
                rsi_score = (rsi - 50) / 20  # 0 到 1
            elif rsi > 70:
                rsi_score = 0.5  # 超买区域降低得分
            elif 30 <= rsi < 50:
                rsi_score = (rsi - 50) / 20  # -1 到 0
            else:
                rsi_score = -0.5  # 超卖但可能继续下跌
        
        # 3. 价格相对均线位置
        sma_20 = calculate_sma(close_prices, 20)
        ema_12 = calculate_ema(close_prices, 12)
        ma_score = 0
        
        if sma_20 and ema_12 and close_prices:
            current_price = close_prices[-1]
            # 价格高于均线为正
            if current_price > sma_20:
                ma_score += 0.5
            if current_price > ema_12:
                ma_score += 0.3
            # EMA 高于 SMA 表示上升趋势
            if ema_12 > sma_20:
                ma_score += 0.2
            
            ma_score = max(-1, min(1, ma_score))
        
        # 4. ADX 趋势强度
        adx_result = calculate_adx(high_prices, low_prices, close_prices)
        adx_score = 0
        trend_direction = 0
        
        if adx_result:
            adx, plus_di, minus_di = adx_result
            # ADX > 25 表示强趋势
            if adx > 25:
                adx_score = min(1, (adx - 25) / 25)  # 归一化
                # 趋势方向
                if plus_di > minus_di:
                    trend_direction = 1
                else:
                    trend_direction = -1
                    adx_score = -adx_score  # 下跌趋势为负
        
        # 综合得分 (加权平均)
        total_score = (
            roc_score * 0.40 +
            rsi_score * 0.20 +
            ma_score * 0.25 +
            adx_score * 0.15
        )
        
        return {
            "symbol": symbol,
            "momentum_score": round(total_score, 4),
            "factors": {
                "roc": round(roc, 2) if roc else None,
                "roc_score": round(roc_score, 3),
                "rsi": round(rsi, 2) if rsi else None,
                "rsi_score": round(rsi_score, 3),
                "ma_score": round(ma_score, 3),
                "adx_score": round(adx_score, 3),
                "trend_direction": trend_direction
            },
            "current_price": close_prices[-1] if close_prices else None
        }
    
    def rank_stocks_by_momentum(
        self,
        today_date: str
    ) -> List[Dict[str, Any]]:
        """
        按动量得分对所有股票排名
        
        Args:
            today_date: 日期
            
        Returns:
            按动量得分降序排列的股票列表
        """
        momentum_scores = []
        
        print(f"📊 计算 {len(self.stock_symbols)} 只股票的动量得分...")
        
        for symbol in self.stock_symbols:
            try:
                score_data = self.calculate_momentum_score(symbol, today_date)
                if score_data and score_data["momentum_score"] is not None:
                    momentum_scores.append(score_data)
            except Exception as e:
                print(f"⚠️ 计算 {symbol} 动量时出错: {e}")
                continue
        
        # 按动量得分降序排序
        momentum_scores.sort(key=lambda x: x["momentum_score"], reverse=True)
        
        # 缓存得分
        self._momentum_cache = {s["symbol"]: s["momentum_score"] for s in momentum_scores}
        
        return momentum_scores
    
    # ==================== 交易执行 ====================
    
    def _execute_trades(
        self,
        today_date: str,
        ranked_stocks: List[Dict[str, Any]],
        current_position: Dict[str, float],
        log_file: str
    ) -> bool:
        """执行交易决策"""
        has_trade = False
        
        # 获取当前持仓的股票
        held_symbols = {
            sym for sym, shares in current_position.items()
            if sym != "CASH" and shares > 0
        }
        
        # 获取应该持有的股票（动量得分最高的 N 只）
        target_symbols = set()
        for stock in ranked_stocks[:self.top_n_stocks]:
            if stock["momentum_score"] >= self.momentum_threshold:
                target_symbols.add(stock["symbol"])
        
        # 1. 卖出：持有但不在目标列表中，或动量转负
        for symbol in held_symbols:
            should_sell = False
            sell_reason = ""
            
            if symbol not in target_symbols:
                should_sell = True
                sell_reason = "动量排名下降，不在目标持仓中"
            elif self._momentum_cache.get(symbol, 0) < self.momentum_threshold:
                should_sell = True
                sell_reason = f"动量得分 {self._momentum_cache.get(symbol, 0):.3f} 低于阈值"
            
            # 风险管理检查
            if self.risk_manager and not should_sell:
                prices = get_open_prices(today_date, [symbol])
                current_price = prices.get(f"{symbol}_price")
                if current_price:
                    sl_tp = self.risk_manager.check_stop_loss_take_profit(symbol, current_price)
                    if sl_tp["should_sell"]:
                        should_sell = True
                        sell_reason = sl_tp["reason"]
            
            if should_sell:
                shares = current_position.get(symbol, 0)
                if shares > 0:
                    has_trade = self._sell_stock(
                        symbol, int(shares), today_date, sell_reason, log_file
                    ) or has_trade
        
        # 2. 买入：在目标列表中但未持有
        symbols_to_buy = target_symbols - held_symbols
        
        if symbols_to_buy:
            # 重新获取持仓（卖出后更新）
            current_position, _ = get_latest_position(today_date, self.signature)
            cash_available = current_position.get("CASH", 0)
            
            # 计算每只股票的分配资金
            num_to_buy = len(symbols_to_buy)
            if num_to_buy > 0 and cash_available > 100:
                allocation_per_stock = (cash_available * 0.95) / num_to_buy  # 保留 5% 现金
                
                for symbol in symbols_to_buy:
                    # 获取价格
                    prices = get_open_prices(today_date, [symbol])
                    price = prices.get(f"{symbol}_price")
                    
                    if not price or price <= 0:
                        continue
                    
                    # 计算可买入股数
                    shares_to_buy = int(allocation_per_stock / price)
                    
                    if shares_to_buy > 0:
                        momentum_score = self._momentum_cache.get(symbol, 0)
                        buy_reason = f"动量得分 {momentum_score:.3f}，排名前 {self.top_n_stocks}"
                        
                        has_trade = self._buy_stock(
                            symbol, shares_to_buy, today_date, buy_reason, log_file
                        ) or has_trade
        
        return has_trade
    
    def _buy_stock(
        self,
        symbol: str,
        amount: int,
        today_date: str,
        reason: str,
        log_file: str
    ) -> bool:
        """买入股票"""
        try:
            current_position, current_action_id = get_latest_position(today_date, self.signature)
            
            prices = get_open_prices(today_date, [symbol])
            price = prices.get(f'{symbol}_price')
            
            if not price:
                self._log_message(log_file, f"❌ 无法获取 {symbol} 的价格", {"symbol": symbol})
                return False
            
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
            
            # 记录入场价格
            if self.risk_manager:
                self.risk_manager.set_entry_price(symbol, price)
            
            # 记录到文件
            with open(self.position_file, "a") as f:
                f.write(json.dumps({
                    "date": today_date,
                    "id": current_action_id + 1,
                    "this_action": {
                        "action": "buy",
                        "symbol": symbol,
                        "amount": amount,
                        "price": price,
                        "reason": reason,
                        "momentum_score": self._momentum_cache.get(symbol)
                    },
                    "positions": new_position
                }) + "\n")
            
            print(f"✅ 买入 {symbol}: {amount}股 @ ${price:.2f} (动量: {self._momentum_cache.get(symbol, 0):.3f})")
            self._log_message(log_file, f"买入 {symbol}", {
                "symbol": symbol,
                "amount": amount,
                "price": price,
                "reason": reason,
                "momentum_score": self._momentum_cache.get(symbol)
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
        reason: str,
        log_file: str
    ) -> bool:
        """卖出股票"""
        try:
            current_position, current_action_id = get_latest_position(today_date, self.signature)
            
            if symbol not in current_position or current_position[symbol] < amount:
                return False
            
            prices = get_open_prices(today_date, [symbol])
            price = prices.get(f'{symbol}_price')
            
            if not price:
                return False
            
            # 计算盈亏
            pnl_info = {}
            if self.risk_manager:
                entry_price = self.risk_manager.get_entry_price(symbol)
                if entry_price:
                    pnl_pct = (price - entry_price) / entry_price
                    pnl_amount = (price - entry_price) * amount
                    pnl_info = {
                        "entry_price": entry_price,
                        "exit_price": price,
                        "pnl_pct": f"{pnl_pct:.2%}",
                        "pnl_amount": round(pnl_amount, 2)
                    }
            
            # 执行卖出
            new_position = current_position.copy()
            new_position[symbol] -= amount
            new_position["CASH"] = new_position.get("CASH", 0) + (price * amount)
            
            # 清除入场价格
            if self.risk_manager and new_position[symbol] == 0:
                self.risk_manager.clear_entry_price(symbol)
            
            # 记录到文件
            with open(self.position_file, "a") as f:
                f.write(json.dumps({
                    "date": today_date,
                    "id": current_action_id + 1,
                    "this_action": {
                        "action": "sell",
                        "symbol": symbol,
                        "amount": amount,
                        "price": price,
                        "reason": reason,
                        **pnl_info
                    },
                    "positions": new_position
                }) + "\n")
            
            pnl_str = f", 盈亏: {pnl_info.get('pnl_pct', 'N/A')}" if pnl_info else ""
            print(f"✅ 卖出 {symbol}: {amount}股 @ ${price:.2f}{pnl_str}")
            self._log_message(log_file, f"卖出 {symbol}", {
                "symbol": symbol,
                "amount": amount,
                "price": price,
                "reason": reason,
                **pnl_info
            })
            
            write_config_value("IF_TRADE", True)
            return True
            
        except Exception as e:
            print(f"❌ 卖出 {symbol} 时出错: {e}")
            return False
    
    # ==================== 交易会话 ====================
    
    async def run_trading_session(self, today_date: str) -> None:
        """运行单日交易会话"""
        print(f"📈 开始动量策略交易会话: {today_date}")
        
        log_file = self._setup_logging(today_date)
        self._log_message(log_file, f"开始 {today_date} 动量策略交易", {
            "lookback_period": self.lookback_period,
            "top_n_stocks": self.top_n_stocks
        })
        
        try:
            # 获取当前持仓
            current_position, _ = get_latest_position(today_date, self.signature)
            
            # 计算动量排名
            ranked_stocks = self.rank_stocks_by_momentum(today_date)
            
            if not ranked_stocks:
                print("⚠️ 无法计算动量得分")
                self._log_message(log_file, "无法计算动量得分", {})
                add_no_trade_record(today_date, self.signature)
                write_config_value("IF_TRADE", False)
                return
            
            # 记录排名
            top_10 = ranked_stocks[:10]
            bottom_5 = ranked_stocks[-5:] if len(ranked_stocks) >= 5 else []
            
            self._log_message(log_file, "动量排名完成", {
                "top_10": [
                    {"symbol": s["symbol"], "score": s["momentum_score"]}
                    for s in top_10
                ],
                "bottom_5": [
                    {"symbol": s["symbol"], "score": s["momentum_score"]}
                    for s in bottom_5
                ]
            })
            
            print(f"📊 动量排名 Top 5: {[f'{s['symbol']}({s['momentum_score']:.3f})' for s in top_10[:5]]}")
            
            # 执行交易
            has_trade = self._execute_trades(today_date, ranked_stocks, current_position, log_file)
            
            if not has_trade:
                print("📊 今日无交易，保持持仓")
                add_no_trade_record(today_date, self.signature)
                write_config_value("IF_TRADE", False)
            else:
                print("✅ 动量策略交易完成")
            
            self._log_message(log_file, "交易会话结束", {"has_trade": has_trade})
            
        except Exception as e:
            print(f"❌ 交易会话错误: {str(e)}")
            self._log_message(log_file, f"错误: {str(e)}", {})
            raise
    
    # ==================== 覆盖父类方法 ====================
    
    def get_position_summary(self) -> Dict[str, Any]:
        """获取持仓摘要（扩展父类方法）"""
        summary = super().get_position_summary()
        if "error" not in summary:
            summary["strategy"] = "momentum"
            summary["lookback_period"] = self.lookback_period
            summary["top_n_stocks"] = self.top_n_stocks
        return summary
    
    def __str__(self) -> str:
        return f"MomentumAgent(signature='{self.signature}', lookback={self.lookback_period}, top_n={self.top_n_stocks})"
    
    def __repr__(self) -> str:
        return self.__str__()
