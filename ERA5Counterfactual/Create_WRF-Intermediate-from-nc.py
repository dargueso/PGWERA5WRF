import netCDF4 as nc
import numpy as np
import pywinter.winter as pyw
import datetime as dt
import xarray as xr
from optparse import OptionParser
import os
from constants import const


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
    if fileexist is True:
        if overwrite is False:
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

overwrite_file = True

syear = opts.syear
eyear = opts.eyear
nyears = eyear - syear + 1
smonth = 9
emonth = 9
sday = 1
eday = 12


vars3d = ["r", "t", "u", "v", "z"]
vars2d = ["d2m", "t2m", "u10", "v10", "sp", "msl", "sst", "stl1", "stl2", "stl3", "stl4","swvl1", "swvl2", "swvl3", "swvl4"]

vars2d_codes = {
    "d2m": "2d",
    "t2m": "2t",
    "u10": "10u",
    "v10": "10v",
    "sp": "sp",
    "msl": "msl",
    "sst": "sst",
    "stl1": "stl1",
    "stl2": "stl2",
    "stl3": "stl3",
    "stl4": "stl4",
    "swvl1": "swvl1",
    "swvl2": "swvl2",
    "swvl3": "swvl3",
    "swvl4": "swvl4",
}

varsout_codes = {
    "t2m": "TT",
    "hurs": "RH",
    "u10": "UU",
    "v10": "VV",
    "sp": "PSFC",
    "msl": "PMSL",
    "sst": "SST",
    "st": "ST",
    "sm": "SM",
    "r": "RH",
    "t": "TT",
    "u": "UU",
    "v": "VV",
    "zg": "GHT",
}

sl_layer = ['000007','007028','028100','100289']

#####################################################################
#####################################################################


d1  = dt.datetime(syear, smonth, sday)
d2  = dt.datetime(eyear, emonth, eday)


# Load the data

ERA5_cfact = "/vg9b/dargueso-NOBKUP/BDY_DATA/ERA5/ERA5_counterfactual/"
ERA5_dir = "/home/dargueso/BDY_DATA/ERA5/ERA5_netcdf"


d1 = dt.datetime(2023, 9, 1)
d2 = dt.datetime(2023, 9, 12)

# total_days = (d2 - d1).days
# date_list = [d1 + dt.timedelta(days=x) for x in range(0, total_days)]

total_hours = (d2 - d1).days * 24 + (d2 - d1).total_seconds() // 3600
date_list = [d1 + dt.timedelta(hours=x) for x in range(0, int(total_hours),3)]

file_ref = xr.open_dataset(ERA5_dir + "/era5_daily_sfc_20120101.nc")
lat = file_ref.lat.values
lon = file_ref.lon.values
dlat = -np.abs(lat[1] - lat[0]) #ERA5 starts from North to South
dlon = np.abs(lon[1] - lon[0])
winter_geo = pyw.Geo0(lat[0], lon[0], dlat, dlon)


for date in date_list:
    
    vout = {}
    total_fields = []
    midmonth = calc_midmonth(date.year)
    
    print("processing date: ", date)
    
    #Read ERA5 data
    ferapl = nc.Dataset(ERA5_dir + f"/era5_daily_pl_" + date.strftime("%Y%m%d") + ".nc", "r")
    ferasfc = nc.Dataset(ERA5_dir + f"/era5_daily_sfc_" + date.strftime("%Y%m%d") + ".nc", "r")
    
    plvs = ferapl.variables['plev'][:]
    
    #Read ERA5 counterfactual data anomalies
    fanompl = nc.Dataset(ERA5_cfact + f"/era5_monthly_pl_2000-2019_1940-1959.nc", "r")
    fanomsfc = nc.Dataset(ERA5_cfact + f"/era5_monthly_sfc_2000-2019_1940-1959.nc", "r")
    
    time_filepl = ferapl.variables["time"]
    time_filesfc = ferasfc.variables["time"]
    
    nt = nc.date2index(date, time_filepl, calendar="standard", select="exact")
    proc_date = nc.num2date(time_filepl[nt], time_filepl.units, calendar="standard")
    
    
    filedate = proc_date.strftime("%Y-%m-%d_%H-%M-%S")
    print("processing date: ", filedate + " (index: " + str(nt) + ")")
    
    #Define output file and check if it exists
    
    file_out = ("ERA5:" + filedate.split("_")[0] + "_" + filedate.split("_")[1].split("-")[0])
    
    filewrite = checkfile(file_out, overwrite_file)
    
    if filewrite is True:
        
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
            var_era = ferapl.variables[var][nt, ::-1, :, :]
            
            if np.any(tdelta) == 0:
                var_anom = fanompl.variables[var][i1, ::-1, :, :]
            else:
                var_anom_1 = fanompl.variables[var][i1, ::-1, :, :]
                var_anom_2 = fanompl.variables[var][i2, ::-1, :, :]
                
                var_anom = (var_anom_1 + (var_anom_2 - var_anom_1) * (tdelta_before) / tdelta_mid_month)
                
            #Define counterfactual variable    
            tmp = var_era + np.nan_to_num(var_anom)   
            vout[var] = tmp.copy()
        
        for var in vars2d:
            
            print("Processing variable %s" % (var))
            var_era = ferasfc.variables[vars2d_codes[var]][nt, :, :]
            
            if np.min(np.abs(tdelta)) == 0:
                var_anom = fanomsfc.variables[var][i1, :, :]
            else:
                var_anom_1 = fanomsfc.variables[var][i1, :, :]
                var_anom_2 = fanomsfc.variables[var][i2, :, :]

                var_anom = (var_anom_1 + (var_anom_2 - var_anom_1) * (tdelta_before) / tdelta_mid_month)
            
            #Define the counterfactual variable
            tmp = var_era + np.nan_to_num(var_anom)
            vout[var] = tmp
            
        
            
        for var in varsout_codes.keys():
            
            if var == 'hurs':
                 # Convert dew point temperature to relative humidity near the surface
                vout["hurs"] = calc_relhum(vout["d2m"], vout["t2m"])
                vout["hurs"][vout["hurs"] < 0] = 0
                vout["hurs"][vout["hurs"] > 100] = 100

            elif var == "r":
                #Limit relative humidity to 0 and 100
                vout["r"][vout["r"] < 0] = 0
                vout["r"][vout["r"] > 100] = 100
            
            elif var == "zg":
                # Convert geopotential to geopotential height
                vout["zg"] = vout["z"] / const.g
                
        
            if var in ["t","r","u","v","zg"]:
                
        
                total_fields.append(pyw.V3dp(varsout_codes[var],vout[var],plvs))
                
            elif var in ["sst"]:
                
                total_fields.append(pyw.V2d(varsout_codes[var],vout[var]))
            
            elif var in ["t2m","hurs","u10","v10","sp","msl",]:
                
                total_fields.append(pyw.V2d(varsout_codes[var],vout[var].data))
            
            elif var in ["sm","st"]:
                
                if var == 'st':
                    soilvar = np.concatenate([vout['stl1'],vout['stl2'],vout['stl3'],vout['stl4']])
                elif var == 'sm':
                    soilvar = np.concatenate([vout['swvl1'],vout['swvl2'],vout['swvl3'],vout['swvl4']])
                else:
                    raise ValueError("Variable not defined")
                

                total_fields.append(pyw.Vsl(varsout_codes[var],soilvar,sl_layer))
                
                
            else:
                raise ValueError("Variable not defined")
                    
                
            
    pyw.cinter("ERA5", f"{date.strftime('%Y-%m-%d')}_{date.hour:02d}", winter_geo, total_fields, "./")  
        
        
    
    













