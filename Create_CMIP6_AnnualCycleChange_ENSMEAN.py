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


import os, argparse
import xarray as xr
import numpy as np
from glob import glob
import subprocess as subprocess
from pathlib import Path


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


def parse_args():
    parser = argparse.ArgumentParser(
        description="PURPOSE: Check the completeness of the CMIP6 files for PGW"
    )

    parser.add_argument(
        "-m",
        "--models",
        dest="models",
        help="Optional input list of models",
        type=str,
        nargs="?",
        default=None,
    )

    # variable(s) to process
    parser.add_argument(
        "-v",
        "--var_names",
        type=str,
        help="Variable names (e.g. ta) to process. Separate "
        + 'multiple variable names with "," (e.g. tas,ta). Default is '
        + "to process all required variables ta,hus,ua,va,zg,hurs,tas,ps,ts.",
        default="ta,hus,ua,va,zg,hurs,tas,ps,ts",
    )

    # input directory
    parser.add_argument(
        "-i",
        "--input_dir",
        type=str,
        help="Directory with input GCM delta files on ERA5 grid",
        default="/vg5/dargueso/BDY_DATA/CMIP6/regrid_ERA5/",
    )

    # corrected_plevs directory
    parser.add_argument(
        "-cp",
        "--corrected_plevs_dir",
        type=str,
        help="Directory where the GCM delta files with corrected plevs should be stored.",
        default="/vg5/dargueso/BDY_DATA/CMIP6/regrid_ERA5/corrected_plevs/",
    )

    # output directory
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        help="Directory where the GCM ENSEMBLE delta files should be stored.",
        default="/vg5/dargueso/BDY_DATA/CMIP6/regrid_ERA5/",
    )
    args = parser.parse_args()
    return args


args = parse_args()
models_str = args.models

if models_str is None:
    with open("list_CMIP6.txt") as f:
        models = f.read().splitlines()
else:
    models = args.models.split(",")

variables = args.var_names.split(",")

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
    Path(args.output_dir).mkdir(exist_ok=True, parents=True)

    for GCM in models:
        if correct_plevs:
            Path(f"{args.corrected_plevs_dir}").mkdir(exist_ok=True, parents=True)
            for vn, varname in enumerate(variables):
                filepath = f"{args.input_dir}/{varname}_{GCM}_delta.nc"
                filename = filepath.split("/")[-1]
                print(filename)
                fin = xr.open_dataset(filepath)
                if varname in ["ta", "hus", "ua", "va", "zg"]:
                    fin.coords["plev"] = plvs
                    fin.to_netcdf(f"{args.corrected_plevs_dir}/{filename}")
                else:
                    if "height" in fin.coords:
                        fin = fin.drop("height")
                    fin = fin[varname]
                    # import pdb; pdb.set_trace()  # fmt: skip
                    fin.to_netcdf(f"{args.corrected_plevs_dir}/{filename}")

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
        filesin = sorted(glob(f"{args.corrected_plevs_dir}/{varname}_*"))

        fin = xr.open_mfdataset(filesin, concat_dim="model", combine="nested")
        fin_ensmean = fin.mean(dim="model").squeeze()
        fin_ensmean.to_netcdf(f"{varname}_CC_signal_ssp585_2070-2099_1985-2014.nc")


###############################################################################
# __main__  scope
###############################################################################

if __name__ == "__main__":
    raise SystemExit(main())

###############################################################################
