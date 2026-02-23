"""Tests for pgw4era.config."""

import textwrap
from pathlib import Path

import pytest

from pgw4era.config import load_config


@pytest.fixture()
def toml_file(tmp_path: Path) -> Path:
    """Write a minimal valid pgw4era.toml to a temp directory."""
    content = textwrap.dedent(
        """\
        [wrf]
        ERA5netcdf_dir = "/data/ERA5/"
        ERA5_sfc_ref_file = "era5_sfc_ref.nc"
        ERA5_pl_ref_file = "./era5_plev.nc"
        CMIP6_monthly_dir = "/data/CMIP6/"
        CMIP6anom_dir = "/data/CMIP6anom/"
        figs_path = "/data/figs"
        syear = 2009
        eyear = 2009
        smonth = 6
        emonth = 7
        experiments = ["historical", "ssp585"]
        periods = [[2004, 2023], [2031, 2050]]
        variables_2d = ["hurs", "tas", "ps", "ts", "vas", "uas", "psl"]
        variables_3d = ["ta", "ua", "va", "zg", "hur"]

        [cryowrf]
        ERA5netcdf_dir = "/data/ERA5/"
        ERA5_sfc_ref_file = "era5_sfc_ref.nc"
        ERA5_pl_ref_file = "./era5_plev.nc"
        CMIP6_monthly_dir = "/data/CMIP6/"
        CMIP6anom_dir = "/data/CMIP6anom/"
        figs_path = "/data/figs"
        syear = 2009
        eyear = 2009
        smonth = 6
        emonth = 7
        experiments = ["historical", "ssp585"]
        periods = [[2004, 2023], [2031, 2050]]
        variables_2d = ["hurs", "tas", "ps", "ts", "vas", "uas", "psl"]
        variables_3d = ["ta", "ua", "va", "zg", "hur"]
        one_timestep_files = false
        noahmp = false
        """
    )
    p = tmp_path / "pgw4era.toml"
    p.write_text(content)
    return p


class TestLoadWrfProfile:
    def test_required_keys_present(self, toml_file):
        cfg = load_config(toml_file, "wrf")
        assert cfg.ERA5netcdf_dir == "/data/ERA5/"
        assert cfg.ERA5_sfc_ref_file == "era5_sfc_ref.nc"
        assert cfg.CMIP6anom_dir == "/data/CMIP6anom/"
        assert cfg.syear == 2009
        assert cfg.eyear == 2009
        assert cfg.experiments == ["historical", "ssp585"]

    def test_derived_keys(self, toml_file):
        cfg = load_config(toml_file, "wrf")
        assert cfg.variables_all == cfg.variables_2d + cfg.variables_3d
        assert cfg.syearp == 2004
        assert cfg.eyearp == 2023
        assert cfg.syearf == 2031
        assert cfg.eyearf == 2050

    def test_variables_lists(self, toml_file):
        cfg = load_config(toml_file, "wrf")
        assert "hurs" in cfg.variables_2d
        assert "ta" in cfg.variables_3d
        assert len(cfg.variables_all) == len(cfg.variables_2d) + len(cfg.variables_3d)

    def test_models_defaults_to_none(self, toml_file):
        cfg = load_config(toml_file, "wrf")
        assert cfg.models is None


class TestLoadCryowrfProfile:
    def test_cryowrf_specific_keys(self, toml_file):
        cfg = load_config(toml_file, "cryowrf")
        assert hasattr(cfg, "one_timestep_files")
        assert cfg.one_timestep_files is False
        assert hasattr(cfg, "noahmp")
        assert cfg.noahmp is False

    def test_shared_keys_also_present(self, toml_file):
        cfg = load_config(toml_file, "cryowrf")
        assert cfg.syear == 2009
        assert cfg.CMIP6anom_dir == "/data/CMIP6anom/"


class TestMissingKeyRaises:
    def test_missing_required_key(self, tmp_path):
        """Omitting a required key must raise ValueError."""
        incomplete = textwrap.dedent(
            """\
            [wrf]
            ERA5netcdf_dir = "/data/ERA5/"
            ERA5_sfc_ref_file = "era5_sfc_ref.nc"
            ERA5_pl_ref_file = "./era5_plev.nc"
            CMIP6_monthly_dir = "/data/CMIP6/"
            CMIP6anom_dir = "/data/CMIP6anom/"
            syear = 2009
            eyear = 2009
            smonth = 6
            emonth = 7
            experiments = ["historical", "ssp585"]
            periods = [[2004, 2023], [2031, 2050]]
            variables_2d = ["hurs", "tas"]
            # variables_3d intentionally omitted
            """
        )
        p = tmp_path / "incomplete.toml"
        p.write_text(incomplete)
        with pytest.raises(ValueError, match="variables_3d"):
            load_config(p, "wrf")


class TestFileNotFound:
    def test_nonexistent_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "does_not_exist.toml", "wrf")


class TestUnknownProfile:
    def test_unknown_profile(self, toml_file):
        with pytest.raises(KeyError, match="unknown_profile"):
            load_config(toml_file, "unknown_profile")
