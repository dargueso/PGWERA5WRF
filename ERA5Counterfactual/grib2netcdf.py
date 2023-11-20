
#!/usr/bin/env python

""" grib2netcdf.py

Author: Daniel Argueso @ CCRC, UNSW. Sydney (Australia)
email: d.argueso@ unsw.edu.au
Created: Wed Jun 17 15:22:24 AEST 2015

"""

import netCDF4 as nc
import numpy as np
from constants import const
import glob as glob
import os
import subprocess

import pdb

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

filepatt = "era5_daily_sfc_201712*.grb"
files=sorted(glob.glob(filepatt))
print(f"{bcolors.HEADER}Converting {filepatt} to netCDF{bcolors.ENDC}")
for fin in files:
	fout=fin.split("grb")[0]+"nc"
	if not os.path.exists(f"ERA5_netcdf/{fout}"):
		try:
			subprocess.check_output(
    		f"cdo -f nc copy {fin} ERA5_netcdf/{fout}",
    		shell=True)
			print(f"{bcolors.OKGREEN}Converted {fin} to netCDF{bcolors.ENDC}")
		except Exception:
			raise SystemExit(
    		f"{bcolors.ERROR}ERROR: Could not grib2 {fin} to netCDF{bcolors.ENDC}"
			)
	else:
		print(f"{bcolors.OKCYAN}{fin} Already processed converted to netCDF{bcolors.ENDC}")
    #os.system("cdo -f nc copy %s ERA5_netcdf/%s" %(fin,fout))

  
