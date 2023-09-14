#!/usr/bin/env python

""" write_intermediate_ERA5_CMIP5anom.py
run write_intermediate_ERA5_CMIP5anom.py -s 2007 -e 2007

Authors: Daniel Argueso- Alejandro Di Luca @ CCRC, UNSW. Sydney (Australia)
email: a.diluca@unsw.edu.au

Created: Wed Jun 17 14:08:31 AEST 2015




Modified: March 23 2016
 - I added a conversion from relative humidity to specific humidity for the 3-d variable (Alejandro)
 - I added a mask to the surface temperature so the output looks the same as the ERA-Interm field (Alejandro)

Modified: May 30 2016
 - (Alejandro) I modified the calculation of the specific humidity in two ways:
    1) For vertical levels in the stratosphere (p<50 hPa) I assume that the saturation pressure is
    zero in the denominator in the calculation of the saturation mixing ratio. Otherwise, saturation
    vapor pressure becomes large than the total pressure!!!
    2) I set all specific humidity values smaller than zero to zero. Generally there are no values smaller
    than zero.

Modified March 27 2018
 - Adapted to ERA5 from a version for ERA-Interim (Daniel)

Modified Sept 6 2018 (from Alejandro July 9 2018 ERA-Interim version write_intermediate_ERAI_CMIP5anom.py)
 - (Alejandro) Netcdf files in /srv/ccrc/data19/z3393020/ERA-interim_CMIP5anom/ have different dimensions for
 files after EIN201401_an_pl.nc (see below).
 In files BEFORE EIN201401_an_pl.nc the pressure level variables is called lev
 In files AFTER EIN201401_an_pl.nc the pressure level variables is called plev

[z3444417@monsoon ERA-interim_CMIP5anom]$ ncdump -h EIN201401_an_pl.nc | grep plev
        plev = 37 ;
        double plev(plev) ;

[z3444417@monsoon ERA-interim_CMIP5anom]$ ncdump -h EIN201312_an_pl.nc | grep lev
        lev = 37 ;
        double lev(lev) ;
                lev:standard_name = "air_pressure" ;
                lev:long_name = "pressure" ;

 The name is not the only difference. The main difference is that in files BEFORE EIN201401_an_pl.nc the levels
 were order from the minima to the maxima while in files AFTER EIN201401_an_pl.nc the levels were order from the maximum
 to the minimum. So all calculation were wrong using the original script for events after 01-2014

I have now modified the script so it checks the name and order of the pressure vertical levels.

Modified July 7 2021
 - Adapted to CMIP6 and ERA5 (Daniel Argüeso)
 - Part of the EPICC project



"""

import netCDF4 as nc
import numpy as np
from constants import const
import glob as glob
from optparse import OptionParser
import calendar
import outputInter as f90
import datetime as dt
import sys
import matplotlib.pyplot as plt
import wrf_variables as fs
import copy as cp
import pdb
import os


def checkfile(file_out, overwrite):
    """Checks if the output file exist and whether it should be written or not"""

    # ***********************************************************
    # BEFORE READING AND PROCESSING THE VARIABLE OF INTEREST CHECK
    # IF THE FILE ALREADY EXISTS
    # If it does then go to the next one...
    fileexist = os.path.exists(file_out)
    filewrite = False
    if overwrite == "False":
        overwrite = False

    print("  --> OUTPUT FILE:")
    print("         ", file_out)
    if fileexist == True:
        if overwrite == False:
            print("          +++ FILE ALREADY EXISTS +++")
            filewrite = False
        else:
            print("           +++ FILE EXISTS AND WILL BE OVERWRITTEN +++")
            filewrite = True
    else:
        print("         +++ FILE DOES NOT EXISTS YET +++")
        filewrite = True
    return filewrite


