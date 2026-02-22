#!/usr/bin/env python
"""pgw4era.wrf.write_intermediate

Write WRF intermediate-format boundary condition files from ERA5 data with
CMIP6 climate-change anomalies applied (Pseudo-Global Warming approach).

The Fortran I/O extension ``outputInter`` (``outputInter.f90`` compiled with
f2py) must be importable.  It is expected to live next to this file; add the
``pgw4era/wrf`` directory to ``PYTHONPATH`` or compile via::

    cd pgw4era/wrf
    f2py -c outputInter.f90 -m outputInter

Authors: Daniel Argüeso, Alejandro Di Luca
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from types import SimpleNamespace

import netCDF4 as nc
import numpy as np

from pgw4era.constants import const
from pgw4era.utils import calc_midmonth, calc_relhum, checkfile

# ---------------------------------------------------------------------------
# Load the compiled Fortran extension from the same directory as this file
# ---------------------------------------------------------------------------
_WRF_DIR = Path(__file__).parent
if str(_WRF_DIR) not in sys.path:
    sys.path.insert(0, str(_WRF_DIR))

try:
    import outputInter as f90  # type: ignore[import]
except ImportError as exc:
    raise ImportError(
        "Could not import 'outputInter'. "
        "Compile it with:\n"
        f"  cd {_WRF_DIR}\n"
        "  f2py -c outputInter.f90 -m outputInter"
    ) from exc

# ---------------------------------------------------------------------------
# Variable mappings
# ---------------------------------------------------------------------------
VARS3D_CODES: dict[str, str] = {"hur": "r", "ta": "t", "ua": "u", "va": "v", "zg": "z"}
VARS2D_CODES: dict[str, str] = {
    "dew": "d2m",
    "tas": "t2m",
    "uas": "u10",
    "vas": "v10",
    "ps": "sp",
    "psl": "msl",
    "ts": "skt",
}
VAR_UNITS_ERA5: dict[str, str] = {
    "z": "m2 s-2",
    "t": "K",
    "u": "m s-1",
    "v": "m s-1",
    "sp": "Pa",
    "msl": "Pa",
    "ts": "K",
    "r": "1",
    "u10": "m s-1",
    "v10": "m s-1",
    "t2m": "K",
    "d2m": "K",
    "lsm": "0/1 Flag",
    "skt": "K",
}

PLVS: list[float] = [
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
    1000.00,
    700.00,
    500.00,
    300.00,
    200.00,
    100.00,
]


# ---------------------------------------------------------------------------
# Main processing function
# ---------------------------------------------------------------------------


def run(cfg: SimpleNamespace, overwrite_file: bool = False, create_figs: bool = False) -> None:
    """Process ERA5 + CMIP6 anomaly data and write WRF intermediate files.

    Parameters
    ----------
    cfg:
        Configuration namespace returned by :func:`pgw4era.config.load_config`.
    overwrite_file:
        If ``True``, overwrite existing output files.
    create_figs:
        If ``True``, save diagnostic PNG figures.
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
    nfields2d = len(vars2d)

    CMIP6anom_dir = cfg.CMIP6anom_dir
    ERA5_dir = cfg.ERA5netcdf_dir

    # Reference grid from ERA5 surface file
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
        print("Looping over timesteps in original ERA5 file")

        for nt in range(date1, date2 + 1):
            proc_date = nc.num2date(time_filepl[nt], units=time_filepl.units, calendar="standard")
            print("processing 3Dvar time: ", proc_date)
            filedate = proc_date.strftime("%Y-%m-%d_%H-%M-%S")

            file_out = "ERA5:" + filedate.split("_")[0] + "_" + filedate.split("_")[1].split("-")[0]
            filewrite = checkfile(file_out, overwrite_file)
            if filewrite:
                tdelta = np.asarray(
                    [(midmonth[i] - proc_date).total_seconds() for i in range(len(midmonth))]
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
                    print(f"Processing variable {var}")
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
                        VAR_UNITS_ERA5[VARS3D_CODES[var]] = "m"

                    if np.argmin(np.abs(tdelta)) == 0:
                        var_anom = fanom.variables[var][i1, ::-1, :, :]
                    else:
                        var_anom_1 = fanom.variables[var][i1, ::-1, :, :]
                        var_anom_2 = fanom.variables[var][i2, ::-1, :, :]
                        var_anom = (
                            var_anom_1
                            + (var_anom_2 - var_anom_1) * tdelta_before / tdelta_mid_month
                        )

                    temp = var_era + np.nan_to_num(var_anom)
                    if var == "hur":
                        temp = np.clip(temp, 0, 100)
                    vout[var] = temp
                    fanom.close()

                for var in vars2d:
                    print(f"Processing variable {var}")
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
                            var_anom_1
                            + (var_anom_2 - var_anom_1) * tdelta_before / tdelta_mid_month
                        )

                    vout[var] = var_era + np.nan_to_num(var_anom)
                    fanom.close()

                # --- Write WRF intermediate format ---
                filedate = proc_date.strftime("%Y-%m-%d_%H-%M-%S")

                fields3d = np.ndarray(shape=(nfields3d, len(PLVS), nlat, nlon), dtype="float32")
                fields2d = np.ndarray(shape=(nfields2d, nlat, nlon), dtype="float32")

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
