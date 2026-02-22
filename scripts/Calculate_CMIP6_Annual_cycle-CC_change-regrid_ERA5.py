#!/usr/bin/env python
"""Calculate_CMIP6_Annual_cycle-CC_change-regrid_ERA5.py

Calculate CMIP6 annual cycle, climate-change signal, and regrid to ERA5 grid.

Usage
-----
    python scripts/Calculate_CMIP6_Annual_cycle-CC_change-regrid_ERA5.py \
        --config pgw4era.toml --profile wrf
"""

from __future__ import annotations

import argparse
import os
import subprocess
from glob import glob
from pathlib import Path

import xarray as xr
from tqdm.auto import tqdm


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


def preprocess(ds):
    drop_vars = [var for var in ds.variables if "bnds" in ds[var].dims]
    ds = ds.drop_vars(drop_vars)
    if "bnds" in ds.dims:
        ds = ds.drop_dims("bnds")
    return ds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate CMIP6 annual cycle, CC signal, and regrid to ERA5.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", default="pgw4era.toml", help="Path to TOML config file.")
    parser.add_argument("--profile", default="wrf", help="Profile name in the TOML config.")
    return parser.parse_args()


def calculate_annual_cycle(GCM, varname, experiments, syear, eyear, idir, odir):
    filenames_p = sorted(glob(f"{idir}/{experiments[0]}/{varname}/{GCM}/{varname}*nc"))
    finallp = xr.open_mfdataset(filenames_p, preprocess=preprocess)
    if finallp.time.dtype == "O":
        finallp["time"] = finallp["time"].astype("datetime64[ns]")
    finallp_period = finallp.sel(time=slice(str(syear), str(eyear)))

    filenames_f = sorted(glob(f"{idir}/{experiments[1]}/{varname}/{GCM}/{varname}*nc"))
    finallf = xr.open_mfdataset(filenames_f, preprocess=preprocess)
    finallf = finallf.where(finallf[varname] != 0.0)
    if finallf.time.dtype == "O":
        finallf["time"] = finallf["time"].astype("datetime64[ns]")
    finallf_period = finallf.sel(time=slice(str(syear), str(eyear)))

    finall = xr.concat([finallp_period, finallf_period], dim="time")

    Path(f"{odir}/{GCM}/").mkdir(exist_ok=True, parents=True)

    ofname = f"{odir}/{GCM}/{varname}_{syear}-{eyear}_{'-'.join(experiments)}.nc"
    print(f"{bcolors.OKCYAN}Saving file: {ofname}{bcolors.ENDC}")

    if not os.path.isfile(ofname):
        import pandas as pd

        fin_p = finall.sel(time=slice(str(syear), str(eyear)))
        avail_dates = pd.to_datetime(fin_p.time.values)
        year_months = {(d.year, d.month) for d in avail_dates}
        all_months = {(y, m) for y in range(syear, eyear + 1) for m in range(1, 13)}

        if year_months != all_months:
            raise SystemExit(
                f"{bcolors.ERROR}ERROR: Not all requested years/months available: "
                f"{GCM} {varname}{bcolors.ENDC}"
            )

        if varname == "hus":
            fin_p = fin_p.where((fin_p.hus >= 0) & (fin_p.hus <= 100))
        elif varname == "hur":
            fin_p = fin_p.where((fin_p.hur >= 0) & (fin_p.hur <= 100))
        elif varname == "ta":
            fin_p = fin_p.where((fin_p.ta >= 0) & (fin_p.ta < 400))
        elif varname == "ua":
            fin_p = fin_p.where((fin_p.ua > -500) & (fin_p.ua < 500))
        elif varname == "va":
            fin_p = fin_p.where((fin_p.va > -500) & (fin_p.va < 500))
        elif varname == "zg":
            fin_p = fin_p.where((fin_p.zg > -1000) & (fin_p.zg < 60000))

        fin_p_mm = fin_p.groupby("time.month").mean("time", skipna=False)
        fin_p_mm.to_netcdf(ofname)
        print(
            f"{bcolors.OKGREEN}Created annual cycle: {GCM} {varname} {syear}-{eyear}{bcolors.ENDC}"
        )
    else:
        print(f"{bcolors.OKCYAN}{varname} {GCM} {syear}-{eyear} Already processed{bcolors.ENDC}")

    finall.close()


