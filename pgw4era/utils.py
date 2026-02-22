"""pgw4era.utils — shared helper functions used across WRF and CRYOWRF pipelines."""

from __future__ import annotations

import datetime as dt
import os

import numpy as np

from pgw4era.constants import const


def checkfile(file_out: str, overwrite: bool | str) -> bool:
    """Check if an output file exists and whether it should be written.

    Parameters
    ----------
    file_out:
        Path to the output file.
    overwrite:
        If ``True`` (or the string ``"True"``), overwrite existing files.

    Returns
    -------
    bool
        ``True`` if the file should be written, ``False`` otherwise.
    """
    if overwrite == "False":
        overwrite = False

    fileexist = os.path.exists(file_out)
    filewrite = False

    print("  --> OUTPUT FILE:")
    print("         ", file_out)
    if fileexist:
        if not overwrite:
            print("          +++ FILE ALREADY EXISTS +++")
            filewrite = False
        else:
            print("           +++ FILE EXISTS AND WILL BE OVERWRITTEN +++")
            filewrite = True
    else:
        print("         +++ FILE DOES NOT EXISTS YET +++")
        filewrite = True

    return filewrite


def calc_midmonth(year: int) -> list[dt.datetime]:
    """Return mid-month datetimes for *year* plus the boundary months.

    Returns a list of 14 datetimes:
    - [0]    mid-December of *year* - 1
    - [1..12] mid-month of each month in *year*
    - [13]   mid-January of *year* + 1

    Parameters
    ----------
    year:
        The year for which to compute mid-month dates.
    """
    midm_date = []

    for month in range(1, 13):
        minit = dt.datetime(year, month, 1, 0)
        if month == 12:
            mend = dt.datetime(year + 1, 1, 1, 1)
        else:
            mend = dt.datetime(year, month + 1, 1, 1)
        tdifference = (mend - minit).total_seconds() / 2
        midm_date.append(minit + dt.timedelta(seconds=tdifference))

    # Prepend mid-December of previous year
    tdifference = (dt.datetime(year, 1, 1, 1) - dt.datetime(year - 1, 12, 1, 1)).total_seconds() / 2
    midm_date = [dt.datetime(year - 1, 12, 1, 1) + dt.timedelta(seconds=tdifference)] + midm_date

    # Append mid-January of next year
    tdifference = (
        dt.datetime(year + 1, 2, 1, 1) - dt.datetime(year + 1, 1, 1, 1)
    ).total_seconds() / 2
    midm_date.append(dt.datetime(year + 1, 1, 1, 1) + dt.timedelta(seconds=tdifference))

    return midm_date


def calc_relhum(dewpt: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Calculate relative humidity from dew-point and air temperature.

    Both *dewpt* and *t* must be in degrees Celsius.

    Parameters
    ----------
    dewpt:
        Dew-point temperature in °C.
    t:
        Air temperature in °C.

    Returns
    -------
    numpy.ndarray
        Relative humidity in percent (0–100).
    """
    relhum = 100.0 * (
        np.exp((const.es_Abolton * dewpt) / (const.es_Bbolton + dewpt))
        / np.exp((const.es_Abolton * t) / (const.es_Bbolton + t))
    )
    return relhum
