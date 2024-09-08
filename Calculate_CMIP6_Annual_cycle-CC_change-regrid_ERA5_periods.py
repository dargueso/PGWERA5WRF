#!/usr/bin/env python
"""
#####################################################################
# Author: Daniel Argueso <daniel>
# Date:   2021-06-07T16:53:49+02:00
# Email:  d.argueso@uib.es
# Last modified by:   daniel
# Last modified time: 2023-04-03
# @Project@ EPICC
# Version: 1.0 (Beta)
# Description:
#
# Dependencies: Intersection of available models created with Get_CMIP6_Monthly_PGW_NCI.py
#
# Files: Monthly files of CMIP6 models, and list of available models SearchLocations_intersection_cmip6_mon.txt
#
#####################################################################
"""

import time
import numpy as np
import netCDF4 as nc
import subprocess as subprocess
from glob import glob
import pandas as pd
import xarray as xr
import os
from pathlib import Path
from tqdm.auto import tqdm
import pgw4era_config as cfg


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


#####################################################################
#####################################################################

# Define a function to drop the 'bnds' dimension and associated variables
def preprocess(ds):
    # Drop variables associated with 'bnds' dimension
    drop_vars = [var for var in ds.variables if 'bnds' in ds[var].dims]
    ds = ds.drop_vars(drop_vars)
    
    # Drop the 'bnds' dimension itself if it exists
    if 'bnds' in ds.dims:
        ds = ds.drop_dims('bnds')
    
    return ds

#####################################################################
#####################################################################

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

syear_exp = {"historical": 1985, "ssp585": 2015}
eyear_exp = {"historical": 2014, "ssp585": 2099}
acycle_odir = f"{odir}/annual_cycle"
deltas_odir = f"{odir}/deltas"
regrid_era5 = f"{odir}/regrid_ERA5"


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


def main():
    print(f"{bcolors.HEADER}Creating Annual cycles and delta files{bcolors.ENDC}")
    Path(acycle_odir).mkdir(exist_ok=True, parents=True)
    Path(deltas_odir).mkdir(exist_ok=True, parents=True)
    Path(regrid_era5).mkdir(exist_ok=True, parents=True)
    
    print (f"{bcolors.OKGREEN}Processing periods: {year_ranges}{bcolors.ENDC}")

    for GCM in tqdm(models):
        # pbar.set_description(f"{GCM}")

        for vn, varname in enumerate(variables):
            
            for period in year_ranges:
                syear = period[0]
                eyear = period[1]
                print(f"{bcolors.OKCYAN}Processing period: {syear} - {eyear}{bcolors.ENDC}")

                calculate_annual_cycle(
                    GCM, varname, experiments, syear, eyear, idir, acycle_odir
                )

            calculate_CC_signal(GCM, varname, experiments, year_ranges, acycle_odir, deltas_odir)

            # REGRID TO ERA5
            syearp = year_ranges[0][0]
            eyearp = year_ranges[0][1]
            syearf = year_ranges[1][0]
            eyearf = year_ranges[1][1]
            delta_file = f"{deltas_odir}/{GCM}/{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}_{'-'.join(experiments)}_delta.nc"
            regrid_file = f"{regrid_era5}/{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}_{'-'.join(experiments)}_{GCM}_delta.nc"
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
                        f"{bcolors.ERROR}ERROR: Could not regrid to ERA5 grid: {GCM} {varname} {bcolors.ENDC}"
                    )


