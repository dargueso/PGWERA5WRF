#!/usr/bin/env python
"""Interpolate_CMIP6_Annual_cycle-CC_pinterp.py

Interpolate CMIP6 annual-cycle CC signals to ERA5 pressure levels.

Usage
-----
    python scripts/Interpolate_CMIP6_Annual_cycle-CC_pinterp.py \
        --config pgw4era.toml --profile wrf
"""

from __future__ import annotations

import argparse
import os
import time

import xarray as xr


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interpolate CMIP6 CC signal to ERA5 pressure levels.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", default="pgw4era.toml", help="Path to TOML config file.")
    parser.add_argument("--profile", default="wrf", help="Profile name in the TOML config.")
    return parser.parse_args()


def checkpoint(ctime, msg="task"):
    if ctime == 0:
        return time.time()
    dtime = time.time() - ctime
    print(f"{msg}")
    print(f"======> DONE in {dtime:0.2f} seconds\n")
    return time.time()


def main() -> None:
    args = parse_args()

    from pgw4era.config import load_config

    cfg = load_config(args.config, args.profile)

    ERA5_pl_ref_file = cfg.ERA5_pl_ref_file
    CMIP6anom_dir = cfg.CMIP6anom_dir
    variables = cfg.variables_3d
    experiments = cfg.experiments
    year_ranges = cfg.periods
    syearp, eyearp = year_ranges[0]
    syearf, eyearf = year_ranges[1]

    era5_ref = xr.open_dataset(ERA5_pl_ref_file)
    era5_plev = era5_ref.plev.values

    interp_dir = f"{CMIP6anom_dir}/interp_plevs"
    os.makedirs(interp_dir, exist_ok=True)

    ctime_i = checkpoint(0)
    for varname in variables:
        ctime_00 = checkpoint(0)

        out_file = (
            f"{interp_dir}/{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}"
            f"_{'-'.join(experiments)}_CC_signal_pinterp.nc"
        )
        if not os.path.exists(out_file):
            fin = xr.open_dataset(
                f"{CMIP6anom_dir}/{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}"
                f"_{'-'.join(experiments)}_CC_signal.nc"
            )
            fin.reindex(plev=fin.plev[::-1])
            fin_pinterp = fin.interp(plev=era5_plev, kwargs={"fill_value": "extrapolate"})
            fin_pinterp.to_netcdf(out_file, unlimited_dims="time")

        checkpoint(ctime_00, f"{varname} file interpolated")

    checkpoint(ctime_i, "Done CC vertical interpolation to ERA5 plevs")


if __name__ == "__main__":
    main()
