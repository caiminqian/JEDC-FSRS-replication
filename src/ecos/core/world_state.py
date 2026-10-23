"""World State Graph - 动态异构图表示世界状态"""

import networkx as nx
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import uuid4
import json


class WorldStateGraph:
    """
    世界状态图 - 动态异构图

    节点类型:
      - market: 市场节点（价格、流动性）
      - human: 人类节点（行为、情绪）
      - institution: 机构节点
      - risk: 风险节点
      - asset: 资产节点（股票、加密、债券）

    边类型:
      - capital_flow: 资金流
      - info_flow: 信息流
      - risk_contagion: 风险传播
      - causation: 因果关系
    """

    def __init__(self, name: str = "World"):
        self.graph = nx.MultiDiGraph()
        self.name = name
        self.created_at = datetime.now()
        self.version = 0
        # 缓存市场节点 (symbol -> node_data)
        self._market_cache: Dict[str, Dict] = {}
        self._market_cache_valid = False  # 状态版本号（每次修改递增）

    def add_node(self, node_id: str, node_type: str, attributes: Dict[str, Any] = None) -> str:
        """添加节点"""
        if attributes is None:
            attributes = {}
        attributes.update({
            "type": node_type,
            "created_at": datetime.now().isoformat(),
            "version": self.version
        })
        self.graph.add_node(node_id, **attributes)
        self.version += 1
        self._invalidate_market_cache()
        return node_id

    def add_edge(self, from_id: str, to_id: str, edge_type: str, **attrs) -> str:
        """添加边（关系）"""
        edge_id = str(uuid4())
        attrs.update({
            "type": edge_type,
            "created_at": datetime.now().isoformat()
        })
        self.graph.add_edge(from_id, to_id, key=edge_id, **attrs)
        self.version += 1
        return edge_id

    def get_node(self, node_id: str) -> Optional[Dict]:
        """获取节点"""
        if self.graph.has_node(node_id):
            return dict(self.graph.nodes[node_id])
        return None

    def update_node(self, node_id: str, attributes: Dict[str, Any], invalidate_cache: bool = True):
        """更新节点属性

        Args:
            node_id: 节点ID
            attributes: 属性字典
            invalidate_cache: 是否失效市场缓存（批量更新时可设为 False）
        """
        if self.graph.has_node(node_id):
            self.graph.nodes[node_id].update(attributes)
            self.graph.nodes[node_id]["version"] = self.version
            self.version += 1
            if invalidate_cache:
                self._invalidate_market_cache()

    def remove_node(self, node_id: str):
        """删除节点（及关联的边）"""
        if self.graph.has_node(node_id):
            self.graph.remove_node(node_id)
            self.version += 1
            self._invalidate_market_cache()

    def get_market_data(self) -> Dict[str, Dict]:
        """
        获取所有市场节点的数据（缓存）

        Returns:
            {symbol: {price, change, volume, liquidity, ...}}
        """
        if not self._market_cache_valid:
            self._rebuild_market_cache()
        return self._market_cache

    def _rebuild_market_cache(self):
        """重建市场数据缓存（每 tick 调用一次）"""
        self._market_cache.clear()
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == "market":
                symbol = data.get("symbol")
                if not symbol:
                    # 从 node_id 提取 symbol (e.g. 'market:BTC' -> 'BTC')
                    symbol = node_id.split(":", 1)[-1] if ":" in node_id else node_id
                self._market_cache[symbol] = dict(data)
        self._market_cache_valid = True

    def _invalidate_market_cache(self):
        """标记缓存失效（节点增删改时调用）"""
        self._market_cache_valid = False

    def get_delta_snapshot(self, since_version: int = None):
        """获取增量快照（简化返回全量）"""
        if since_version is None:
            return {
                "nodes": [{"id": n, **d} for n, d in self.graph.nodes(data=True)],
                "edges": [{"from": u, "to": v, "key": k, **d}
                          for u, v, k, d in self.graph.edges(keys=True, data=True)],
                "version": self.version
            }
        return self.get_delta_snapshot(None)

    def apply_delta(self, delta):
        """应用增量更新"""
        for node in delta.get("nodes_added", []):
            nid = node.pop("id")
            ntype = node.pop("type")
            self.add_node(nid, ntype, node)
        for edge in delta.get("edges_added", []):
            u = edge.pop("from")
            v = edge.pop("to")
            key = edge.pop("key")
            etype = edge.pop("type")
            self.add_edge(u, v, etype, **edge)

    def persist_to_neo4j(self, driver, batch_size: int = 100):
        """批量持久化到 Neo4j"""
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            for node_id, data in self.graph.nodes(data=True):
                node_type = data.get('type', 'unknown')
                labels = ['Node', node_type.capitalize()]
                props = {k: v for k, v in data.items() if k not in ['type']}
                props['id'] = node_id
                query = 'CREATE (n:' + ':'.join(labels) + ' {props})'
                session.run(query, props=props)
            for u, v, key, data in self.graph.edges(keys=True, data=True):
                edge_type = data.get('type', 'RELATED').upper()
                props = {k: v for k, v in data.items() if k not in ['type']}
                query = 'MATCH (a {id: $u}), (b {id: $v}) CREATE (a)-[r:' + edge_type + ' {props}]->(b)'
                session.run(query, u=u, v=v, props=props)
        print('[Neo4j] Persisted', self.graph.number_of_nodes(), 'nodes,', self.graph.number_of_edges(), 'edges')

    def get_edges(self, node_id: str, edge_type: str = None) -> List[tuple]:
        """获取从节点出发的边"""
        edges = []
        for u, v, key, data in self.graph.out_edges(node_id, keys=True, data=True):
            if edge_type is None or data.get("type") == edge_type:
                edges.append((v, key, data))
        return edges

    def get_subgraph(self, node_type: str) -> nx.MultiDiGraph:
        """获取特定类型节点的子图"""
        nodes = [n for n, d in self.graph.nodes(data=True)
                 if d.get("type") == node_type]
        return self.graph.subgraph(nodes)

    def get_nodes_by_type(self, node_type: str) -> List[str]:
        """获取指定类型的所有节点ID"""
        return [n for n, d in self.graph.nodes(data=True)
                if d.get("type") == node_type]

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（用于传输/存储）"""
        return {
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "nodes": [
                {"id": n, **d}
                for n, d in self.graph.nodes(data=True)
            ],
            "edges": [
                {
                    "from": u,
                    "to": v,
                    "key": k,
                    **data
                }
                for u, v, k, data in self.graph.edges(keys=True, data=True)
            ]
        }

    def to_networkx(self) -> nx.MultiDiGraph:
        """获取 NetworkX 图对象"""
        return self.graph

    def clear(self):
        """清空图"""
        self.graph.clear()
        self.version = 0

    def stats(self) -> Dict[str, Any]:
        """图统计信息"""
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "version": self.version,
            "node_types": self._count_node_types(),
            "edge_types": self._count_edge_types()
        }

    def _count_node_types(self) -> Dict[str, int]:
        counts = {}
        for n, d in self.graph.nodes(data=True):
            t = d.get("type", "unknown")
            counts[t] = counts.get(t, 0) + 1
        return counts

    def _count_edge_types(self) -> Dict[str, int]:
        counts = {}
        for u, v, k, d in self.graph.edges(keys=True, data=True):
            t = d.get("type", "unknown")
            counts[t] = counts.get(t, 0) + 1
        return counts

    def save(self, filepath: str):
        """保存到 JSON 文件"""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load(cls, filepath: str) -> "WorldStateGraph":
        """从 JSON 文件加载"""
        with open(filepath, "r") as f:
            data = json.load(f)

        world = cls(name=data.get("name", "Loaded World"))
        world.version = data.get("version", 0)
        world.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))

        # 加载节点
        for node in data.get("nodes", []):
            node_id = node.pop("id")
            world.graph.add_node(node_id, **node)

        # 加载边
        for edge in data.get("edges", []):
            from_id = edge.pop("from")
            to_id = edge.pop("to")
            key = edge.pop("key")
            world.graph.add_edge(from_id, to_id, key=key, **edge)

        return world
