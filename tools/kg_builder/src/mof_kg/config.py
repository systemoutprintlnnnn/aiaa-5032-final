"""Configuration for MOF KG Builder"""
from pathlib import Path
from pydantic import BaseModel


class Config(BaseModel):
    """Runtime configuration"""
    # Project root directory
    project_dir: Path = Path(__file__).resolve().parents[4]

    # Source data directory
    data_dir: Path = project_dir / "reference_code" / "MOF_KG"
    water_stability_path: Path = data_dir / "1.water_stability_chemunity_v0.1.0.csv"
    name_mapping_path: Path = data_dir / "2.MOF_names_and_CSD_codes.csv"
    synthesis_path: Path = data_dir / "3.MOF-Synthesis.json"

    # Output directories
    output_dir: Path = project_dir / "backend" / "data" / "kg"
    kg_output_dir: Path = output_dir
    dataset_output_dir: Path = output_dir / "dataset"

    class Config:
        arbitrary_types_allowed = True


def get_config() -> Config:
    config = Config()
    # Ensure output directories exist
    config.kg_output_dir.mkdir(parents=True, exist_ok=True)
    config.dataset_output_dir.mkdir(parents=True, exist_ok=True)
    return config
