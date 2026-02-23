#!/usr/bin/env python
"""grib2netcdf.py — Convert ERA5 GRIB files to netCDF using grib_to_netcdf.

Edit ``filepatt`` and the output directory to match your data layout.

Usage
-----
    python scripts/grib2netcdf.py
"""

from __future__ import annotations

import os
import subprocess
from glob import glob


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


def main() -> None:
    filepatt = "ERA5_grb/3hr/era5_daily_*_2009060?.grb"
    files = sorted(glob(filepatt))
    print(f"{bcolors.HEADER}Converting {filepatt} to netCDF{bcolors.ENDC}")

    for fin in files:
        fout = os.path.basename(fin).split("grb")[0] + "nc"
        if not os.path.exists(f"ERA5_netcdf/{fout}"):
            try:
                subprocess.check_output(
                    f"grib_to_netcdf -o ERA5_netcdf/{fout} {fin}",
                    shell=True,
                )
                print(f"{bcolors.OKGREEN}Converted {fin} to netCDF{bcolors.ENDC}")
            except Exception:
                raise SystemExit(
                    f"{bcolors.ERROR}ERROR: Could not convert {fin} to netCDF{bcolors.ENDC}"
                )
        else:
            print(f"{bcolors.OKCYAN}{fin} already converted to netCDF{bcolors.ENDC}")


if __name__ == "__main__":
    main()
