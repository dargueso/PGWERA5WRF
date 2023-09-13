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
import os, argparse
from pathlib import Path
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


#####################################################################
#####################################################################

def parse_args():

    parser = argparse.ArgumentParser(
        description="PURPOSE: Create files with annual cycle of changes PGW"
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
    parser.add_argument('-v', '--var_names', type=str,
            help='Variable names (e.g. ta) to process. Separate ' +
            'multiple variable names with "," (e.g. tas,ta). Default is ' +
            'to process all required variables ta,hus,ua,va,zg,hurs,tas,ps,ts',
            default='ta,hus,ua,va,zg,hurs,tas,ps,ts,uas')

    # input directory
    parser.add_argument('-i', '--input_dir', type=str,
                help='Directory with input GCM delta files on ERA5 grid',
                default =  "/vg5/dargueso/BDY_DATA/CMIP6/")
    
    # output directory
    parser.add_argument('-o', '--output_dir', type=str,
                help='Directory where the GCM ENSEMBLE delta files ' +
                ' should be stored.',
                default = "/vg5/dargueso/BDY_DATA/CMIP6/")

    args = parser.parse_args()
    return args


#####################################################################
#####################################################################

args = parse_args()
models_str = args.models

if models_str is None:
    with open("list_CMIP6.txt") as f:
        models = f.read().splitlines()
else:
    models = args.models.split(",")

variables = args.var_names.split(',')
idir = args.input_dir
odir = args.output_dir
experiments = ["historical", "ssp585"]
syear_exp = {"historical": 1985, "ssp585": 2070}
eyear_exp = {"historical": 2014, "ssp585": 2099}

acycle_odir = f"{odir}/annual_cycle"
deltas_odir = f"{odir}/deltas"
regrid_era5 = f"{odir}/regrid_ERA5"

plvs=np.asarray([100000, 92500, 85000, 70000, 60000, 50000, 40000, 30000, 25000,
    20000, 15000, 10000, 7000, 5000, 3000, 2000, 1000, 500, 100 ])

def main():

    print(f"{bcolors.HEADER}Creating Annual cycles and delta files{bcolors.ENDC}")
    Path(acycle_odir).mkdir(exist_ok=True, parents=True)
    Path(deltas_odir).mkdir(exist_ok=True, parents=True)
    Path(regrid_era5).mkdir(exist_ok=True, parents=True)
  
    

    for GCM in (tqdm(models)):
        #pbar.set_description(f"{GCM}")

        for vn, varname in enumerate(variables):

            for exp in experiments:

                syear = syear_exp[exp]
                eyear = eyear_exp[exp]

                calculate_annual_cycle(GCM,varname,exp,syear,eyear,idir,acycle_odir)
        
        
            calculate_CC_signal(GCM,varname,acycle_odir,deltas_odir)

            #REGRID TO ERA5
            delta_file = f"{deltas_odir}/{GCM}/{varname}_delta.nc"
            regrid_file = f"{regrid_era5}/{varname}_{GCM}_delta.nc"
            if not os.path.isfile(regrid_file):
                try:
                    subprocess.check_output(
                        f"cdo -remapbil,era5_grid {delta_file} {regrid_file}",
                        shell=True,
                    )
                    print(f"{bcolors.OKGREEN}Regridded delta to ERA5: {GCM} {varname}{bcolors.ENDC}")
                except Exception:
                    raise SystemExit(
                        f"{bcolors.ERROR}ERROR: Could not regrid to ERA5 grid: {GCM} {varname} {bcolors.ENDC}"
                    )






###########################################################
###########################################################
def calculate_annual_cycle(GCM, varname,exp,syear,eyear,idir,odir):
    """For a given model, member and variable,
    Calculate annual cycle"""



    filenames_all = sorted(glob(f"{idir}/{exp}/{varname}/{GCM}/{varname}*nc"))
    finall = xr.open_mfdataset(filenames_all, concat_dim="time", combine="nested")

    if finall.time.dtype=='O':
        finall['time']=finall['time'].astype("datetime64[ns]")

    Path(f"{odir}/{GCM}/").mkdir(exist_ok=True, parents=True)

    ofname = f"{odir}/{GCM}/{varname}_{exp}.nc"

    if not os.path.isfile(ofname):
        fin_p = finall.sel(time=slice(str(syear), str(eyear)))

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
        print(f"{bcolors.OKGREEN}Created annual cycle file for {GCM} {varname} {exp}{bcolors.ENDC}")
    else:
        print(f"{bcolors.OKCYAN}{exp} {varname} {GCM} Already processed{bcolors.ENDC}")

    finall.close()


###########################################################
###########################################################
def calculate_CC_signal(GCM, varname,idir,odir):
    """From present and future annual cycle
    calculate CC signal for every month"""

    ofname = f"{odir}/{GCM}/{varname}_delta.nc"
    Path(f"{odir}/{GCM}/").mkdir(exist_ok=True, parents=True)

    if not os.path.isfile(ofname):

        fin_p = xr.open_dataset(f"{idir}/{GCM}/{varname}_historical.nc")
        fin_f = xr.open_dataset(f"{idir}/{GCM}/{varname}_ssp585.nc")
        #import pdb; pdb.set_trace()  # fmt: skip
        fin_d = fin_f - fin_p

        if "plev_bnds" in fin_d.keys():
            fin_d = fin_d.drop(("plev_bnds"))
        if "lon_bnds" in fin_d.keys():
            fin_d = fin_d.drop(("lon_bnds"))
        if "lat_bnds" in fin_d.keys():
            fin_d = fin_d.drop(("lat_bnds"))

        datelist = pd.date_range(f"1990-01-01", periods=12, freq="MS")

        foutclean = fin_d.rename({"month": "time"})
        foutclean = foutclean.assign_coords({"time": datelist})
        foutclean.to_netcdf(ofname,
            unlimited_dims="time",
        )


        fin_p.close()
        fin_f.close()
        print(f"{bcolors.OKGREEN}Created delta file for {GCM} {varname}{bcolors.ENDC}")
    else:
        print(f"{bcolors.OKCYAN}CC file {varname} {GCM} Already processed{bcolors.ENDC}")




###############################################################################
##### __main__  scope
###############################################################################

if __name__ == "__main__":
    main()

###############################################################################
