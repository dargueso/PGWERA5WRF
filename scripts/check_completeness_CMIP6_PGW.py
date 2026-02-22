#!/usr/bin/env python
"""check_completeness_CMIP6_PGW.py — Check that CMIP6 files cover the required period.

Usage
-----
    python scripts/check_completeness_CMIP6_PGW.py [-m MODEL1,MODEL2] [-v ta,hur]
"""

from __future__ import annotations

import argparse
import logging
import os
from glob import glob

import xarray as xr
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
        description="Check completeness of CMIP6 files for PGW.",
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

    logfile = "check_CMIP6_PGW.log"
    if os.path.exists(logfile):
        os.remove(logfile)

    logging.basicConfig(
        filename=logfile,
        filemode="a",
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )
    logging.info("Checking completeness of CMIP6 files for PGW")
    logger = logging.getLogger("checkCMIP6PGW")

    scenarios = {"historical": [1950, 2014], "ssp585": [2015, 2099]}

    for GCM in models:
        complete = True
        first = True
        for scen in scenarios:
            print(f"{bcolors.HEADER}Checking {GCM} {scen}{bcolors.ENDC}")
            for var in (pbar := tqdm(variables)):
                pbar.set_description(f"Processing {var}")
                path_in = f"./{scen}/{var}/{GCM}/"
                files_var = sorted(glob(f"{path_in}/{var}_*"))

                if files_var:
                    finvar = xr.open_mfdataset(files_var, use_cftime=True, combine="by_coords")
                    if finvar.time[0].dt.year > scenarios[scen][0] or (
                        finvar.time[-1].dt.year < scenarios[scen][1]
                    ):
                        complete = False
                        if first:
                            logger.info(f"{scen} {GCM} is not complete")
                            first = False
                        logger.info(f"{GCM} {scen} {var} is not complete")
                    finvar.close()
                else:
                    complete = False
                    if first:
                        logger.info(f"{scen} {GCM} is not complete")
                        first = False
                    logger.info(f"{GCM} {scen} {var} is not complete")

        if complete:
            print(f"{bcolors.OKGREEN} {GCM} is complete{bcolors.ENDC}")
            logger.info(f"{GCM} is complete")
        else:
            print(
                f"{bcolors.FAIL}{GCM} is not complete{bcolors.ENDC}"
                f"{bcolors.BOLD} Check log file {logfile}{bcolors.ENDC}"
            )


if __name__ == "__main__":
    raise SystemExit(main())
