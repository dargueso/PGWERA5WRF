#!/usr/bin/env python
"""
#####################################################################
# Author: Daniel Argueso <daniel> @ UIB
# Date:   2017-10-31T12:33:11+01:00
# Email:  d.argueso@uib.es
# Last modified by:   daniel
# Last modified time: 2017-10-31T12:33:16+01:00
#
# @Project@ REHIPRE
# Version: x.0 (Beta)
# Description: Script to run WPS and real recursively to generate
# daily boundary conditions. To be run in megacelula3 (Meteo-UIB)
#
# Dependencies:
#
# Files:
#
#####################################################################
"""

import os
import datetime as dt
from glob import glob
import subprocess as subprocess
import pdb
import numpy as np


def check_output(flogname, N, message):
    """Function that check a text file with a log and search
    for a pattern (message) in the last N lines
    """
    flog = open(flogname, "r")
    lineList = flog.readlines()[-N:]
    issuccess = False
    for line in lineList:
        if message in line:
            issuccess = True

    return issuccess


# Start month of the simulation. Will start at day 1.

start_month = 1
start_year = 2011
end_year = 2021


# How many days in advance (spin-up)?
spinup = 10

# name the input deck to use
indeck_wps = "namelist_wps_EPICC_2km_ERA5_CMIP6anom_SOILERA.deck"

this_dir = os.getcwd()
wrf_dir = "/home/dargueso/WRF_runs/EPICC_WRFV4.2.2_CMIP6PGW/WRF/run"
wps_dir = "/home/dargueso/WRF_runs/EPICC_WRFV4.2.2_CMIP6PGW/WPS"
grb_dir = "/vg6a/dargueso/BDY_DATA/ERA5/"
bdy_dir = "/vg6a/dargueso/BDY_DATA/ERA5_CMIP6anom/WRF-boundary/EPICC/EPICC_2km_ERA5/"

lendays = 10

###########################################################
############# END OF USER MODIF ###########################
###########################################################
###########################################################

year = start_year
month = start_month

init_date = dt.datetime(start_year, start_month, 1) - dt.timedelta(days=spinup)

year = init_date.year
month = init_date.month
day = init_date.day

sdaystr = str(day).rjust(2, "0")
smonstr = str(month).rjust(2, "0")


while year < end_year:
    # get the month as a 2 digit string

    s_simyea = year

    print("#####################################")
    print("Creating soil moisture conditions for day:")
    print("%s-%s-%s" % (year, smonstr, sdaystr))

    # open the sample deck for namelist WPS
    fin_wps = open(indeck_wps, "r")

    # open the namelist.wps I am creating
    fout_wps = open(f"{wrf_dir}/namelist.wps", "w")

    # Loop over the lines in the input file that need modification

    for lines in fin_wps.readlines():
        lines = lines.replace("%syear%", str(s_simyea))
        lines = lines.replace("%smonth%", smonstr)
        lines = lines.replace("%sday%", sdaystr)

        fout_wps.write(lines)
    fin_wps.close()
    fout_wps.close()

    # NAMELSIT CREATED
    ###########################################################
    ###########################################################

    # RUNNING WPS PROGRAMS AND REAL
    os.rename("%s/namelist.wps" % (wrf_dir), "%s/namelist.wps" % (wps_dir))
    os.chdir(wps_dir)

    subprocess.call("ln -sf  Vtable.ERA5.SOIL1ststep Vtable", shell=True)

    ###########################################################
    ###########################################################
    #  UNGRIB

    print("Running ungrib.exe")

    # this only works for 1-day runs for now.

    grbfiles = sorted(glob(f"{grb_dir}/era5_daily_sfc_{year}{smonstr}{sdaystr}.grb"))
    # subprocess.call("./link_grib.csh %s/era5_daily_*_%s%s%s.grb %s/era5_daily_*_%s%s%s.grb" %(grb_dir,s_simyea,smonstr,sdaystr,grb_dir,e_simyea,emonstr,edaystr), shell=True)
    subprocess.call(
        "./link_grib.csh %s" % (" ".join(str(x) for x in grbfiles)), shell=True
    )

    flogname = "ungrib.log"
    flog = open(flogname, "w")
    subprocess.call("./ungrib.exe ", stdout=flog, shell=True)
    flog.close()

    completed = check_output(flogname, 4, "Successful completion")

    if completed:
        print("ungrib completed successfully")
    else:
        raise Exception(
            "ERROR: ungrib program did not finish successfully, check %s" % (flogname)
        )

    # subprocess.call("mv SOILERA5:* %s/WRF-Intermediate/" % (grb_dir), shell=True)
    subprocess.call("rm -f PFILE:*", shell=True)
    subprocess.call("rm -f GRIBFILE*", shell=True)

    os.chdir(wrf_dir)
    year = year + 1