def calc_midmonth(year):
    midm_date = []

    for month in range(1, 13):
        minit = dt.datetime(year, month, 0o1, 00)
        if month == 12:
            mend = dt.datetime(year + 1, 1, 0o1, 0o1)
        else:
            mend = dt.datetime(year, month + 1, 0o1, 0o1)
        tdiference = (mend - minit).total_seconds() / 2
        midm_date = midm_date + [minit + dt.timedelta(seconds=tdiference)]

    tdiference = (
        dt.datetime(year, 1, 0o1, 0o1) - dt.datetime(year - 1, 12, 0o1, 0o1)
    ).total_seconds() / 2
    midm_date = [
        dt.datetime(year - 1, 12, 0o1, 0o1) + dt.timedelta(seconds=tdiference)
    ] + midm_date

    tdiference = (
        dt.datetime(year + 1, 2, 0o1, 0o1) - dt.datetime(year + 1, 1, 0o1, 0o1)
    ).total_seconds() / 2
    midm_date = midm_date + [
        dt.datetime(year + 1, 1, 0o1, 0o1) + dt.timedelta(seconds=tdiference)
    ]

    return midm_date


def calc_relhum(dewpt, t):
    """Function to calculate relative humidity
    from dew point temperature and temperature
    """

    relhum = 100.0 * (
        np.exp((const.es_Abolton * dewpt) / (const.es_Bbolton + dewpt))
        / np.exp((const.es_Abolton * t) / (const.es_Bbolton + t))
    )
    return relhum


### Options
parser = OptionParser()
parser.add_option(
    "-s",
    "--syear",
    type="int",
    dest="syear",
    help="first year to process",
    metavar="input argument",
)
parser.add_option(
    "-e",
    "--eyear",
    type="int",
    dest="eyear",
    help="last year to process",
    metavar="input argument",
)

(opts, args) = parser.parse_args()
###

overwrite_file = False
create_figs = False
syear = opts.syear
eyear = opts.eyear
nyears = eyear - syear + 1
smonth = 1
emonth = 1 

vars3d = ["hur", "ta", "ua", "va", "zg"]
vars3d_codes = {"hur": "r", "ta": "t", "ua": "u", "va": "v", "zg": "z"}
# vars3d_codes={'hur':'var157','ta':'var130','ua':'var131','va':'var132','zg':'var129'}
vars2d = ["hurs", "tas", "uas", "vas", "ps", "psl", "ts"]
vars2d_codes = {
    "dew": "2d",
    "tas": "2t",
    "uas": "10u",
    "vas": "10v",
    "ps": "sp",
    "psl": "msl",
    "ts": "skt",
}
# vars2d_codes={'dew':'var168','tas':'var167','uas':'var165','vas':'var166','ps':'var134','psl':'var151','ts':'var235'}
var_units_era5 = {
    "z": "m2 s-2",
    "t": "K",
    "u": "m s-1",
    "v": "m s-1",
    "sp": "Pa",
    "msl": "Pa",
    "ts": "K",
    "r": "1",
    "10u": "m s-1",
    "10v": "m s-1",
    "2t": "K",
    "2d": "K",
    "lsm": "0/1 Flag",
}

nfields3d = len(vars3d)
nfields2d = len(vars2d)

CMIP6anom_dir = "/home/dargueso/BDY_DATA/CMIP6"
ERA5_dir = "/home/dargueso/BDY_DATA/ERA5/ERA5_netcdf"
figs_path = "/home/dargueso/BDY_DATA/CMIP6/Figs"

plvs = [
    100000.0,
    97500.00,
    95000.00,
    92500.00,
    90000.00,
    87500.00,
    85000.00,
    82500.00,
    80000.00,
    77500.00,
    75000.00,
    70000.00,
    65000.00,
    60000.00,
    55000.00,
    50000.00,
    45000.00,
    40000.00,
    35000.00,
    30000.00,
    25000.00,
    22500.00,
    20000.00,
    17500.00,
    15000.00,
    12500.00,
    10000.00,
    7000.00,
    5000.00,
    3000.00,
    2000.00,
    1000.000,
    700.00,
    500.00,
    300.00,
    200.00,
    100.00,
]

