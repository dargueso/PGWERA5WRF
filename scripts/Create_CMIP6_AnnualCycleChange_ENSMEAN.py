#!/usr/bin/env python
"""Create_CMIP6_AnnualCycleChange_ENSMEAN.py

Compute the ensemble mean of CMIP6 annual-cycle climate-change signals.

Usage
-----
    python scripts/Create_CMIP6_AnnualCycleChange_ENSMEAN.py \
        --config pgw4era.toml --profile wrf
"""

from __future__ import annotations

import argparse
from glob import glob
from pathlib import Path

import numpy as np
import xarray as xr


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


def mean_with_missing_threshold(data_array, dim, threshold=0.2):
    valid_counts = data_array.count(dim=dim)
    total_counts = data_array.sizes[dim]
    missing_fraction = 1 - (valid_counts / total_counts)
    mask = missing_fraction > threshold
    mean_values = data_array.mean(dim=dim, skipna=True)
    return mean_values.where(~mask, np.nan)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create CMIP6 annual-cycle change ensemble mean.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", default="pgw4era.toml", help="Path to TOML config file.")
    parser.add_argument("--profile", default="wrf", help="Profile name in the TOML config.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    from pgw4era.config import load_config

    cfg = load_config(args.config, args.profile)

    models_str = cfg.models
    if models_str is None:
        with open("list_CMIP6.txt") as f:
            models = f.read().splitlines()
    else:
        models = cfg.models

    variables = cfg.variables_all
    experiments = cfg.experiments
    year_ranges = cfg.periods
    syearp, eyearp = year_ranges[0]
    syearf, eyearf = year_ranges[1]

    idir = f"{cfg.CMIP6anom_dir}/regrid_ERA5"
    odir = f"{cfg.CMIP6anom_dir}/regrid_ERA5"
    cpdir = f"{cfg.CMIP6anom_dir}/corrected_plevs"

    plvs = np.asarray(
        [
            100000,
            92500,
            85000,
            70000,
            60000,
            50000,
            40000,
            30000,
            25000,
            20000,
            15000,
            10000,
            7000,
            5000,
            3000,
            2000,
            1000,
            500,
            100,
        ]
    )
    correct_plevs = True

    Path(odir).mkdir(exist_ok=True, parents=True)

    for GCM in models:
        if correct_plevs:
            Path(cpdir).mkdir(exist_ok=True, parents=True)
            for varname in variables:
                filepath = (
                    f"{idir}/{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}"
                    f"_{'-'.join(experiments)}_{GCM}_delta.nc"
                )
                filename = filepath.split("/")[-1]
                print(filename)
                fin = xr.open_dataset(filepath)
                if varname in ["ta", "hur", "ua", "va", "zg"]:
                    fin.coords["plev"] = plvs
                    fin.to_netcdf(f"{cpdir}/{filename}")
                else:
                    if "height" in fin.coords:
                        fin = fin.drop_vars("height")
                    fin = fin[varname]
                    fin.to_netcdf(f"{cpdir}/{filename}")

    for varname in variables:
        print(varname)
        filesin = []
        for GCM in models:
            filesin.extend(
                sorted(
                    glob(
                        f"{cpdir}/{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}"
                        f"_{'-'.join(experiments)}_{GCM}_delta.nc"
                    )
                )
            )

        fin = xr.open_mfdataset(filesin, concat_dim="model", combine="nested")

        if "areacella" in fin.variables:
            fin = fin.drop_vars("areacella")

        fin.to_netcdf(
            f"{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}"
            f"_{'-'.join(experiments)}_CC_signal_allmodels.nc"
        )

        fin_ensmean = mean_with_missing_threshold(fin, dim="model", threshold=1).squeeze()
        fin_ensmean.to_netcdf(
            f"{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}_{'-'.join(experiments)}_CC_signal.nc"
        )


if __name__ == "__main__":
    raise SystemExit(main())
