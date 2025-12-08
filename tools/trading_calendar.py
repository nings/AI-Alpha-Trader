"""
交易日历模块
提供美股交易日判断功能，包括节假日处理
"""

from datetime import datetime, timedelta
from typing import List, Set, Optional
import json
from pathlib import Path


# 美股固定节假日（每年相同日期）
# 格式: (月, 日)
FIXED_HOLIDAYS = {
    (1, 1),    # 元旦 New Year's Day
    (7, 4),    # 独立日 Independence Day
    (12, 25),  # 圣诞节 Christmas Day
}

# 美股浮动节假日（需要按规则计算）
# 格式: (月, 周数, 星期几) - 星期几: 0=周一, 6=周日
FLOATING_HOLIDAYS = {
    "mlk_day": (1, 3, 0),           # 马丁·路德·金纪念日: 1月第3个周一
    "presidents_day": (2, 3, 0),     # 总统日: 2月第3个周一
    "memorial_day": (5, -1, 0),      # 阵亡将士纪念日: 5月最后一个周一
    "labor_day": (9, 1, 0),          # 劳动节: 9月第1个周一
    "thanksgiving": (11, 4, 3),      # 感恩节: 11月第4个周四
}

# 特殊节假日（耶稣受难日，复活节前的周五，需要特殊计算）
# 这里预先定义一些年份的耶稣受难日
GOOD_FRIDAY_DATES = {
    2024: (3, 29),
    2025: (4, 18),
    2026: (4, 3),
    2027: (3, 26),
    2028: (4, 14),
    2029: (3, 30),
    2030: (4, 19),
}


class TradingCalendar:
    """
    美股交易日历
    
    功能：
    1. 判断某日是否为交易日
    2. 获取下一个/上一个交易日
    3. 获取日期范围内的所有交易日
    4. 支持自定义节假日
    """
    
    def __init__(self, custom_holidays: Optional[Set[str]] = None):
        """
        初始化交易日历
        
        Args:
            custom_holidays: 自定义节假日集合，格式为 "YYYY-MM-DD"
        """
        self.custom_holidays = custom_holidays or set()
        self._holiday_cache: dict = {}
    
    def _get_nth_weekday_of_month(
        self,
        year: int,
        month: int,
        weekday: int,
        n: int
    ) -> datetime:
        """
        获取某月的第 n 个星期几
        
        Args:
            year: 年份
            month: 月份
            weekday: 星期几 (0=周一, 6=周日)
            n: 第几个 (正数从月初算，负数从月末算)
            
        Returns:
            对应的日期
        """
        if n > 0:
            # 从月初开始找
            first_day = datetime(year, month, 1)
            # 找到第一个目标星期几
            days_ahead = weekday - first_day.weekday()
            if days_ahead < 0:
                days_ahead += 7
            first_weekday = first_day + timedelta(days=days_ahead)
            # 加上 (n-1) 周
            return first_weekday + timedelta(weeks=n - 1)
        else:
            # 从月末开始找
            if month == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month + 1, 1)
            last_day = next_month - timedelta(days=1)
            
            # 找到最后一个目标星期几
            days_behind = last_day.weekday() - weekday
            if days_behind < 0:
                days_behind += 7
            last_weekday = last_day - timedelta(days=days_behind)
            # 减去 (-n-1) 周
            return last_weekday - timedelta(weeks=-n - 1)
    
    def _get_holidays_for_year(self, year: int) -> Set[str]:
        """
        获取某年的所有节假日
        
        Args:
            year: 年份
            
        Returns:
            节假日集合，格式为 "YYYY-MM-DD"
        """
        if year in self._holiday_cache:
            return self._holiday_cache[year]
        
        holidays = set()
        
        # 1. 固定节假日
        for month, day in FIXED_HOLIDAYS:
            date = datetime(year, month, day)
            # 如果节假日落在周六，周五休市
            if date.weekday() == 5:
                date = date - timedelta(days=1)
            # 如果节假日落在周日，周一休市
            elif date.weekday() == 6:
                date = date + timedelta(days=1)
            holidays.add(date.strftime("%Y-%m-%d"))
        
        # 2. 浮动节假日
        for name, (month, week, weekday) in FLOATING_HOLIDAYS.items():
            date = self._get_nth_weekday_of_month(year, month, weekday, week)
            holidays.add(date.strftime("%Y-%m-%d"))
        
        # 3. 耶稣受难日
        if year in GOOD_FRIDAY_DATES:
            month, day = GOOD_FRIDAY_DATES[year]
            holidays.add(f"{year}-{month:02d}-{day:02d}")
        
        self._holiday_cache[year] = holidays
        return holidays
    
    def is_holiday(self, date: datetime) -> bool:
        """
        判断某日是否为节假日
        
        Args:
            date: 日期
            
        Returns:
            是否为节假日
        """
        date_str = date.strftime("%Y-%m-%d")
        
        # 检查自定义节假日
        if date_str in self.custom_holidays:
            return True
        
        # 检查标准节假日
        year_holidays = self._get_holidays_for_year(date.year)
        return date_str in year_holidays
    
    def is_trading_day(self, date: datetime) -> bool:
        """
        判断某日是否为交易日
        
        Args:
            date: 日期
            
        Returns:
            是否为交易日
        """
        # 周末不是交易日
        if date.weekday() >= 5:
            return False
        
        # 节假日不是交易日
        if self.is_holiday(date):
            return False
        
        return True
    
    def is_trading_day_str(self, date_str: str) -> bool:
        """
        判断某日是否为交易日（字符串版本）
        
        Args:
            date_str: 日期字符串，格式 "YYYY-MM-DD"
            
        Returns:
            是否为交易日
        """
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return self.is_trading_day(date)
    
    def get_next_trading_day(self, date: datetime) -> datetime:
        """
        获取下一个交易日
        
        Args:
            date: 起始日期
            
        Returns:
            下一个交易日
        """
        next_day = date + timedelta(days=1)
        while not self.is_trading_day(next_day):
            next_day += timedelta(days=1)
        return next_day
    
    def get_previous_trading_day(self, date: datetime) -> datetime:
        """
        获取上一个交易日
        
        Args:
            date: 起始日期
            
        Returns:
            上一个交易日
        """
        prev_day = date - timedelta(days=1)
        while not self.is_trading_day(prev_day):
            prev_day -= timedelta(days=1)
        return prev_day
    
    def get_trading_days(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[datetime]:
        """
        获取日期范围内的所有交易日
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易日列表
        """
        trading_days = []
        current = start_date
        
        while current <= end_date:
            if self.is_trading_day(current):
                trading_days.append(current)
            current += timedelta(days=1)
        
        return trading_days
    
    def get_trading_days_str(
        self,
        start_date: str,
        end_date: str
    ) -> List[str]:
        """
        获取日期范围内的所有交易日（字符串版本）
        
        Args:
            start_date: 开始日期，格式 "YYYY-MM-DD"
            end_date: 结束日期，格式 "YYYY-MM-DD"
            
        Returns:
            交易日字符串列表
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        trading_days = self.get_trading_days(start, end)
        return [d.strftime("%Y-%m-%d") for d in trading_days]
    
    def count_trading_days(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """
        计算日期范围内的交易日数量
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易日数量
        """
        return len(self.get_trading_days(start_date, end_date))
    
    def add_trading_days(
        self,
        date: datetime,
        days: int
    ) -> datetime:
        """
        在日期上加/减若干交易日
        
        Args:
            date: 起始日期
            days: 交易日数量（正数向后，负数向前）
            
        Returns:
            结果日期
        """
        if days == 0:
            return date
        
        result = date
        step = 1 if days > 0 else -1
        remaining = abs(days)
        
        while remaining > 0:
            result += timedelta(days=step)
            if self.is_trading_day(result):
                remaining -= 1
        
        return result
    
    def get_holidays_in_range(
        self,
        start_date: str,
        end_date: str
    ) -> List[dict]:
        """
        获取日期范围内的所有节假日
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            节假日列表，包含日期和名称
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        holidays = []
        current = start
        
        while current <= end:
            if current.weekday() < 5 and self.is_holiday(current):
                holidays.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "weekday": current.strftime("%A")
                })
            current += timedelta(days=1)
        
        return holidays