def calculate_CC_signal(GCM, varname, experiments, year_ranges, idir, odir):
    syearp, eyearp = year_ranges[0]
    syearf, eyearf = year_ranges[1]

    ofname = (
        f"{odir}/{GCM}/{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}"
        f"_{'-'.join(experiments)}_delta.nc"
    )
    Path(f"{odir}/{GCM}/").mkdir(exist_ok=True, parents=True)

    if not os.path.isfile(ofname):
        import pandas as pd

        fin_p = xr.open_dataset(
            f"{idir}/{GCM}/{varname}_{syearp}-{eyearp}_{'-'.join(experiments)}.nc"
        )
        fin_f = xr.open_dataset(
            f"{idir}/{GCM}/{varname}_{syearf}-{eyearf}_{'-'.join(experiments)}.nc"
        )
        fin_d = fin_f - fin_p

        datelist = pd.date_range(f"{syearp}-01-01", periods=12, freq="MS")
        foutclean = fin_d.rename({"month": "time"})
        foutclean = foutclean.assign_coords({"time": datelist})
        foutclean.to_netcdf(ofname, unlimited_dims="time")

        fin_p.close()
        fin_f.close()
        print(f"{bcolors.OKGREEN}Created delta file: {GCM} {varname}{bcolors.ENDC}")
    else:
        print(f"{bcolors.OKCYAN}CC file {varname} {GCM} Already processed{bcolors.ENDC}")


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
    idir = cfg.CMIP6_monthly_dir
    odir = cfg.CMIP6anom_dir

    acycle_odir = f"{odir}/annual_cycle"
    deltas_odir = f"{odir}/deltas"
    regrid_era5 = f"{odir}/regrid_ERA5"

    print(f"{bcolors.HEADER}Creating Annual cycles and delta files{bcolors.ENDC}")
    Path(acycle_odir).mkdir(exist_ok=True, parents=True)
    Path(deltas_odir).mkdir(exist_ok=True, parents=True)
    Path(regrid_era5).mkdir(exist_ok=True, parents=True)

    print(f"{bcolors.OKGREEN}Processing periods: {year_ranges}{bcolors.ENDC}")

    for GCM in tqdm(models):
        for varname in variables:
            for period in year_ranges:
                syear, eyear = period
                print(f"{bcolors.OKCYAN}Processing period: {syear} - {eyear}{bcolors.ENDC}")
                calculate_annual_cycle(GCM, varname, experiments, syear, eyear, idir, acycle_odir)

            calculate_CC_signal(GCM, varname, experiments, year_ranges, acycle_odir, deltas_odir)

            syearp, eyearp = year_ranges[0]
            syearf, eyearf = year_ranges[1]
            delta_file = (
                f"{deltas_odir}/{GCM}/{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}"
                f"_{'-'.join(experiments)}_delta.nc"
            )
            regrid_file = (
                f"{regrid_era5}/{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}"
                f"_{'-'.join(experiments)}_{GCM}_delta.nc"
            )
            if not os.path.isfile(regrid_file):
                try:
                    subprocess.check_output(
                        f"cdo -remapbil,era5_grid {delta_file} {regrid_file}",
                        shell=True,
                    )
                    print(
                        f"{bcolors.OKGREEN}Regridded delta to ERA5: {GCM} {varname}{bcolors.ENDC}"
                    )
                except Exception:
                    raise SystemExit(
                        f"{bcolors.ERROR}ERROR: Could not regrid to ERA5: {GCM} {varname}"
                        f"{bcolors.ENDC}"
                    )


if __name__ == "__main__":
    main()
