import os

import pandas as pd
import pytest

from aok.core.datarequest import DataRequest
from aok.tests.column_requirements import REQUIRED_ATL03_COLUMNS

pytestmark = pytest.mark.integration


requires_sliderule = pytest.mark.skipif(
    os.getenv("RUN_SLIDERULE_INTEGRATION") != "1",
    reason="Set RUN_SLIDERULE_INTEGRATION=1 to run SlideRule integration tests.",
)


def dataframe_has_field(df: pd.DataFrame, field: str) -> bool:
    """
    Return True if a field exists either as a dataframe column or as the index name.

    SlideRule typically returns time_ns as the dataframe index rather than as a regular
    column, so required-field checks need to accept both forms.
    """
    return field in df.columns or df.index.name == field


def missing_required_fields(
    df: pd.DataFrame,
    required_fields: set[str],
) -> set[str]:
    """
    Return required fields that are missing from both columns and the index.
    """
    return {field for field in required_fields if not dataframe_has_field(df, field)}


@requires_sliderule
def test_sliderule_real_atl03_request_returns_photons():
    request = DataRequest(
        spatial=[
            {"lon": -76.319707, "lat": 34.895786},
            {"lon": -76.210123, "lat": 34.895786},
            {"lon": -76.210123, "lat": 34.985618},
            {"lon": -76.319707, "lat": 34.985618},
            {"lon": -76.319707, "lat": 34.895786},
        ],
        date_range=("2022-04-23", "2022-04-23"),
        need_atl03=True,
        need_atl24=False,
        need_gebco=False,
        need_shoreline=False,
    )

    result = request.get_sliderule_data()

    assert result is request
    assert request.photons is not None
    assert isinstance(request.photons, pd.DataFrame)
    assert len(request.photons) > 0

    assert request.products == ["ATL03"]
    assert request.sources == ["sliderule"]

    assert "ATL03" in request.metadata
    assert request.metadata["ATL03"]["request_type"] == "atl03"
    assert request.metadata["ATL03"]["n_rows"] == len(request.photons)

    assert dataframe_has_field(request.photons, "time_ns"), (
        "Expected time_ns to exist either as a column or as the dataframe index."
    )

    missing_fields = missing_required_fields(
        request.photons,
        REQUIRED_ATL03_COLUMNS,
    )

    assert not missing_fields, (
        "Real ATL03 SlideRule result is missing required fields: "
        f"{sorted(missing_fields)}"
    )
