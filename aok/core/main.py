from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any

from .calculate_kdph import CalculateKdph
from .config import KdConfig, get_args
from .datarequest import DataRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AOKPipeline:
    """Config-driven Kd pipeline object for notebooks and CLI use."""

    def __init__(self, args: KdConfig | Any):
        self.workspace_path = getattr(args, "workspace_path", None)
        if isinstance(args, KdConfig):
            self.args = args
        elif isinstance(args, dict):
            self.args = KdConfig(**args)
        elif hasattr(args, "__dict__"):
            self.args = KdConfig(**vars(args))
        else:
            self.args = KdConfig.model_validate(args)

        output_path = Path(self.args.output_path)
        if not output_path.is_absolute() and self.workspace_path:
            output_path = Path(self.workspace_path) / output_path
        self.output_path = str(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        self.timestamp = self._infer_timestamp()
        self.kdph = CalculateKdph(self.args)

    def _infer_timestamp(self) -> str:
        if hasattr(self.args, "atl03_file") and self.args.atl03_file:
            match = re.search(r"ATL03_(\d{14})", str(self.args.atl03_file))
            if match:
                return match.group(1)
        return "unknown"

    def run(self):
        logger.info("Starting Kd pipeline for %s", self.timestamp)
        logger.info("Output directory: %s", self.output_path)

        request = DataRequest(
            spatial=self.args.spatial,
            date_range=(
                str(self.args.temporal[0])[:10],
                str(self.args.temporal[1])[:10],
            ),
            need_atl03=True,
            need_atl24=True,
            get_gebco=True,
            atl03_version=self.args.atl03_version,
        )
        acquired = request.get_sliderule_data()
        photons = acquired.photons if isinstance(acquired, DataRequest) else acquired

        return {
            "timestamp": self.timestamp,
            "output_path": self.output_path,
            "config": self.args.model_dump(mode="json"),
            "products": request.products,
            "sources": request.sources,
            "metadata": request.metadata,
            "photons": photons,
            "kd": None,
            "stage_diagnostics": {},
        }


def run_pipeline(args: KdConfig | Any):
    """Library-facing API used by notebooks and tests."""
    return AOKPipeline(args).run()


if __name__ == "__main__":
    kd_args = get_args()
    try:
        run_pipeline(kd_args)
    except Exception as exc:  # pragma: no cover - CLI guard only
        logger.error("An error occurred: %s", exc)
        raise