nlat = 601
nlon = 1200


file_ref = nc.Dataset("%s/era5_daily_sfc_20140101.nc" % (ERA5_dir), "r")
lat = file_ref.variables["lat"][:]
lon = file_ref.variables["lon"][:]

olon, olat = np.meshgrid(lon, lat)


year = syear
month = smonth
day = 1

while year < eyear or (year == eyear and month < emonth):
    midmonth = calc_midmonth(year)

    print("processing year %s month %02d day %02d" % (year, month, day))

    ferapl = nc.Dataset(
        "%s/era5_daily_pl_%s%02d%02d.nc" % (ERA5_dir, year, month, day), "r"
    )
    ferasfc = nc.Dataset(
        "%s/era5_daily_sfc_%s%02d%02d.nc" % (ERA5_dir, year, month, day), "r"
    )

    date_init = dt.datetime(year, month, day, 00)
    date_end = dt.datetime(year, month, day, 18)

    time_filepl = ferapl.variables["time"]
    time_filesfc = ferasfc.variables["time"]

    date1 = nc.date2index(date_init, time_filepl, calendar="standard", select="exact")
    date2 = nc.date2index(date_end, time_filepl, calendar="standard", select="exact")
    ndays = (date_end - date_init).total_seconds() / 86400.0 + 1
    nsteps = int((date_end - date_init).total_seconds() / 86400.0 * 4.0 + 1)

    vout = {}
    print("Looping over timesteps in original ERA5 file")

    for nt in range(date1, date2 + 1):
        proc_date = nc.num2date(
            time_filepl[nt], units=time_filepl.units, calendar="standard"
        )
        print("processing 3Dvar time: ", proc_date)
        Y = str(proc_date.year)
        M = str(proc_date.month)
        D = str(proc_date.day)
        H = str(proc_date.hour)
        filedate = proc_date.strftime("%Y-%m-%d_%H-%M-%S")

        # CHECK IF THE FILE ALREADY EXISTS
        file_out = (
            "ERA5:"
            + filedate.split("_")[0]
            + "_"
            + filedate.split("_")[1].split("-")[0]
        )
        filewrite = checkfile(file_out, overwrite_file)
        if filewrite == True:
            tdelta = np.asarray(
                [
                    (midmonth[i] - proc_date).total_seconds()
                    for i in range(len(midmonth))
                ]
            )
            tdelta_min = np.argmin(np.abs(tdelta))
            if tdelta[tdelta_min] < 0:
                i1 = (tdelta_min - 1) % 12
                i2 = (tdelta_min) % 12
                tdelta_before = np.abs(tdelta[tdelta_min])
                tdelta_mid_month = (
                    midmonth[tdelta_min + 1] - midmonth[tdelta_min]
                ).total_seconds()
            else:
                i1 = (tdelta_min - 2) % 12
                i2 = (tdelta_min - 1) % 12
                tdelta_before = np.abs(tdelta[tdelta_min - 1])
                tdelta_mid_month = (
                    midmonth[tdelta_min] - midmonth[tdelta_min - 1]
                ).total_seconds()

            for var in vars3d:
                print("Processing variable %s" % (var))

                fanom = nc.Dataset(
                    "%s/%s_CC_signal_ssp585_2070-2099_1985-2014_pinterp.nc"
                    % (CMIP6anom_dir, var)
                )
                var_era = ferapl.variables["%s" % (vars3d_codes[var])][nt, ::-1, :, :]
                # anom_units=getattr(fanom.variables["%s" %(var)],'units')
                ilon, ilat = np.meshgrid(
                    fanom.variables["lon"][:], fanom.variables["lat"][:]
                )

                # Convert geopotential height from m2/s2 to m
                if var == "zg":
                    var_era = var_era / 9.81
                    var_units_era5["%s" % (vars3d_codes[var])] = "m"

                if np.argmin(np.abs(tdelta)) == 0:
                    var_anom = fanom.variables["%s" % (var)][i1, ::-1, :, :]

                else:
                    var_anom_1 = fanom.variables["%s" % (var)][i1, ::-1, :, :]
                    var_anom_2 = fanom.variables["%s" % (var)][i2, ::-1, :, :]

                    var_anom = (
                        var_anom_1
                        + (var_anom_2 - var_anom_1) * (tdelta_before) / tdelta_mid_month
                    )

                # Convert relative humidity to specific humidity
                # if var == "hus":
                #     # Read temperature and pressure
                #     varT = ferapl.variables["%s" % (vars3d_codes["ta"])][
                #         nt, ::-1, :, :
                #     ]
                #     varP = np.repeat(
                #         np.repeat(plvs, varT.shape[1]), varT.shape[2]
                #     )
                #     varP = varP.reshape(
                #         varT.shape[0], varT.shape[1], varT.shape[2]
                #     )  # varP is in Pa

                #     es = 100.0 * fs.compute_es(
                #         varT
                #     )  # the result of compute is in hPa
                #     es_mod = cp.deepcopy(es)
                #     es_mod[
                #         30:, :, :
                #     ] = 0  # saturation pressure equal zero in the stratosphere (levels over 20 hPa)
                #     ws = es * const.Rd / (const.Rv * (varP - es_mod))
                #     w = ws * var_era / 100.0
                #     var_era = w / (w + 1)

                # # Define the pseudo global warming
                # temp = var_era + np.nan_to_num(var_anom)
                # if var == "hus":
                #     temp[
                #         temp < 0
                #     ] = 0  # replace values smaller than zero by zero
                # vout[var] = temp
                # fanom.close()
                # Define the pseudo global warming
                temp = var_era + np.nan_to_num(var_anom)
                if var == "hur":
                    temp[temp < 0] = 0  # replace values smaller than zero by zero
                    temp[temp > 100] = 100
                vout[var] = temp
                fanom.close()

                # -----------------------------------------------------------------------------------------------
                # MAKE PLOT
                if create_figs == True:
                    nlev = 10
                    file_name = {0: "era5", 1: "anom", 2: "pgw"}
                    for ii in range(3):
                        if ii == 0:
                            aa = var_era[nlev, :]
                            units = var_units_era5["%s" % (vars3d_codes[var])]
                        if ii == 1:
                            aa = var_anom[nlev, :]
                            units = var_units_era5["%s" % (vars3d_codes[var])]
                        if ii == 2:
                            aa = vout[var][nlev, :]
                        figname = figs_path + "%s_lev%s_%s_%s-%s-%s-%s.png" % (
                            var,
                            str(nlev),
                            file_name[ii],
                            Y,
                            M,
                            D,
                            H,
                        )
                        plt.contourf(aa)
                        plt.colorbar()
                        plt.title(var + " [" + units + "]")
                        plt.savefig(figname)
                        plt.close()

                # -----------------------------------------------------------------------------------------------

            for var in vars2d:
                print("Processing variable %s" % (var))
                if var == "hurs":
                    # Surface relative humidity doesn't exist in original ERA-INt, must be calculated from T2 and DEWPT
                    dew_era = (
                        ferasfc.variables[vars2d_codes["dew"]][nt, :, :] - const.tkelvin
                    )
                    tas_era = (
                        ferasfc.variables[vars2d_codes["tas"]][nt, :, :] - const.tkelvin
                    )

                    var_era = calc_relhum(dew_era, tas_era)

                else:
                    var_era = ferasfc.variables["%s" % (vars2d_codes[var])][nt, :, :]

                fanom = nc.Dataset(
                    "%s/%s_CC_signal_ssp585_2070-2099_1985-2014.nc"
                    % (CMIP6anom_dir, var)
                )
                # if hasattr(fanom.variables["%s" %(var)],'units'):
                #     anom_units=getattr(fanom.variables["%s" %(var)],'units')
                # else:
                #     if var == 'hurs':
                #       anom_units=''
                #     else:
                #       import pdb; pdb.set_trace()
                ilon, ilat = np.meshgrid(
                    fanom.variables["lon"][:], fanom.variables["lat"][:]
                )

                if np.min(np.abs(tdelta)) == 0:
                    var_anom = fanom.variables["%s" % (var)][i1, :, :]
                else:
                    var_anom_1 = fanom.variables["%s" % (var)][i1, :, :]
                    var_anom_2 = fanom.variables["%s" % (var)][i2, :, :]

                    var_anom = (
                        var_anom_1
                        + (var_anom_2 - var_anom_1) * (tdelta_before) / tdelta_mid_month
                    )

                # var_anom = interpolate_grid(ilat,ilon,var_anom_c,olat,olon,method='nearest')

                # Define the pseudo global warming
                vout[var] = var_era + np.nan_to_num(var_anom)

                # if var=='ts':
                # import pdb; pdb.set_trace()
                # vout[var][var_era.mask==True]=
                # vout[var][var_era==-9.e+33]=-9.e+33

                # -----------------------------------------------------------------------------------------------
                # MAKE PLOT
                if create_figs == True:
                    file_name = {0: "era5", 1: "anom", 2: "pgw"}
                    for ii in range(3):
                        if ii == 0:
                            aa = var_era[:]
                            if var == "hurs":
                                units = "%"
                            else:
                                units = var_units_era5["%s" % (vars2d_codes[var])]
                        if ii == 1:
                            aa = var_anom[:]
                            units = anom_units
                        if ii == 2:
                            aa = vout[var][:]
                        figname = figs_path + "%s_%s_%s-%s-%s-%s.png" % (
                            var,
                            file_name[ii],
                            Y,
                            M,
                            D,
                            H,
                        )
                        plt.contourf(aa)
                        plt.colorbar()
                        plt.title(var + " [" + units + "]")
                        plt.savefig(figname)
                        plt.close()
                        # -----------------------------------------------------------------------------------------------

                fanom.close()

            # ###################################################################################################
            ####################  Writing to WRF intermediate format  #############################
            filedate = proc_date.strftime("%Y-%m-%d_%H-%M-%S")

            fields3d = np.ndarray(
                shape=(nfields3d, len(plvs), nlat, nlon), dtype="float32"
            )  # ,order='Fortran')
            fields2d = np.ndarray(
                shape=(nfields2d, nlat, nlon), dtype="float32"
            )  # ,order='Fortran')

            startlat = lat[0]
            startlon = lon[0]
            deltalon = 0.30
            deltalat = -0.30

            fields3d[0, :, :, :] = np.float32(vout["hur"])
            fields3d[1, :, :, :] = np.float32(vout["ta"])
            fields3d[2, :, :, :] = np.float32(vout["ua"])
            fields3d[3, :, :, :] = np.float32(vout["va"])
            fields3d[4, :, :, :] = np.float32(vout["zg"])

            fields2d[0, :, :] = np.float32(vout["uas"])
            fields2d[1, :, :] = np.float32(vout["vas"])
            fields2d[2, :, :] = np.float32(vout["hurs"])
            fields2d[3, :, :] = np.float32(vout["ps"])
            fields2d[4, :, :] = np.float32(vout["psl"])
            fields2d[5, :, :] = np.float32(vout["tas"])
            fields2d[6, :, :] = np.float32(vout["ts"])

            f90.writeint(
                plvs,
                fields3d,
                fields2d,
                filedate,
                nlat,
                nlon,
                startlat,
                startlon,
                deltalon,
                deltalat,
            )
            # ###################################################################################################
    end_date = dt.datetime(year, month, day) + dt.timedelta(days=1)
    year = end_date.year
    month = end_date.month
    day = end_date.day
