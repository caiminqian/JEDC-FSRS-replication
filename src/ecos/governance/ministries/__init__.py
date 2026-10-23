"""六部 (Ministries) - ECOS 政府执行机构
"""

from .personnel import PersonnelMinistry
from .finance import FinanceMinistry
from .ritual import RitualMinistry
from .military import MilitaryMinistry
from .justice import JusticeMinistry
from .works import WorksMinistry

__all__ = [
    "PersonnelMinistry",
    "FinanceMinistry",
    "RitualMinistry",
    "MilitaryMinistry",
    "JusticeMinistry",
    "WorksMinistry",
]
