from argparse import Namespace

import pytest

from aok.core.acquisition.base import DataRequest
from aok.core.acquisition.request_data import get_data_from_cloud


@pytest.fixture
def fake_icepyx_backend():
    called = {}

    def _fake_icepyx_download(request, **kwargs):
        called["backend"] = "icepyx"
        called["request"] = request
        called["kwargs"] = kwargs
        return "icepyx_result"

    return called, _fake_icepyx_download


@pytest.fixture
def fake_sliderule_backend():
    called = {}

    def _fake_sliderule_download(request, **kwargs):
        called["backend"] = "sliderule"
        called["request"] = request
        called["kwargs"] = kwargs
        return "sliderule_result"

    return called, _fake_sliderule_download


def test_get_data_from_cloud_dispatch_to_icepyx(monkeypatch, fake_icepyx_backend):
    """
    Checks that get_data_from_cloude calls icepyx properly
    """
    called, fake_get_icepyx_data = fake_icepyx_backend

    monkeypatch.setattr(
        "aok.core.acquisition.request_data.get_icepyx_data", fake_get_icepyx_data
    )

    req = DataRequest(spatial=[0, 0, 1, 1])
    result = get_data_from_cloud(
        req,
        provider="icepyx",
        download_dir="/tmp/data",
        overwrite=True,
    )

    assert called["backend"] == "icepyx"
    assert called["request"] == req
    assert called["kwargs"] == {
        "download_dir": "/tmp/data",
        "overwrite": True,
    }
    assert result == "icepyx_result"


def test_get_data_from_cloud_dispatch_to_sliderule(monkeypatch, fake_sliderule_backend):
    """
    Checks that get_data_from_cloud calls sliderule properly
    """
    called, fake_get_sliderule_data = fake_sliderule_backend

    monkeypatch.setattr(
        "aok.core.acquisition.request_data.get_sliderule_data", fake_get_sliderule_data
    )

    req = DataRequest(spatial=[0, 0, 1, 1])
    result = get_data_from_cloud(
        request=req,
        provider="sliderule",
        download_dir="/tmp/data",
        overwrite=True,
    )

    assert called["backend"] == "sliderule"
    assert called["request"] == req
    assert called["kwargs"] == {
        "download_dir": "/tmp/data",
        "overwrite": True,
    }
    assert result == "sliderule_result"


# test_get_data_from_cloud_requests_from_yml
def test_get_data_from_cloud_requests_from_yml_path(
    monkeypatch, tmp_path, fake_icepyx_backend
):
    """
    Checks that when a yaml file path is provided, the request_builder is called
    is called.
    """
    called, fake_get_icepyx_data = fake_icepyx_backend

    fake_request = DataRequest(spatial=[0, 0, 1, 1])
    yaml_file = tmp_path / "request.yml"
    yaml_file.write_text("spatial: [0, 0, 1, 1]\n")

    def fake_build_data_request(cli_args=None, yaml_path=None):
        called["cli_args"] = cli_args
        called["yaml_path"] = yaml_path
        return fake_request

    monkeypatch.setattr(
        "aok.core.acquisition.request_data.build_data_request",
        fake_build_data_request,
    )
    monkeypatch.setattr(
        "aok.core.acquisition.request_data.get_icepyx_data",
        fake_get_icepyx_data,
    )

    result = get_data_from_cloud(
        request=None,
        provider="icepyx",
        yaml_path=yaml_file,
        download_dir="/tmp/data",
    )

    assert called["cli_args"] is None
    assert called["yaml_path"] == yaml_file
    assert called["request"] is fake_request
    assert called["kwargs"] == {"download_dir": "/tmp/data"}
    assert result == "icepyx_result"


# test_get_data_from_cloud_requests_from_cli
def test_get_data_from_cloud_requests_from_cli_args(
    monkeypatch, tmp_path, fake_icepyx_backend
):
    """
    Checks that when cli_args are provided, the request_builder is
    is called.
    """
    called, fake_get_icepyx_data = fake_icepyx_backend

    cli_args = Namespace(
        spatial=[0, 0, 1, 1],
        target_beams="gt1l,gt1r",
    )

    fake_request = DataRequest(
        spatial=[0, 0, 1, 1],
        beams=["gt1l", "gt1r"],
    )

    def fake_build_data_request(cli_args=None, yaml_path=None):
        called["cli_args"] = cli_args
        called["yaml_path"] = yaml_path
        return fake_request

    monkeypatch.setattr(
        "aok.core.acquisition.request_data.build_data_request",
        fake_build_data_request,
    )
    monkeypatch.setattr(
        "aok.core.acquisition.request_data.get_icepyx_data",
        fake_get_icepyx_data,
    )

    result = get_data_from_cloud(
        request=None,
        provider="icepyx",
        cli_args=cli_args,
        download_dir="/tmp/data",
    )

    assert called["cli_args"] is cli_args
    assert called["yaml_path"] is None
    assert called["request"] is fake_request
    assert called["kwargs"] == {"download_dir": "/tmp/data"}
    assert result == "icepyx_result"


def test_request_data_raises_when_no_request_or_builder_input_is_provided():
    with pytest.raises(
        ValueError, match="A DataRequest, cli_args, or yaml_path must be provided."
    ):
        get_data_from_cloud(request=None, provider="icepyx")


def test_request_data_raises_when_incorrect_provider_is_provided():
    with pytest.raises(ValueError, match="Unknown provider: website"):
        get_data_from_cloud(
            request=DataRequest(spatial=[0, 0, 1, 1]), provider="website"
        )
