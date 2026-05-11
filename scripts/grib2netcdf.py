#!/usr/bin/env python
"""grib2netcdf.py — Convert ERA5 GRIB files to netCDF using grib_to_netcdf.

Usage
-----
    python scripts/grib2netcdf.py --config my_experiment.toml --profile cryowrf

Optional keys in the chosen config profile:
    grib_input_pattern  glob for input GRIB files
                        (default: "ERA5_grb/3hr/era5_daily_*_2009060?.grb")
    grib_output_dir     output directory for NetCDF files  (default: "ERA5_netcdf")
"""

from __future__ import annotations

import argparse
import os
import subprocess
from glob import glob
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Python < 3.11 requires 'tomli' to be installed: pip install tomli"
        ) from exc


_DEFAULT_INPUT_PATTERN = "ERA5_grb/3hr/era5_daily_*_2009060?.grb"
_DEFAULT_OUTPUT_DIR = "ERA5_netcdf"


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert ERA5 GRIB files to NetCDF.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to the pgw4era TOML configuration file.",
    )
    parser.add_argument(
        "--profile",
        default="wrf",
        help="Configuration profile to read (e.g. 'wrf' or 'cryowrf').",
    )
    return parser.parse_args()


def _load_grib_config(config_path: str | None, profile: str) -> tuple[str, str]:
    """Return (input_pattern, output_dir) from config or hardcoded defaults."""
    if config_path is None:
        return _DEFAULT_INPUT_PATTERN, _DEFAULT_OUTPUT_DIR

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("rb") as fh:
        data = tomllib.load(fh)

    cfg = data.get(profile, {})
    input_pattern = cfg.get("grib_input_pattern", _DEFAULT_INPUT_PATTERN)
    output_dir = cfg.get("grib_output_dir", _DEFAULT_OUTPUT_DIR)
    return input_pattern, output_dir


def main() -> None:
    args = parse_args()
    filepatt, output_dir = _load_grib_config(args.config, args.profile)

    files = sorted(glob(filepatt))
    print(f"{bcolors.HEADER}Converting {filepatt} to netCDF{bcolors.ENDC}")

    os.makedirs(output_dir, exist_ok=True)

    for fin in files:
        fout = os.path.splitext(os.path.basename(fin))[0] + ".nc"
        out_path = os.path.join(output_dir, fout)
        if not os.path.exists(out_path):
            try:
                subprocess.check_output(
                    f"grib_to_netcdf -o {out_path} {fin}",
                    shell=True,
                    stderr=subprocess.STDOUT,
                )
                print(f"{bcolors.OKGREEN}Converted {fin} to netCDF{bcolors.ENDC}")
            except subprocess.CalledProcessError as exc:
                raise SystemExit(
                    f"{bcolors.ERROR}ERROR: Could not convert {fin} to netCDF\n"
                    f"{exc.output.decode(errors='replace')}{bcolors.ENDC}"
                )
        else:
            print(f"{bcolors.OKCYAN}{fin} already converted to netCDF{bcolors.ENDC}")


if __name__ == "__main__":
    main()
