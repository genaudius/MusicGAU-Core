from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import Column, Integer, String, Text, UniqueConstraint, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


class ApiCache(Base):
    __tablename__ = "api_cache"
    __table_args__ = (UniqueConstraint("namespace", "key", name="uq_namespace_key"),)

    id = Column(Integer, primary_key=True)
    namespace = Column(String(64), nullable=False)
    key = Column(String(512), nullable=False)
    value_json = Column(Text, nullable=False)
    created_at = Column(Integer, nullable=False)


@dataclass(frozen=True)
class CacheDB:
    path: Path

    def _engine(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(f"sqlite:///{self.path}", future=True)

    def init(self) -> None:
        eng = self._engine()
        Base.metadata.create_all(eng)

    def get(self, namespace: str, key: str) -> Optional[dict[str, Any]]:
        eng = self._engine()
        with Session(eng) as s:
            stmt = select(ApiCache).where(ApiCache.namespace == namespace, ApiCache.key == key)
            row = s.execute(stmt).scalar_one_or_none()
            if row is None:
                return None
            return json.loads(row.value_json)

    def set(self, namespace: str, key: str, value: dict[str, Any]) -> None:
        eng = self._engine()
        payload = json.dumps(value, ensure_ascii=False)
        now = int(time.time())
        with Session(eng) as s:
            stmt = select(ApiCache).where(ApiCache.namespace == namespace, ApiCache.key == key)
            row = s.execute(stmt).scalar_one_or_none()
            if row is None:
                row = ApiCache(namespace=namespace, key=key, value_json=payload, created_at=now)
                s.add(row)
            else:
                row.value_json = payload
            s.commit()

