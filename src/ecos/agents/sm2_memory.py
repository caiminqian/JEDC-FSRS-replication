"""
SM-2 算法 - 间隔重复调度引擎

Reference:
  - P.A. Wozniak, "Using spaced repetition to improve the speed of learning", 1995
  - https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-of-work

核心职责:
  1. 管理记忆项目的复习间隔 I(n)
  2. 根据复习质量 q (0-5) 更新 E-Factor (EF)
  3. 决定下次复习时间

与 EE 的关系:
  - EE 提供: R(t) = exp(-t/S) - 计算当前记忆保持率
  - SM-2 提供: I(n) = I(n-1) * EF - 决定复习间隔
  - EF 更新依赖于复习质量评分 q
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
import math


@dataclass
class SM2Item:
    """SM-2 记忆项目"""
    item_id: str
    description: str

    # SM-2 核心状态
    interval_days: int = 1           # I(n): 下次复习间隔（天）
    ef: float = 2.5                  # E-Factor: 项目易学性 [1.3, 10]
    repetition_count: int = 0        # n: 已复习次数
    last_review: Optional[datetime] = None

    # 元数据
    category: str = "default"
    difficulty: float = 5.0

    def next_review_date(self) -> Optional[datetime]:
        if self.last_review is None:
            return None
        return self.last_review + timedelta(days=self.interval_days)

    def is_due(self, when: Optional[datetime] = None) -> bool:
        """Check if item is due for review.
        
        New items (last_review=None) are always due (first review needed).
        """
        if self.last_review is None:
            return True
        when = when or datetime.now(timezone.utc)
        next_date = self.next_review_date()
        return next_date is not None and when >= next_date

    def days_since_review(self) -> Optional[int]:
        if self.last_review is None:
            return None
        delta = datetime.now(timezone.utc) - self.last_review
        return delta.days


class SM2Scheduler:
    """
    SM-2 调度器完整实现

    算法步骤 (来自 SuperMemo 论文):

    Step 1 - 初始化:
      I(1) = 1 天
      I(2) = 6 天
      EF = 2.5

    Step 2 - 每次复习后，根据质量 q 更新 EF:
      EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
      边界: EF ∈ [1.3, 10.0]

    Step 3 - 计算下次复习间隔:
      if n == 1: I(1) = 1
      elif n == 2: I(2) = 6
      else: I(n) = ceil(I(n-1) * EF)

    Step 4 - 质量惩罚:
      if q < 3:
        重置: n = 0, I = 1, EF = max(1.3, EF * 0.8)

    质量评分 q:
      5 - 完美回忆
      4 - 正确但犹豫
      3 - 正确但困难
      2 - 错误，答案感觉熟悉
      1 - 错误，但答案记得
      0 - 完全忘记
    """

    def __init__(self):
        self.items: Dict[str, SM2Item] = {}
        self.MIN_EF = 1.3
        self.DEFAULT_EF = 2.5
        self.INITIAL_INTERVALS = {1: 1, 2: 6}

    def add_item(self, item_id: str, description: str, category: str = "default") -> SM2Item:
        item = SM2Item(
            item_id=item_id,
            description=description,
            category=category,
            interval_days=self.INITIAL_INTERVALS[1],
            ef=self.DEFAULT_EF,
            repetition_count=0
        )
        self.items[item_id] = item
        return item

    def review_item(self, item_id: str, quality: int,
                   review_time: Optional[datetime] = None) -> Dict:
        if item_id not in self.items:
            raise KeyError(f"Item {item_id} not found")

        item = self.items[item_id]
        review_time = review_time or datetime.now(timezone.utc)

        old_ef = item.ef
        old_interval = item.interval_days
        reset = False

        # Step 4: q < 3 → 重置（不改变 EF，原论文规定）
        if quality < 3:
            item.repetition_count = 0
            item.interval_days = self.INITIAL_INTERVALS[1]
            # EF 保持不变
            reset = True
        else:
            # SM-2 关键：先算新间隔（用旧 EF），再更新 EF
            # I(1)=1, I(2)=6, I(n)=ceil(I(n-1)*EF_old) for n>2
            item.repetition_count += 1
            if item.repetition_count == 1:
                item.interval_days = self.INITIAL_INTERVALS[1]
            elif item.repetition_count == 2:
                item.interval_days = self.INITIAL_INTERVALS[2]
            else:
                import math
                item.interval_days = max(1, math.ceil(old_interval * old_ef))

            # Step 2: 最后更新 EF
            item.ef = self._update_ef(old_ef, quality)

        item.last_review = review_time

        return {
            "item_id": item_id,
            "quality": quality,
            "old_ef": old_ef,
            "new_ef": item.ef,
            "old_interval": old_interval,
            "new_interval": item.interval_days,
            "repetition_count": item.repetition_count,
            "next_review": item.next_review_date(),
            "reset": reset
        }

    def _update_ef(self, old_ef: float, quality: int) -> float:
        """
        SM-2 EF 更新公式:
          EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))

        质量 q 对 EF 的影响:
          q=5 → Δ=+0.10  (完美，变易学)
          q=4 → Δ=+0.00  (正确但犹豫，不变)
          q=3 → Δ=-0.14  (困难，变难)
          q=2 → Δ=-0.32
          q=1 → Δ=-0.54
          q=0 → Δ=-0.80
        """
        delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        new_ef = old_ef + delta
        return max(self.MIN_EF, min(10.0, new_ef))

    def get_due_items(self, when: Optional[datetime] = None) -> Dict[str, SM2Item]:
        when = when or datetime.now(timezone.utc)
        return {aid: item for aid, item in self.items.items() if item.is_due(when)}

    def get_stats(self) -> Dict:
        total = len(self.items)
        due = len(self.get_due_items())
        avg_ef = sum(i.ef for i in self.items.values()) / total if total > 0 else 0
        avg_interval = sum(i.interval_days for i in self.items.values()) / total if total > 0 else 0
        return {
            "total_items": total,
            "due_today": due,
            "avg_ef": round(avg_ef, 2),
            "avg_interval_days": round(avg_interval, 1),
            "items_by_category": self._count_by_category()
        }

    def _count_by_category(self) -> Dict[str, int]:
        counts = {}
        for item in self.items.values():
            counts[item.category] = counts.get(item.category, 0) + 1
        return counts

    def to_dict(self) -> Dict:
        return {
            "items": {
                aid: {
                    "description": item.description,
                    "interval_days": item.interval_days,
                    "ef": item.ef,
                    "repetition_count": item.repetition_count,
                    "last_review": item.last_review.isoformat() if item.last_review else None,
                    "category": item.category
                }
                for aid, item in self.items.items()
            }
        }
