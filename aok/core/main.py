from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any

from .config import KdConfig, get_args

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AOKPipeline:
    """Minimal pipeline object that keeps the config-driven API stable.

    The project is in transition from the older local file workflow to the
    modular SlideRule-and-GeoDataFrame pipeline described in the staging plan.
    This class preserves the public entrypoint pattern used by the tests while
    keeping the implementation rooted in the validated config contract.
    """

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

    def _infer_timestamp(self) -> str:
        if hasattr(self.args, "atl03_file") and self.args.atl03_file:
            match = re.search(r"ATL03_(\d{14})", str(self.args.atl03_file))
            if match:
                return match.group(1)

        return "unknown"

    def run(self):
        """Run the config-driven pipeline.

        This is intentionally a compatibility layer for the current project state:
        it validates the config contract, prepares the output directory, and
        returns a structured result that can be extended by the modular pipeline as
        each checkpoint is implemented.
        """
        logger.info("Starting Kd pipeline for %s", self.timestamp)
        logger.info("Output directory: %s", self.output_path)

        return {
            "timestamp": self.timestamp,
            "output_path": self.output_path,
            "config": self.args.model_dump(mode="json")
            if hasattr(self.args, "model_dump")
            else dict(self.args),
        }


def run_pipeline(args: KdConfig | Any):
    """Library-facing wrapper used by notebooks and tests.

    A pipeline object is created from the validated configuration and executed.
    This wrapper keeps the front-end API stable while the underlying workflow is
    being migrated to the modular data-acquisition + GeoDataFrame architecture.
    """
    pipeline = AOKPipeline(args)
    return pipeline.run()


if __name__ == "__main__":
    kd_args = get_args()
    try:
        run_pipeline(kd_args)
    except Exception as exc:  # pragma: no cover - CLI guard only
        logger.error("An error occurred: %s", exc)
        raise