# ==================== 便捷函数 ====================

# 全局日历实例
_calendar: Optional[TradingCalendar] = None


def get_trading_calendar() -> TradingCalendar:
    """获取全局交易日历实例"""
    global _calendar
    if _calendar is None:
        _calendar = TradingCalendar()
    return _calendar


def is_trading_day(date_str: str) -> bool:
    """
    判断某日是否为交易日
    
    Args:
        date_str: 日期字符串，格式 "YYYY-MM-DD"
        
    Returns:
        是否为交易日
    """
    return get_trading_calendar().is_trading_day_str(date_str)


def get_trading_days(start_date: str, end_date: str) -> List[str]:
    """
    获取日期范围内的所有交易日
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        交易日列表
    """
    return get_trading_calendar().get_trading_days_str(start_date, end_date)


def get_previous_trading_day(date_str: str) -> str:
    """
    获取上一个交易日
    
    Args:
        date_str: 日期字符串
        
    Returns:
        上一个交易日
    """
    date = datetime.strptime(date_str, "%Y-%m-%d")
    prev = get_trading_calendar().get_previous_trading_day(date)
    return prev.strftime("%Y-%m-%d")


def get_next_trading_day(date_str: str) -> str:
    """
    获取下一个交易日
    
    Args:
        date_str: 日期字符串
        
    Returns:
        下一个交易日
    """
    date = datetime.strptime(date_str, "%Y-%m-%d")
    next_day = get_trading_calendar().get_next_trading_day(date)
    return next_day.strftime("%Y-%m-%d")


if __name__ == "__main__":
    # 测试代码
    calendar = TradingCalendar()
    
    # 测试 2025 年节假日
    print("2025 年美股节假日:")
    holidays = calendar.get_holidays_in_range("2025-01-01", "2025-12-31")
    for h in holidays:
        print(f"  {h['date']} ({h['weekday']})")
    
    # 测试交易日判断
    print("\n交易日判断测试:")
    test_dates = [
        "2025-01-01",  # 元旦
        "2025-01-02",  # 元旦后
        "2025-01-20",  # MLK Day
        "2025-07-04",  # 独立日
        "2025-11-27",  # 感恩节
        "2025-12-25",  # 圣诞节
    ]
    
    for date_str in test_dates:
        is_td = calendar.is_trading_day_str(date_str)
        print(f"  {date_str}: {'交易日' if is_td else '非交易日'}")
    
    # 测试获取交易日列表
    print("\n2025年1月交易日:")
    trading_days = calendar.get_trading_days_str("2025-01-01", "2025-01-31")
    print(f"  共 {len(trading_days)} 个交易日")
    print(f"  {trading_days[:5]}...")
