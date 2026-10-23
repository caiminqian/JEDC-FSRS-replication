"""户部 (Finance Ministry) - 国库与财政
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Budget:
    """国家预算"""
    fiscal_year: int
    revenue_estimates: float      # 预计收入
    expenditure_estimates: float  # 预计支出
    deficit_budget: float = 0.0   # 赤字预算
    treasury_bond_issuance: float = 0.0  # 国债发行额


class FinanceMinistry:
    """
    户部 - 财政司
    
    职责:
    1. 管理国库（Treasury）
    2. 征收交易税（对每个 Agent 的交易征税）
    3. 发行国债（融资）
    4. 执行预算（拨款给各部）
    5. 统计财政报表
    """
    
    def __init__(self, initial_treasury: float = 1e6, agents: List = None):
        self.treasury = initial_treasury
        self.fiscal_year = datetime.now().year
        self.budget = None
        self.tax_rates = {
            "trade": 0.001,     # 交易税 0.1%
            "profit": 0.20,     # 所得税 20%
            "capital_gains": 0.15,  # 资本利得税 15%
        }
        self.total_tax_collected = 0.0
        self.bond_issuance_count = 0
        self.agents = agents or []
        
    def collect_taxes(self) -> float:
        """征收税款（从内部 agents 列表）"""
        tax_revenue = 0.0
        
        for agent in self.agents:
            # 1. 交易税：每笔交易金额的 0.1%
            trades = agent.get_trade_history(last_n=10)
            for trade in trades:
                trade_amount = trade.get("price", 0) * trade.get("quantity", 0)
                tax = trade_amount * self.tax_rates["trade"]
                tax_revenue += tax
            
            # 2. 利润税：基于正收益
            total_pnl = agent.stats.get("rewards", 0)
            if total_pnl > 0:
                tax = total_pnl * self.tax_rates["profit"]
                tax_revenue += tax
        
        self.treasury += tax_revenue
        self.total_tax_collected += tax_revenue
        return tax_revenue
    
    def issue_bonds(self, amount: float, maturity: int = 100) -> str:
        """
        发行国债
        
        Args:
            amount: 发行规模
            maturity: 到期期限 (ticks)
            
        Returns:
            bond_id
        """
        bond_id = f"BOND_{self.bond_issuance_count:04d}_{datetime.now().strftime('%Y%m%d')}"
        self.bond_issuance_count += 1
        
        # 国债收入进入国库
        self.treasury += amount
        
        # TODO: 记录国债待偿还
        print(f"  [户部] 发行国债 {bond_id}: {amount:,.0f}")
        
        return bond_id
    
    def allocate_budget(self, ministry: str, amount: float) -> bool:
        """
        预算拨款给六部
        
        Args:
            ministry: 部门名称
            amount: 拨款金额
            
        Returns:
            是否拨款成功
        """
        if self.treasury >= amount:
            self.treasury -= amount
            print(f"  [户部] 拨款 {amount:,.0f} -> {ministry}")
            return True
        else:
            print(f"  [户部] 拨款失败: 国库不足 {self.treasury:,.0f} < {amount:,.0f}")
            return False
    
    def create_annual_budget(self) -> Budget:
        """制定年度预算"""
        # 简单估算：基于当前经济规模
        gdp_estimate = self._estimate_gdp()
        revenue_ratio = 0.15  # 税收占 GDP 15%
        expenditure_ratio = 0.18  # 支出占 GDP 18%
        
        self.budget = Budget(
            fiscal_year=self.fiscal_year,
            revenue_estimates=gdp_estimate * revenue_ratio,
            expenditure_estimates=gdp_estimate * expenditure_ratio,
            deficit_budget=gdp_estimate * (expenditure_ratio - revenue_ratio)
        )
        
        print(f"  [户部] {self.fiscal_year} 年度预算: 收入 {self.budget.revenue_estimates:,.0f}, 支出 {self.budget.expenditure_estimates:,.0f}")
        return self.budget
    
    def _estimate_gdp(self) -> float:
        """估算 GDP（所有 Agent 的总交易额 + 资产价值）"""
        # 粗略估算
        total_volume = 1e8  # placeholder
        return total_volume
    
    def get_financial_report(self) -> Dict:
        """财政报告"""
        return {
            "treasury_balance": self.treasury,
            "fiscal_year": self.fiscal_year,
            "total_tax_collected": self.total_tax_collected,
            "budget": {
                "revenue": self.budget.revenue_estimates if self.budget else 0,
                "expenditure": self.budget.expenditure_estimates if self.budget else 0,
                "deficit": self.budget.deficit_budget if self.budget else 0,
            },
            "bond_issuance_count": self.bond_issuance_count
        }

    def get_performance_metrics(self) -> Dict:
        """户部绩效指标"""
        return {
            "treasury_balance": self.treasury,
            "tax_collected": self.total_tax_collected,
            "bonds_issued": self.bond_issuance_count,
            "budget_utilization": (self.budget.expenditure_estimates / max(1, self.budget.revenue_estimates)) if self.budget else 0
        }


__all__ = ["FinanceMinistry", "Budget"]
