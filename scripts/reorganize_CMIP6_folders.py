#!/usr/bin/env python
"""reorganize_CMIP6_folders.py — Copy/reorganise CMIP6 files into the expected folder layout.

Usage
-----
    python scripts/reorganize_CMIP6_folders.py [-m MODEL1,MODEL2] [-v ta,hur]
"""

from __future__ import annotations

import argparse
import os
import subprocess

from tqdm.auto import tqdm


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy CMIP6 files into the expected folder layout.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-m", "--models", dest="models", nargs="?", default=None)
    parser.add_argument(
        "-v",
        "--var_names",
        type=str,
        default="ta,hur,ua,va,zg,hurs,tas,ps,psl,ts,uas,vas",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    models_str = args.models
    variables = args.var_names.split(",")

    if models_str is None:
        with open("list_CMIP6.txt") as f:
            models = f.read().splitlines()
    else:
        models = models_str.split(",")

    input_folder = "/home/dargueso/BDY_DATA/CMIP6/all/"
    dest_folder = "/home/dargueso/BDY_DATA/CMIP6/"
    tableID = "Amon"

    scenarios = {"historical": [1850, 2014], "ssp585": [2015, 2100]}

    for GCM in models:
        GCM_short = GCM
        for scen in scenarios:
            print(f"{bcolors.HEADER}Copying {GCM} {scen}{bcolors.ENDC}")
            for var in (pbar := tqdm(variables)):
                pbar.set_description(f"Copying {var}")
                idir = f"{input_folder}/"
                odir = f"{dest_folder}/{scen}/{var}/{GCM_short}/"
                os.makedirs(odir, exist_ok=True)

                try:
                    subprocess.check_output(
                        f"rsync -av --progress {idir}/{var}_{tableID}_{GCM_short}_{scen}*.nc {odir}",
                        shell=True,
                    )
                except Exception:
                    print(f"{bcolors.FAIL}Error copying {var} {GCM} {scen}{bcolors.ENDC}")


if __name__ == "__main__":
    raise SystemExit(main())
