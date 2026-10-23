"""ECOS Governance Layer - 三省六部架构
"""

# 仅保留对外公共 API 的单一再导出，避免包 __init__ 在导入时
# 触发治理子模块 -> 包 __init__ 的循环导入。
# 其它符号 (CentralGovernment / Edict / Task / 六部 ...)
# 请直接从对应子模块导入，例如:
#   from ecos.governance.central_government import CentralGovernment
#   from ecos.governance.types import Edict, Task
#   from ecos.governance.governance_manager import GovernanceManager
from .governance_manager import GovernanceManager

__all__ = [
    "GovernanceManager",
]
