#!/usr/bin/env python
"""pgw4era.cryowrf.write_intermediate_onetimestep

Variant of :mod:`pgw4era.cryowrf.write_intermediate` that writes **one output
file per timestep** rather than appending to a single file per day.  This is
useful when downstream tools expect one-file-per-timestep layout.

Enable via the ``one_timestep_files = true`` option in the CRYOWRF profile of
``pgw4era.toml``.

The public entry point is :func:`run`, with the same signature as the
standard CRYOWRF variant.
"""

from __future__ import annotations

import datetime as dt
from types import SimpleNamespace

import netCDF4 as nc
import numpy as np

from pgw4era.constants import const

# Re-use all common logic from the standard CRYOWRF module; only the file-writing
# loop is overridden here.
from pgw4era.cryowrf.write_intermediate import (
    _N2D,
    _RHO_WATER,
    PLVS,
    VARS2D_CODES,
    VARS3D_CODES,
    f90,
)
from pgw4era.utils import calc_midmonth, calc_relhum, checkfile


def run(cfg: SimpleNamespace, overwrite_file: bool = False, create_figs: bool = False) -> None:
    """Write one CRYOWRF intermediate file per timestep.

    Identical to :func:`pgw4era.cryowrf.write_intermediate.run` except that
    the output file for each timestep is written before moving on to the next.

    Parameters
    ----------
    cfg:
        Configuration namespace returned by :func:`pgw4era.config.load_config`.
    overwrite_file:
        If ``True``, overwrite existing output files.
    create_figs:
        Unused; kept for API consistency.
    """
    syear = cfg.syear
    eyear = cfg.eyear
    smonth = cfg.smonth
    emonth = cfg.emonth
    experiments = cfg.experiments
    year_ranges = cfg.periods
    syearp, eyearp = year_ranges[0]
    syearf, eyearf = year_ranges[1]

    vars3d = cfg.variables_3d
    vars2d = cfg.variables_2d
    nfields3d = len(vars3d)

    CMIP6anom_dir = cfg.CMIP6anom_dir
    ERA5_dir = cfg.ERA5netcdf_dir

    file_ref = nc.Dataset(f"{cfg.ERA5netcdf_dir}/{cfg.ERA5_sfc_ref_file}")
    lat = file_ref.variables["latitude"][:]
    lon = file_ref.variables["longitude"][:]
    file_ref.close()

    nlon = len(lon)
    nlat = len(lat)

    year, month, day = syear, smonth, 1

    while year < eyear or (year == eyear and month < emonth):
        midmonth = calc_midmonth(year)

        print(f"processing year {year} month {month:02d} day {day:02d}")

        ferapl = nc.Dataset(f"{ERA5_dir}/era5_daily_pl_{year}{month:02d}{day:02d}.nc", "r")
        ferasfc = nc.Dataset(f"{ERA5_dir}/era5_daily_sfc_{year}{month:02d}{day:02d}.nc", "r")

        date_init = dt.datetime(year, month, day, 0)
        date_end = dt.datetime(year, month, day, 21)

        time_filepl = ferapl.variables["time"]

        date1 = nc.date2index(date_init, time_filepl, calendar="standard", select="exact")
        date2 = nc.date2index(date_end, time_filepl, calendar="standard", select="exact")

        vout: dict[str, np.ndarray] = {}

        for nt in range(date1, date2 + 1):
            proc_date = nc.num2date(time_filepl[nt], units=time_filepl.units, calendar="standard")
            print("processing time: ", proc_date)
            filedate = proc_date.strftime("%Y-%m-%d_%H-%M-%S")

            file_out = "ERA5:" + filedate.split("_")[0] + "_" + filedate.split("_")[1].split("-")[0]
            filewrite = checkfile(file_out, overwrite_file)
            if not filewrite:
                continue

            tdelta = np.asarray(
                [(midmonth[i] - proc_date).total_seconds() for i in range(len(midmonth))]
            )
            tdelta_min = np.argmin(np.abs(tdelta))
            if tdelta[tdelta_min] < 0:
                i1 = (tdelta_min - 1) % 12
                i2 = (tdelta_min) % 12
                tdelta_before = np.abs(tdelta[tdelta_min])
                tdelta_mid_month = (midmonth[tdelta_min + 1] - midmonth[tdelta_min]).total_seconds()
            else:
                i1 = (tdelta_min - 2) % 12
                i2 = (tdelta_min - 1) % 12
                tdelta_before = np.abs(tdelta[tdelta_min - 1])
                tdelta_mid_month = (midmonth[tdelta_min] - midmonth[tdelta_min - 1]).total_seconds()

            for var in vars3d:
                fanom = nc.Dataset(
                    f"{CMIP6anom_dir}/{var}_{syearp}-{eyearp}_{syearf}-{eyearf}"
                    f"_{experiments[0]}-{experiments[1]}_CC_signal_pinterp.nc"
                )
                if np.all(np.diff(ferapl.variables["level"][:]) > 0):
                    var_era = ferapl.variables[VARS3D_CODES[var]][nt, ::-1, :, :]
                else:
                    var_era = ferapl.variables[VARS3D_CODES[var]][nt, :, :, :]

                if var == "zg":
                    var_era = var_era / 9.81

                if np.argmin(np.abs(tdelta)) == 0:
                    var_anom = fanom.variables[var][i1, ::-1, :, :]
                else:
                    var_anom_1 = fanom.variables[var][i1, ::-1, :, :]
                    var_anom_2 = fanom.variables[var][i2, ::-1, :, :]
                    var_anom = (
                        var_anom_1 + (var_anom_2 - var_anom_1) * tdelta_before / tdelta_mid_month
                    )

                temp = var_era + np.nan_to_num(var_anom)
                if var == "hur":
                    temp = np.clip(temp, 0, 100)
                vout[var] = temp
                fanom.close()

            for var in vars2d:
                if var == "hurs":
                    dew_era = ferasfc.variables[VARS2D_CODES["dew"]][nt, :, :] - const.tkelvin
                    tas_era = ferasfc.variables[VARS2D_CODES["tas"]][nt, :, :] - const.tkelvin
                    var_era = calc_relhum(dew_era, tas_era)
                else:
                    var_era = ferasfc.variables[VARS2D_CODES[var]][nt, :, :]

                fanom = nc.Dataset(
                    f"{CMIP6anom_dir}/{var}_{syearp}-{eyearp}_{syearf}-{eyearf}"
                    f"_{experiments[0]}-{experiments[1]}_CC_signal.nc"
                )
                if np.min(np.abs(tdelta)) == 0:
                    var_anom = fanom.variables[var][i1, :, :]
                else:
                    var_anom_1 = fanom.variables[var][i1, :, :]
                    var_anom_2 = fanom.variables[var][i2, :, :]
                    var_anom = (
                        var_anom_1 + (var_anom_2 - var_anom_1) * tdelta_before / tdelta_mid_month
                    )

                vout[var] = var_era + np.nan_to_num(var_anom)
                fanom.close()

            # Snow fields
            if "sd" in ferasfc.variables:
                snow_we = ferasfc.variables["sd"][nt, :, :] * _RHO_WATER
            else:
                snow_we = np.zeros((nlat, nlon), dtype="float32")

            if "rsn" in ferasfc.variables:
                rho_snow = ferasfc.variables["rsn"][nt, :, :]
                rho_snow = np.where(rho_snow > 0, rho_snow, 300.0)
            else:
                rho_snow = np.full((nlat, nlon), 300.0, dtype="float32")

            snow_depth = snow_we / rho_snow

            fields3d = np.ndarray(shape=(nfields3d, len(PLVS), nlat, nlon), dtype="float32")
            fields2d = np.ndarray(shape=(_N2D, nlat, nlon), dtype="float32")

            startlat = float(lat[0])
            startlon = float(lon[0])
            deltalon = 0.30
            deltalat = -0.30

            fields3d[0] = np.float32(vout["hur"])
            fields3d[1] = np.float32(vout["ta"])
            fields3d[2] = np.float32(vout["ua"])
            fields3d[3] = np.float32(vout["va"])
            fields3d[4] = np.float32(vout["zg"])

            fields2d[0] = np.float32(vout["uas"])
            fields2d[1] = np.float32(vout["vas"])
            fields2d[2] = np.float32(vout["hurs"])
            fields2d[3] = np.float32(vout["ps"])
            fields2d[4] = np.float32(vout["psl"])
            fields2d[5] = np.float32(vout["tas"])
            fields2d[6] = np.float32(vout["ts"])
            fields2d[7] = np.float32(snow_we)
            fields2d[8] = np.float32(snow_depth)

            # Write one file per timestep
            f90.writeint(
                PLVS,
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

        ferapl.close()
        ferasfc.close()

        end_date = dt.datetime(year, month, day) + dt.timedelta(days=1)
        year, month, day = end_date.year, end_date.month, end_date.day
