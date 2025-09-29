#!/usr/bin/env python
"""
#####################################################################
# Author: Daniel Argueso <daniel>
# Date:   2021-08-25T18:41:42+02:00
# Email:  d.argueso@uib.es
# Last modified by:   daniel
# Last modified time: 2021-08-25T18:41:44+02:00
#
# @Project@
# Version: x.0 (Beta)
# Description:
#
# Dependencies:
#
# Files:
#
#####################################################################
"""
import xarray as xr
import numpy as np
from glob import glob
import subprocess as subprocess
from pathlib import Path
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

def mean_with_missing_threshold(data_array, dim, threshold=0.2):
    # Step 1: Count the number of valid (non-NaN) points along the dimension
    valid_counts = data_array.count(dim=dim)
    
    # Step 2: Calculate the total number of points along the dimension
    total_counts = data_array.sizes[dim]
    
    # Step 3: Identify where more than 20% of the points are missing
    missing_fraction = 1 - (valid_counts / total_counts)
    mask = missing_fraction > threshold
    
    # Step 4: Calculate the mean, ignoring NaNs
    mean_values = data_array.mean(dim=dim, skipna=True)
    
    # Step 5: Apply the mask to set the mean to NaN where the threshold is exceeded
    mean_values = mean_values.where(~mask, np.nan)
    
    return mean_values


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
syearp = year_ranges[0][0]
eyearp = year_ranges[0][1]
syearf = year_ranges[1][0]
eyearf = year_ranges[1][1]

idir = f"{cfg.CMIP6anom_dir }/regrid_ERA5"
odir = f"{cfg.CMIP6anom_dir }/regrid_ERA5"
cpdir = f"{cfg.CMIP6anom_dir }/corrected_plevs"
syear_exp = {"historical": 1985, "ssp585": 2015}
eyear_exp = {"historical": 2014, "ssp585": 2099}


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


#####################################################################
#####################################################################


def main():
    Path(odir).mkdir(exist_ok=True, parents=True)

    for GCM in models:
        if correct_plevs:
            Path(f"{cpdir}").mkdir(exist_ok=True, parents=True)
            for vn, varname in enumerate(variables):
                filepath = f"{idir}/{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}_{'-'.join(experiments)}_{GCM}_delta.nc"
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
                    # import pdb; pdb.set_trace()  # fmt: skip
                    fin.to_netcdf(f"{cpdir}/{filename}")

    for varname in variables:
        print(varname)
        # import pdb; pdb.set_trace()  # fmt: skip
        # try:
        #     subprocess.check_output(
        #         f"cdo ensmean {args.corrected_plevs_dir}/{varname}_* {varname}_CC_signal_ssp585_2099-2070_1985-2014.nc",
        #         shell=True,
        #     )
        #     print(f"{bcolors.OKGREEN}Ensemble mean of GCMs{bcolors.ENDC}")
        # except Exception:
        #     raise SystemExit(
        #         f"{bcolors.ERROR}ERROR: Could not make the ensemble mean{bcolors.ENDC}"
        #     )

        filesin = []
        for GCM in models:
            filesin.extend(
                sorted(
                    glob(
                        f"{cpdir}/{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}_{'-'.join(experiments)}_{GCM}_delta.nc"
                    )
                )
            )
        
        fin = xr.open_mfdataset(filesin, concat_dim="model", combine="nested")

        if "areacella" in fin.variables:
            fin = fin.drop_vars("areacella")

        fin.to_netcdf(f"{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}_{'-'.join(experiments)}_CC_signal_allmodels.nc")
        
        fin_ensmean = mean_with_missing_threshold(fin, dim="model",threshold=1).squeeze()
        fin_ensmean.to_netcdf(f"{varname}_{syearp}-{eyearp}_{syearf}-{eyearf}_{'-'.join(experiments)}_CC_signal.nc")


###############################################################################
# __main__  scope
###############################################################################

if __name__ == "__main__":
    raise SystemExit(main())

###############################################################################
