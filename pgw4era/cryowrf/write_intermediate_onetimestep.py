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

import calendar
import datetime as dt
import os
from types import SimpleNamespace

import netCDF4 as nc
import numpy as np
import xarray as xr

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
    _anom_sign = -1.0 if getattr(cfg, "reverse", False) else 1.0

    ERA5_dir = os.path.abspath(cfg.ERA5netcdf_dir)
    ensemble_dir = os.path.abspath(cfg.CMIP6ensemble_dir or cfg.CMIP6anom_dir)

    output_dir = cfg.output_dir
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        os.chdir(output_dir)

    file_ref = nc.Dataset(f"{ERA5_dir}/{cfg.ERA5_sfc_ref_file}")
    lat = file_ref.variables["latitude"][:]
    lon = file_ref.variables["longitude"][:]
    file_ref.close()

    nlon = len(lon)
    nlat = len(lat)

    startlat = float(lat[0])
    startlon = float(lon[0])
    deltalon = float(lon[1] - lon[0])
    deltalat = float(lat[1] - lat[0])

    sday = cfg.sday
    eday = cfg.eday or calendar.monthrange(eyear, emonth)[1]
    ERA5_pl_pattern = cfg.ERA5_pl_pattern
    ERA5_sfc_pattern = cfg.ERA5_sfc_pattern

    def _interp_anom(path, varname):
        """Load anomaly file and interpolate to ERA5 lat/lon grid."""
        with xr.open_dataset(path) as _ds:
            _da = _ds[varname]
            _lat_dim = next(d for d in _da.dims if "lat" in d.lower())
            _lon_dim = next(d for d in _da.dims if "lon" in d.lower())
            return _da.interp({_lat_dim: lat, _lon_dim: lon}, method="linear").values

    print("Pre-loading anomaly files and interpolating to ERA5 grid...")
    anom_cache_3d: dict[str, np.ndarray] = {}
    for _var in vars3d:
        _path = (
            f"{ensemble_dir}/interp_plevs/{_var}_{syearp}-{eyearp}_{syearf}-{eyearf}"
            f"_{experiments[0]}-{experiments[1]}_CC_signal_pinterp.nc"
        )
        anom_cache_3d[_var] = _interp_anom(_path, _var)
        print(f"  loaded 3D anom: {_var} shape={anom_cache_3d[_var].shape}")

    anom_cache_2d: dict[str, np.ndarray] = {}
    for _var in vars2d:
        _path = (
            f"{ensemble_dir}/{_var}_{syearp}-{eyearp}_{syearf}-{eyearf}"
            f"_{experiments[0]}-{experiments[1]}_CC_signal.nc"
        )
        anom_cache_2d[_var] = _interp_anom(_path, _var)
        print(f"  loaded 2D anom: {_var} shape={anom_cache_2d[_var].shape}")

    current_date = dt.datetime(syear, smonth, sday)
    loop_end = dt.datetime(eyear, emonth, eday)

    while current_date <= loop_end:
        year, month, day = current_date.year, current_date.month, current_date.day
        midmonth = calc_midmonth(year)

        print(f"processing year {year} month {month:02d} day {day:02d}")

        ferapl = nc.Dataset(f"{ERA5_dir}/{current_date.strftime(ERA5_pl_pattern)}", "r")
        ferasfc = nc.Dataset(f"{ERA5_dir}/{current_date.strftime(ERA5_sfc_pattern)}", "r")

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
                if np.all(np.diff(ferapl.variables["level"][:]) > 0):
                    var_era = ferapl.variables[VARS3D_CODES[var]][nt, ::-1, :, :]
                else:
                    var_era = ferapl.variables[VARS3D_CODES[var]][nt, :, :, :]

                if var == "zg":
                    var_era = var_era / 9.81

                if np.argmin(np.abs(tdelta)) == 0:
                    var_anom = anom_cache_3d[var][i1, ::-1, :, :]
                else:
                    var_anom_1 = anom_cache_3d[var][i1, ::-1, :, :]
                    var_anom_2 = anom_cache_3d[var][i2, ::-1, :, :]
                    var_anom = (
                        var_anom_1 + (var_anom_2 - var_anom_1) * tdelta_before / tdelta_mid_month
                    )

                temp = var_era + np.nan_to_num(_anom_sign * var_anom)
                if var == "hur":
                    temp = np.clip(temp, 0, 100)
                vout[var] = temp

            for var in vars2d:
                if var not in VARS2D_CODES and var != "hurs":
                    print(f"  WARNING: {var} has no ERA5 surface mapping — skipping")
                    continue
                if var == "hurs":
                    dew_era = ferasfc.variables[VARS2D_CODES["dew"]][nt, :, :] - const.tkelvin
                    tas_era = ferasfc.variables[VARS2D_CODES["tas"]][nt, :, :] - const.tkelvin
                    var_era = calc_relhum(dew_era, tas_era)
                elif var == "siconc":
                    # ERA5 siconc is fraction (0-1); CMIP6 anomaly is in % (0-100)
                    var_era = ferasfc.variables[VARS2D_CODES[var]][nt, :, :] * 100.0
                else:
                    var_era = ferasfc.variables[VARS2D_CODES[var]][nt, :, :]

                if np.min(np.abs(tdelta)) == 0:
                    var_anom = anom_cache_2d[var][i1, :, :]
                else:
                    var_anom_1 = anom_cache_2d[var][i1, :, :]
                    var_anom_2 = anom_cache_2d[var][i2, :, :]
                    var_anom = (
                        var_anom_1 + (var_anom_2 - var_anom_1) * tdelta_before / tdelta_mid_month
                    )

                result = np.array(var_era, dtype="float64") + np.nan_to_num(_anom_sign * var_anom)

                if var == "siconc":
                    result = np.clip(result, 0.0, 100.0)
                elif var == "tos":
                    # ERA5 sst is masked over land; restore those cells to avoid fill-value
                    # artefacts at the Antarctic coastline when stripped by np.float32()
                    if isinstance(var_era, np.ma.MaskedArray):
                        land = np.ma.getmaskarray(var_era)
                        if land.any():
                            result[land] = var_era.data[land]

                vout[var] = result

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

            # --- ERA5-only fields (no PGW anomaly): soil, terrain, land mask ---
            def _read_invar(era5_name: str, fallback: float) -> np.ndarray:
                if era5_name in ferasfc.variables:
                    raw = ferasfc.variables[era5_name]
                    data = raw[nt, :, :] if raw.ndim == 3 else raw[:, :]
                    return np.array(data, dtype="float32")
                return np.full((nlat, nlon), fallback, dtype="float32")

            stl1 = _read_invar("stl1", 273.15)
            stl2 = _read_invar("stl2", 273.15)
            stl3 = _read_invar("stl3", 273.15)
            stl4 = _read_invar("stl4", 273.15)
            swvl1 = _read_invar("swvl1", 0.0)
            swvl2 = _read_invar("swvl2", 0.0)
            swvl3 = _read_invar("swvl3", 0.0)
            swvl4 = _read_invar("swvl4", 0.0)
            soilhgt = _read_invar("z", 0.0) / 9.81  # geopotential → height (m)
            landsea = _read_invar("lsm", 0.0)

            fields3d = np.ndarray(shape=(nfields3d, len(PLVS), nlat, nlon), dtype="float32")
            fields2d = np.ndarray(shape=(_N2D, nlat, nlon), dtype="float32")

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
            fields2d[9] = np.float32(vout["tos"])
            fields2d[10] = np.float32(vout["siconc"] / 100.0)  # fraction (0-1) for WRF
            fields2d[11] = stl1
            fields2d[12] = stl2
            fields2d[13] = stl3
            fields2d[14] = stl4
            fields2d[15] = swvl1
            fields2d[16] = swvl2
            fields2d[17] = swvl3
            fields2d[18] = swvl4
            fields2d[19] = soilhgt
            fields2d[20] = landsea

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

        current_date += dt.timedelta(days=1)
