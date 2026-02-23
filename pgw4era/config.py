"""pgw4era.config — TOML configuration loader with profile selection."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Python < 3.11 requires 'tomli' to be installed: pip install tomli"
        ) from exc

# Keys that must be present in every profile
_REQUIRED_KEYS = [
    "ERA5netcdf_dir",
    "ERA5_sfc_ref_file",
    "ERA5_pl_ref_file",
    "CMIP6_monthly_dir",
    "CMIP6anom_dir",
    "syear",
    "eyear",
    "smonth",
    "emonth",
    "experiments",
    "periods",
    "variables_2d",
    "variables_3d",
]

# Derived convenience keys added automatically
_DERIVED_KEYS = ["variables_all", "syearp", "eyearp", "syearf", "eyearf"]


def load_config(path: str | Path, profile: str) -> SimpleNamespace:
    """Load *profile* from a pgw4era TOML file and return a SimpleNamespace.

    Parameters
    ----------
    path:
        Path to the TOML configuration file.
    profile:
        Profile name to load (e.g. ``"wrf"`` or ``"cryowrf"``).

    Returns
    -------
    SimpleNamespace
        All keys from the profile are accessible as attributes.  Additional
        derived attributes are added for convenience (``variables_all``,
        ``syearp``, ``eyearp``, ``syearf``, ``eyearf``).

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    KeyError
        If *profile* is not defined in the TOML file.
    ValueError
        If any required key is missing from the profile.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("rb") as fh:
        data = tomllib.load(fh)

    if profile not in data:
        available = ", ".join(data.keys())
        raise KeyError(f"Profile '{profile}' not found in {path}. Available: {available}")

    cfg = dict(data[profile])

    # Validate required keys
    missing = [k for k in _REQUIRED_KEYS if k not in cfg]
    if missing:
        raise ValueError(f"Profile '{profile}' is missing required key(s): {', '.join(missing)}")

    # Derived helpers
    cfg.setdefault("models", None)
    cfg.setdefault("figs_path", None)
    cfg["variables_all"] = cfg["variables_2d"] + cfg["variables_3d"]
    periods = cfg["periods"]
    cfg["syearp"] = periods[0][0]
    cfg["eyearp"] = periods[0][1]
    cfg["syearf"] = periods[1][0]
    cfg["eyearf"] = periods[1][1]

    return SimpleNamespace(**cfg)
