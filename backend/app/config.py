from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "MOF KG-Enhanced RAG FastAPI MVP"
    data_source_label: str = "AI4ChemS/MOF_ChemUnity public sample data"
    backend_dir: Path = Path(__file__).resolve().parents[1]

    @property
    def open_source_data_dir(self) -> Path:
        return self.backend_dir / "data" / "open_source"


@lru_cache
def get_settings() -> Settings:
    return Settings()
