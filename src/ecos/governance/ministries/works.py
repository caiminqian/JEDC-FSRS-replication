"""工部 (Works Ministry) - 基础设施建设
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InfrastructureProject:
    """基建项目"""
    project_id: str
    name: str
    project_type: str     # "new_market", "upgrade", "bridge"
    cost: float
    progress: float = 0.0  # 0-100%
    start_tick: int = 0
    duration: int = 100    # ticks
    status: str = "planned"  # planned/construction/completed


class WorksMinistry:
    """
    工部 - 工程司
    
    职责:
    1. 新建交易所/市场
    2. 升级基础设施（提高吞吐量、降低延迟）
    3. 建设跨市场桥梁（资产通道）
    4. 维护现有设施
    
    项目类型:
    - 新市场建设（新交易对）
    - 数据中心升级
    - 网络优化
    """
    
    def __init__(self, world):
        self.world = world
        self.projects: Dict[str, InfrastructureProject] = {}
        self.completed_projects: List[InfrastructureProject] = []
        self.project_counter = 0
        
    def propose_project(self, name: str, project_type: str, cost: float, duration: int) -> str:
        """
        提议基建项目（需户部拨款）
        
        Returns:
            project_id
        """
        project_id = f"PROJ_{self.project_counter:04d}"
        self.project_counter += 1
        
        project = InfrastructureProject(
            project_id=project_id,
            name=name,
            project_type=project_type,
            cost=cost,
            start_tick=0,
            duration=duration,
            status="planned"
        )
        self.projects[project_id] = project
        print(f"  [工部] 项目提案: {name} (成本 ${cost:,.0f})")
        return project_id
    
    def start_project(self, project_id: str):
        """启动项目"""
        if project_id in self.projects:
            self.projects[project_id].status = "construction"
            self.projects[project_id].start_tick = 0  # TODO: current tick
            print(f"  [工部] 项目开工: {self.projects[project_id].name}")
    
    def update_projects(self, current_tick: int):
        """更新所有项目进度"""
        for project_id, project in list(self.projects.items()):
            if project.status != "construction":
                continue
            
            # 进度推进
            ticks_elapsed = current_tick - project.start_tick
            project.progress = (ticks_elapsed / project.duration) * 100
            
            if project.progress >= 100:
                project.status = "completed"
                self.completed_projects.append(project)
                del self.projects[project_id]
                print(f"  [工部] 项目竣工: {project.name}")
    
    def build_new_market(self, symbol: str, initial_price: float) -> bool:
        """
        新建一个市场（工部直接执行）
        
        Returns:
            是否成功
        """
        # 成本：100 万
        cost = 1e6
        
        # 检查是否已存在
        if self.world.graph.has_node(f"market:{symbol}"):
            print(f"  [工部] 市场 {symbol} 已存在")
            return False
        
        # 检查资金（需户部拨款，这里简化直接扣国库？）
        # TODO: 调用户部拨款
        
        # 创建市场节点
        self.world.add_node(
            f"market:{symbol}",
            "market",
            {
                "symbol": symbol,
                "price": initial_price,
                "change": 0.0,
                "volume": 1e6,
                "liquidity": 1.0,
                "created_by": "工部"
            }
        )
        print(f"  [工部] 新建市场: {symbol} @ ${initial_price:,.2f}")
        return True
    
    def get_project_status(self) -> Dict:
        return {
            "active_projects": len(self.projects),
            "completed_projects": len(self.completed_projects),
            "total_investment": sum(p.cost for p in self.completed_projects),
            "active_details": [
                {"id": p.project_id, "name": p.name, "progress": f"{p.progress:.1f}%"}
                for p in self.projects.values()
            ]
        }

    def perform_maintenance(self) -> Dict:
        """
        执行系统维护（定期清理、升级）
        """
        result = {
            "action": "maintenance",
            "projects_completed": 0,
            "cost": 0
        }
        
        # 完成一个待命的基础设施项目
        if self.projects:
            # 推进所有项目进度
            for project in self.projects.values():
                project.progress += 10  # 每次维护 +10%
                if project.progress >= 100:
                    project.progress = 100
                    self.completed_projects.append(project)
                    result["projects_completed"] += 1
                    result["cost"] += project.cost
            
            # 移除已完成项目
            self.projects = {pid: p for pid, p in self.projects.items() if p.progress < 100}
        else:
            # 如果没有项目，创建一个维护项目
            pid = self.propose_project(
                name="系统维护",
                project_type="maintenance",
                cost=10000,
                duration=10
            )
            self.start_project(pid)
            result["action"] = "initiated_maintenance_project"
        
        return result

def get_performance_metrics(self) -> Dict:
    return self.get_project_status()

__all__ = ["WorksMinistry", "InfrastructureProject"]