###########################################################
###########################################################
def calculate_annual_cycle(GCM, varname, experiments, syear, eyear, idir, odir):
    """For a given model, member and variable,
    Calculate annual cycle"""
    
    filenames_p = sorted(glob(f"{idir}/{experiments[0]}/{varname}/{GCM}/{varname}*nc"))
    finall_p = xr.open_mfdataset(filenames_p, preprocess=preprocess)
    
    filenames_f = sorted(glob(f"{idir}/{experiments[1]}/{varname}/{GCM}/{varname}*nc"))
    finall_f = xr.open_mfdataset(filenames_f, preprocess=preprocess)
    
    if finall_p.time.dtype == "O":
        finall_p["time"] = finall_p["time"].astype("datetime64[ns]")
    if finall_f.time.dtype == "O":
        finall_f["time"] = finall_f["time"].astype("datetime64[ns]")
    
    #Concatenate the two datasets along the time dimension
    finall = xr.concat([finall_p, finall_f], dim="time")
    
    Path(f"{odir}/{GCM}/").mkdir(exist_ok=True, parents=True)

    ofname = f"{odir}/{GCM}/{varname}_{syear}-{eyear}_{'-'.join(experiments)}.nc"
    print (f"{bcolors.OKCYAN}Saving file: {ofname}{bcolors.ENDC}")

    if not os.path.isfile(ofname):
        fin_p = finall.sel(time=slice(str(syear), str(eyear)))
        
        # Convert the time variable to a pandas datetime series
        avail_dates = pd.to_datetime(fin_p.time.values)

        # Extract year and month as tuples (year, month)
        year_months = set((date.year, date.month) for date in avail_dates)
        
        # Generate a set of all year-month combinations for the period
        all_months = set((year, month) for year in range(syear,eyear+1) for month in range(1, 13))

        # Check if the two sets are equal
        all_months_present = year_months == all_months

        if not all_months_present:
            raise SystemExit(
                f"{bcolors.ERROR}ERROR: Not all requested years/months seem to be available: {GCM} {varname} {bcolors.ENDC}"
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

        fin_p_mm = fin_p.groupby("time.month").mean("time")
        fin_p_mm.to_netcdf(ofname)
        print(
            f"{bcolors.OKGREEN}Created annual cycle file for {GCM} {varname} {syear}-{eyear}{bcolors.ENDC}"
        )
    else:
        print(f"{bcolors.OKCYAN}{varname} {GCM} {syear}-{eyear} Already processed{bcolors.ENDC}")

    finall.close()
    

###########################################################
###########################################################
def calculate_CC_signal(GCM, varname, experiments, year_ranges, idir, odir):
    """From present and future annual cycle
    calculate CC signal for every month"""

    syearp = year_ranges[0][0]
    eyearp = year_ranges[0][1]
    syearf = year_ranges[1][0]
    eyearf = year_ranges[1][1]
    


    ofname = f"{odir}/{GCM}/{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}_{'-'.join(experiments)}_delta.nc"
    Path(f"{odir}/{GCM}/").mkdir(exist_ok=True, parents=True)

    if not os.path.isfile(ofname):
        fin_p = xr.open_dataset(f"{idir}/{GCM}/{varname}_{syearp}-{eyearp}_{'-'.join(experiments)}.nc")
        fin_f = xr.open_dataset(f"{idir}/{GCM}/{varname}_{syearf}-{eyearf}_{'-'.join(experiments)}.nc")
        # import pdb; pdb.set_trace()  # fmt: skip
        fin_d = fin_f - fin_p

        datelist = pd.date_range(f"{syearp}-01-01", periods=12, freq="MS")

        foutclean = fin_d.rename({"month": "time"})
        foutclean = foutclean.assign_coords({"time": datelist})
        foutclean.to_netcdf(
            ofname,
            unlimited_dims="time",
        )

        fin_p.close()
        fin_f.close()
        print(f"{bcolors.OKGREEN}Created delta file for {GCM} {varname}{bcolors.ENDC}")
    else:
        print(
            f"{bcolors.OKCYAN}CC file {varname} {GCM} Already processed{bcolors.ENDC}"
        )

def parse_year_periods(periods_string):
    periods = periods_string.split(",")  # Split by comma to get each period
    year_ranges = []

    for period in periods:
        start_year, end_year = period.split("-")  # Split each period by the hyphen
        start_year = int(start_year.strip())  # Convert start year to integer
        end_year = int(end_year.strip())  # Convert end year to integer
        year_ranges.append((start_year, end_year))  # Append as a tuple

    return year_ranges

###############################################################################
##### __main__  scope
###############################################################################

if __name__ == "__main__":
    main()

###############################################################################
