from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
import yaml

TEMPORAL_RANGE_LENGTH = 2
PLACEHOLDER_DATE = datetime(2000, 1, 1)
SPATIAL_BOUNDS_ERROR = "spatial bounds cannot be the zeroed default extent"
TEMPORAL_BOUNDS_ERROR = "temporal bounds cannot be the placeholder date range"
HORIZONTAL_RES_ERROR = "horizontal_res must be positive"
VERTICAL_RES_ERROR = "vertical_res must be positive"


class KdConfig(BaseModel):
    """Validated configuration for the AOK Kd pipeline.

    This keeps the YAML file as the canonical run contract while ensuring the
    library API and CLI entrypoint use the same validated schema.
    """

    model_config = ConfigDict(validate_assignment=True, extra="ignore")

    output_path: str | Path = Field(default="./results/")
    horizontal_res: int = Field(default=500)
    vertical_res: float = Field(default=0.25)
    subsurface_thresh: float | None = Field(default=1.0)
    ignore_subsurface_height_thres: float | None = Field(default=-6.0)
    solar_bg_filter: bool = Field(default=True)
    solar_elev_threshold: float = Field(default=6.0)
    solar_bg_median_window_deg: float = Field(default=10.0)
    solar_bg_noise_multiplier: float = Field(default=1.5)
    solar_bg_min_signal_conf: int = Field(default=2)
    spatial: list[float] = Field(
        default_factory=lambda: [-150.622053, 61.045382, -150.361757, 61.171146]
    )
    temporal: list[str | datetime] = Field(
        default_factory=lambda: ["2025-08-21", "2025-08-22"]
    )
    atl03_version: str | None = None
    decay_zone_threshold: float = Field(default=0.0)
    kd_fit_method: str = Field(default="log_linear")
    generate_plots: bool = Field(default=False)

    @property
    def output_dir(self) -> Path:
        return Path(self.output_path)

    def normalize(self) -> KdConfig:
        """Normalize YAML values into a consistent runtime config."""
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)
        if len(self.temporal) == TEMPORAL_RANGE_LENGTH:
            self.temporal = [
                datetime.fromisoformat(str(item))
                if not isinstance(item, datetime)
                else item
                for item in self.temporal
            ]
        return self


def check_config_values(config: KdConfig) -> None:
    """Minimal validation guardrails for the top-level config contract."""
    if config.spatial == [0.0] * 4:
        raise ValueError(SPATIAL_BOUNDS_ERROR)

    if len(config.temporal) == TEMPORAL_RANGE_LENGTH and all(
        item in (PLACEHOLDER_DATE, PLACEHOLDER_DATE.date().isoformat())
        for item in config.temporal
    ):
        raise ValueError(TEMPORAL_BOUNDS_ERROR)

    if config.horizontal_res <= 0:
        raise ValueError(HORIZONTAL_RES_ERROR)

    if config.vertical_res <= 0:
        raise ValueError(VERTICAL_RES_ERROR)


def get_args(config_path: str | Path | None = None) -> KdConfig:
    """Load the runtime config from YAML and return a validated KdConfig."""
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "config.yaml"
    config_path = Path(config_path)

    with config_path.open("r", encoding="utf-8") as fh:
        raw_config: dict[str, Any] = yaml.safe_load(fh) or {}

    config = KdConfig(**raw_config)
    check_config_values(config)
    return config
