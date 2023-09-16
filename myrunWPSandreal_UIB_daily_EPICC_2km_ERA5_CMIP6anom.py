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
import calendar
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


def sel_intfiles(filelist, sdate, edate):
    d1 = dt.date(int(sdate[0:4]), int(sdate[4:6]), int(sdate[6:8]))
    d2 = dt.date(int(edate[0:4]), int(edate[4:6]), int(edate[6:8]))

    years = np.array([fname.split(":")[-1].split("-")[0] for fname in filelist], int)
    months = np.array([fname.split(":")[-1].split("-")[1] for fname in filelist], int)
    days = np.array(
        [fname.split(":")[-1].split("-")[2][0:2] for fname in filelist], int
    )

    file_dates = np.array(
        [dt.date(years[i], months[i], days[i]) for i in range(len(years))]
    )

    selec_files = [
        filelist[i] for i, n in enumerate(file_dates) if ((n >= d1) & (n <= d2))
    ]

    return selec_files


def sel_grbfiles(filelist, sdate, edate):
    d1 = dt.date(int(sdate[0:4]), int(sdate[4:6]), int(sdate[6:8]))
    d2 = dt.date(int(edate[0:4]), int(edate[4:6]), int(edate[6:8]))

    years = np.array([fname.split("_")[-1][0:4] for fname in filelist], int)
    months = np.array([fname.split("_")[-1][4:6] for fname in filelist], int)
    days = np.array([fname.split("_")[-1][6:8] for fname in filelist], int)

    file_dates = np.array(
        [dt.date(years[i], months[i], days[i]) for i in range(len(years))]
    )

    selec_files = [
        filelist[i] for i, n in enumerate(file_dates) if ((n >= d1) & (n <= d2))
    ]

    return selec_files


# Start month of the simulation. Will start at day 1.

start_month = 1
start_year = 2012

# End month of the simulation (included).
end_month = 1
end_year = 2013


# How many days in advance (spin-up)?
spinup = 10

# name the input deck to use
indeck_wps = "namelist_wps_EPICC_2km_ERA5_CMIP6anom.deck"
indeck_wrf = "namelist_input_EPICC_2km_ERA5_CMIP6anom.deck"

this_dir = os.getcwd()
wrf_dir = "/home/dargueso/WRF_runs/EPICC_WRFV4.2.2_CMIP6PGW_copy/WRF/run"
wps_dir = "/home/dargueso/WRF_runs/EPICC_WRFV4.2.2_CMIP6PGW_copy/WPS"
grb_dir = "/vg6a/dargueso/BDY_DATA/ERA5_CMIP6anom/"
int_dir = "/vg5/dargueso/BDY_DATA/PGW_CMIP6_tests/"
bdy_dir = "/vg5/dargueso//BDY_DATA/PGW_CMIP6_tests"

run_geogrid = False
run_ungrib = False
run_metgrid = True

run_real = True

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
# day = 10
firstday = True


