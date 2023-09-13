#!/usr/bin/env python
"""
@File    :  check_completeness_simulation.py
@Time    :  2023/02/20 18:11:40
@Author  :  Daniel Argüeso
@Version :  1.0
@Contact :  d.argueso@uib.es
@License :  (C)Copyright 2023, Daniel Argüeso
@Project :  EPICC
@Desc    :  None
"""

import os
import argparse
from tqdm.auto import tqdm
import shutil
import logging
from tqdm.auto import tqdm
from glob import glob
import subprocess


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
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
        + "to process all required variables ta,hur,ua,va,zg,hurs,tas,ps,psl,ts,uas,vas",
        default="ta,hur,ua,va,zg,hurs,tas,ps,psl,ts,uas,vas",
    )
    args = parser.parse_args()
    return args


args = parse_args()
models_str = args.models
variables = args.var_names.split(",")


if models_str is None:
    with open("list_CMIP6.txt") as f:
        models_hist = f.read().splitlines()
    with open("list_CMIP6.txt") as f:
        models_proj = f.read().splitlines()

    models = list(set(models_hist + models_proj))
else:
    models = args.models.split(",")

input_folder = "/home/dargueso/BDY_DATA/CMIP6/all/"
dest_folder = "/home/dargueso/BDY_DATA/CMIP6/"
tableID = "Amon"

scenarios = {"historical": [1850, 2014], "ssp585": [2015, 2100]}


#####################################################################
#####################################################################


def main():
    for GCM in models:
        # GCM_short = "_".join(GCM.split("_")[:-1])
        GCM_short = GCM
        # variant = GCM.split("_")[-1]
        for scen in scenarios.keys():
            print(f"{bcolors.HEADER}Copying {GCM} {scen}{bcolors.ENDC}")
            for var in (pbar := tqdm(variables)):
                pbar.set_description(f"Copying {var}")
                idir = f"{input_folder}/"
                odir = f"{dest_folder}/{scen}/{var}/{GCM_short}/"  # /{variant}"
                if not os.path.exists(odir):
                    os.makedirs(odir)

                try:
                    subprocess.check_output(
                        f"rsync -av --progress {idir}/{var}_{tableID}_{GCM_short}_{scen}*.nc {odir}",
                        shell=True,
                    )

                except Exception:
                    print(
                        f"{bcolors.FAIL}Error copying {var} {GCM} {scen} {bcolors.ENDC}"
                    )
                    continue


###############################################################################
# __main__  scope
###############################################################################

if __name__ == "__main__":
    raise SystemExit(main())

###############################################################################
