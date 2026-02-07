"""
SimpleMem-inspired memory system for Daily Feed
Efficient lifelong memory with semantic compression
"""

import json
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3

from app.config import get_settings

settings = get_settings()


@dataclass
class MemoryUnit:
    """
    A compact memory unit representing an atomic fact/memory.
    Inspired by SimpleMem's semantic structured compression.
    """
    id: str
    content: str  # The compressed, self-contained fact
    timestamp: datetime
    source: str  # Where this memory came from
    category: str  # Topic/category
    entities: List[str]  # Named entities mentioned
    importance: float  # 0-1 importance score
    access_count: int = 0  # For recency-based ranking
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "category": self.category,
            "entities": self.entities,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryUnit":
        return cls(
            id=data["id"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data["source"],
            category=data["category"],
            entities=data["entities"],
            importance=data["importance"],
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None,
        )


class SimpleMemStore:
    """
    SimpleMem-inspired memory store with:
    - Semantic structured compression
    - Online semantic synthesis
    - Intent-aware retrieval planning
    """
    
    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for memory storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_units (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    category TEXT NOT NULL,
                    entities TEXT NOT NULL,  -- JSON array
                    importance REAL DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    embedding BLOB  -- For future vector search
                )
            """)
            
            # Index for efficient retrieval
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_category 
                ON memory_units(category)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_timestamp 
                ON memory_units(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_importance 
                ON memory_units(importance DESC)
            """)
            
            # Synthesis tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS synthesis_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_ids TEXT NOT NULL,  -- JSON array of merged unit IDs
                    result_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    reason TEXT
                )
            """)
            
            conn.commit()
    
    def _generate_id(self, content: str, timestamp: datetime) -> str:
        """Generate unique ID for memory unit."""
        data = f"{content}:{timestamp.isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    def store(
        self,
        content: str,
        source: str,
        category: str = "general",
        entities: Optional[List[str]] = None,
        importance: float = 0.5
    ) -> MemoryUnit:
        """
        Store a new memory unit.
        Applies semantic compression to create atomic, self-contained fact.
        """
        timestamp = datetime.now(timezone.utc)
        unit_id = self._generate_id(content, timestamp)
        
        unit = MemoryUnit(
            id=unit_id,
            content=content,
            timestamp=timestamp,
            source=source,
            category=category,
            entities=entities or [],
            importance=max(0.0, min(1.0, importance))
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO memory_units 
                (id, content, timestamp, source, category, entities, importance, access_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                unit.id,
                unit.content,
                unit.timestamp.isoformat(),
                unit.source,
                unit.category,
                json.dumps(unit.entities),
                unit.importance,
                unit.access_count,
                None
            ))
            conn.commit()
        
        return unit
    
    def retrieve(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        entities: Optional[List[str]] = None,
        limit: int = 10,
        min_importance: float = 0.0,
        time_range_days: Optional[int] = None
    ) -> List[MemoryUnit]:
        """
        Intent-aware retrieval with multi-view matching.
        
        Retrieves memories based on:
        - Semantic similarity (content match)
        - Lexical matching (entity overlap)
        - Symbolic filtering (category, time, importance)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Build query dynamically based on intent
            where_clauses = ["importance >= ?"]
            params = [min_importance]
            
            if category:
                where_clauses.append("category = ?")
                params.append(category)
            
            if time_range_days:
                cutoff = (datetime.now(timezone.utc) - timedelta(days=time_range_days)).isoformat()
                where_clauses.append("timestamp >= ?")
                params.append(cutoff)
            
            # Execute retrieval
            query_sql = f"""
                SELECT * FROM memory_units 
                WHERE {' AND '.join(where_clauses)}
                ORDER BY importance DESC, timestamp DESC
                LIMIT ?
            """
            params.append(limit * 2)  # Fetch more for filtering
            
            rows = conn.execute(query_sql, params).fetchall()
            
            units = []
            for row in rows:
                unit = MemoryUnit(
                    id=row["id"],
                    content=row["content"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    source=row["source"],
                    category=row["category"],
                    entities=json.loads(row["entities"]),
                    importance=row["importance"],
                    access_count=row["access_count"],
                    last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None
                )
                
                # Score based on entity overlap if entities provided
                if entities:
                    entity_overlap = len(set(unit.entities) & set(entities))
                    if entity_overlap > 0 or not query:
                        units.append((unit, entity_overlap + unit.importance))
                else:
                    units.append((unit, unit.importance))
            
            # Sort by combined score and return top results
            units.sort(key=lambda x: x[1], reverse=True)
            result = [u[0] for u in units[:limit]]
            
            # Update access count for retrieved units
            for unit in result:
                self._touch_unit(unit.id)
            
            return result
    
    def _touch_unit(self, unit_id: str):
        """Update access timestamp and count."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE memory_units 
                SET access_count = access_count + 1, last_accessed = ?
                WHERE id = ?
            """, (datetime.now(timezone.utc).isoformat(), unit_id))
            conn.commit()
    
    def synthesize(
        self,
        unit_ids: List[str],
        consolidated_content: str,
        reason: str = "semantic_similarity"
    ) -> MemoryUnit:
        """
        Online semantic synthesis - merge related memories into higher-level abstraction.
        
        This implements SimpleMem's Stage 2: Online Semantic Synthesis.
        Related memory units are synthesized into unified abstract representations.
        """
        # Get source units
        sources = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            for uid in unit_ids:
                row = conn.execute(
                    "SELECT * FROM memory_units WHERE id = ?", (uid,)
                ).fetchone()
                if row:
                    sources.append(row)
        
        if not sources:
            raise ValueError("No source units found for synthesis")
        
        # Create synthesized unit
        categories = set(s["category"] for s in sources)
        entities = set()
        for s in sources:
            entities.update(json.loads(s["entities"]))
        
        # Calculate aggregated importance
        avg_importance = sum(s["importance"] for s in sources) / len(sources)
        
        # Store new synthesized unit
        new_unit = self.store(
            content=consolidated_content,
            source=f"synthesis:{','.join(unit_ids)}",
            category=list(categories)[0] if len(categories) == 1 else "general",
            entities=list(entities),
            importance=min(1.0, avg_importance * 1.1)  # Boost importance slightly
        )
        
        # Log synthesis
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO synthesis_log (source_ids, result_id, timestamp, reason)
                VALUES (?, ?, ?, ?)
            """, (
                json.dumps(unit_ids),
                new_unit.id,
                datetime.now(timezone.utc).isoformat(),
                reason
            ))
            conn.commit()
        
        return new_unit
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memory_units").fetchone()[0]
            
            category_dist = conn.execute("""
                SELECT category, COUNT(*) as count 
                FROM memory_units 
                GROUP BY category
            """).fetchall()
            
            recent = conn.execute("""
                SELECT COUNT(*) FROM memory_units 
                WHERE timestamp >= ?
            """, ((datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),)).fetchone()[0]
            
            avg_importance = conn.execute("""
                SELECT AVG(importance) FROM memory_units
            """).fetchone()[0] or 0
            
            return {
                "total_units": total,
                "recent_7d": recent,
                "category_distribution": {c: n for c, n in category_dist},
                "avg_importance": round(avg_importance, 3),
            }
    
    def get_recent(self, days: int = 7, category: Optional[str] = None) -> List[MemoryUnit]:
        """Get recent memories."""
        return self.retrieve(
            time_range_days=days,
            category=category,
            limit=50
        )
    
    def clear_old(self, days: int = 30, min_importance: float = 0.3):
        """Clear old, low-importance memories."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM memory_units 
                WHERE timestamp < ? AND importance < ?
            """, (cutoff, min_importance))
            conn.commit()


# Article-specific memory extensions
class ArticleMemory(SimpleMemStore):
    """Memory store specialized for article tracking."""
    
    def remember_article(
        self,
        article_id: int,
        title: str,
        summary: str,
        category: str,
        source: str,
        key_points: List[str]
    ) -> MemoryUnit:
        """
        Store article information in memory.
        Compresses article into atomic memory unit.
        """
        # Extract entities (simplified - in production use NER)
        entities = self._extract_entities(title + " " + summary)
        
        # Create compressed content
        content = f"Article: {title}. Summary: {summary}"
        if key_points:
            content += f" Key points: {'; '.join(key_points[:3])}"
        
        return self.store(
            content=content,
            source=f"article:{article_id}",
            category=category,
            entities=entities,
            importance=0.6  # Articles have moderate importance
        )
    
    def find_similar_articles(
        self,
        title: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[MemoryUnit]:
        """Find articles similar to given title."""
        entities = self._extract_entities(title)
        
        return self.retrieve(
            entities=entities,
            category=category,
            limit=limit,
            time_range_days=30  # Look at last 30 days
        )
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Simple entity extraction (placeholder for NER).
        In production, use spaCy or LLM-based NER.
        """
        # Simple approach: extract capitalized phrases
        import re
        words = re.findall(r'\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\b', text)
        # Filter common false positives
        stop_words = {'The', 'A', 'An', 'This', 'That', 'These', 'Those'}
        return list(set(w for w in words if w not in stop_words))[:10]
    
    def get_user_interests(self) -> Dict[str, float]:
        """
        Analyze memory to determine user interests.
        Returns category -> interest score mapping.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get category counts weighted by access
            rows = conn.execute("""
                SELECT category, 
                       COUNT(*) as count,
                       SUM(access_count) as total_access,
                       AVG(importance) as avg_importance
                FROM memory_units 
                WHERE source LIKE 'article:%'
                GROUP BY category
            """).fetchall()
            
            interests = {}
            for row in rows:
                # Calculate interest score
                score = (
                    row["count"] * 0.3 +
                    row["total_access"] * 0.5 +
                    row["avg_importance"] * 20
                )
                interests[row["category"]] = round(score, 2)
            
            return dict(sorted(interests.items(), key=lambda x: x[1], reverse=True))


# Global memory instance
_memory_store: Optional[ArticleMemory] = None


def get_memory_store() -> ArticleMemory:
    """Get global memory store instance."""
    global _memory_store
    if _memory_store is None:
        _memory_store = ArticleMemory()
    return _memory_store