while year < end_year or (year == end_year and month < end_month):
    ## DEFINE SOILERA FILES
    # soilera5_file = f"SOILERA5:{start_year-1}-12-22_00"
    soilera5_file = "SOILERA5:2005-12-01_00"

    # get the month as a 2 digit string
    monthstr = str(month).rjust(2, "0")

    # Number of days in this month
    numdays = calendar.monthrange(year, month)[1]

    s_simyea = year
    s_simmon = month
    s_simday = day

    init_date = dt.datetime(year, month, day)
    end_date = dt.datetime(year, month, day) + dt.timedelta(days=lendays)

    if end_date > dt.datetime(end_year, end_month, 1):
        end_date = dt.datetime(end_year, end_month, 1)

    e_simyea = end_date.year
    e_simmon = end_date.month
    e_simday = end_date.day

    sdaystr = str(s_simday).rjust(2, "0")
    smonstr = str(s_simmon).rjust(2, "0")
    edaystr = str(e_simday).rjust(2, "0")
    emonstr = str(e_simmon).rjust(2, "0")

    print("#####################################")
    print("Creating boundary conditions for day:")
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
        lines = lines.replace("%eyear%", str(e_simyea))
        lines = lines.replace("%emonth%", emonstr)
        lines = lines.replace("%eday%", edaystr)
        lines = lines.replace("%soilera5_file%", soilera5_file)

        fout_wps.write(lines)
    fin_wps.close()
    fout_wps.close()

    # open the sample deck for namelist.input
    fin_wrf = open(indeck_wrf, "r")

    # open the namelist.input I am creating
    fout_wrf = open("namelist.input", "w")

    # Loop over the lines in the input file that need modification

    for lines in fin_wrf.readlines():
        lines = lines.replace("%syear%", str(s_simyea))
        lines = lines.replace("%smonth%", smonstr)
        lines = lines.replace("%sday%", sdaystr)
        lines = lines.replace("%eyear%", str(e_simyea))
        lines = lines.replace("%emonth%", emonstr)
        lines = lines.replace("%eday%", edaystr)

        fout_wrf.write(lines)

    fin_wrf.close()
    fout_wrf.close()

    # NAMELSITS CREATED
    ###########################################################
    ###########################################################

    # RUNNING WPS PROGRAMS AND REAL
    os.rename("%s/namelist.wps" % (wrf_dir), "%s/namelist.wps" % (wps_dir))
    os.chdir(wps_dir)

    ###########################################################
    ###########################################################
    #  GEOGRID

    if (run_geogrid) and (firstday):
        print("Running geogrid.exe")

        flogname = "geogrid.log"
        flog = open(flogname, "w")
        subprocess.call("./geogrid.exe ", stdout=flog, shell=True)
        flog.close()

        completed = check_output(flogname, 4, "Successful completion")

        if completed:
            print("geogrid completed successfully")
        else:
            raise Exception(
                "ERROR: geogrid program did not finish successfully, check %s"
                % (flogname)
            )

    ###########################################################
    ###########################################################
    #  UNGRIB

    if run_ungrib:
        print("Running ungrib.exe")

        # this only works for 1-day runs for now.

        grbfiles = sorted(glob("%s/era5_daily_*.grb" % (grb_dir)))

        sdatestr = "%s%s%s" % (s_simyea, smonstr, sdaystr)
        edatestr = "%s%s%s" % (e_simyea, emonstr, edaystr)

        grbfiles = sel_grbfiles(grbfiles, sdatestr, edatestr)

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
                "ERROR: ungrib program did not finish successfully, check %s"
                % (flogname)
            )

        subprocess.call("mv ERA5:* %s/WRF-Intermediate/" % (grb_dir), shell=True)
        subprocess.call("rm -f PFILE:*", shell=True)
        subprocess.call("rm -f GRIBFILE*", shell=True)

    ###########################################################
    ###########################################################
    # METGRID

    if run_metgrid:
        print("Running metgrid.exe")

        intfiles = sorted(glob("%s/ERA5:*" % (int_dir)))
        # intfiles = sorted(glob("%s/WRF-Intermediate/ERA5:*" % (grb_dir)))

        sdatestr = "%s%s%s" % (s_simyea, smonstr, sdaystr)
        edatestr = "%s%s%s" % (e_simyea, emonstr, edaystr)

        intfiles = sel_intfiles(intfiles, sdatestr, edatestr)

        for intfile in intfiles:
            subprocess.call("ln -sf %s ." % (intfile), shell=True)

        flogname = "metgrid.log"
        flog = open(flogname, "w")
        subprocess.call("./metgrid.exe ", stdout=flog, shell=True)
        flog.close()

        completed = check_output(flogname, 4, "Successful completion")

        if completed:
            print("metgrid completed successfully")
        else:
            raise Exception(
                "ERROR: metgrid program did not finish successfully, check %s"
                % (flogname)
            )

        os.system("rm ERA5:*")

    os.chdir(wrf_dir)

    ###########################################################
    ###########################################################
    #   REAL

    if run_real:
        print("Running real.exe")

        subprocess.call("ln -sf %s/met_em.d0?.*.nc ." % (wps_dir), shell=True)

        # flog = open(flogname,"r")
        subprocess.call("./real.exe ", shell=True)  # ,stdout=flog,shell=True)
        # flog.close()
        flogname = "rsl.out.0000"
        completed = check_output(flogname, 4, "SUCCESS COMPLETE REAL_EM INIT")

        if completed:
            print("real completed successfully")
        else:
            raise Exception(
                "ERROR: real program did not finish successfully, check %s" % (flogname)
            )

        bdy_filelist = glob("wrf*_d0?")

        for bdy_file in bdy_filelist:
            subprocess.call(
                "mv %s/%s %s/%s_%s-%s-%s"
                % (wrf_dir, bdy_file, bdy_dir, bdy_file, s_simyea, smonstr, sdaystr),
                shell=True,
            )

        subprocess.call("rm -f met_em.d0?.*.nc", shell=True)
        subprocess.call("rm -f %s/met_em.d0?.*.nc" % (wps_dir), shell=True)
        print("Boundary conditions created successfully")

    print("Requested WPS and WRF program completed successfully")
    print("#####################################")

    firstday = False

    year = end_date.year
    month = end_date.month
    day = end_date.day
