#!/usr/bin/env python
"""Get_ERA5_ECMWF_plevs.py — Download ERA5 pressure-level data via CDS API.

Edit the year/month/day ranges inside this script to match your target period.
"""

import datetime as dt

import cdsapi

c = cdsapi.Client()


def retrieve_era5():
    """Iterate over days and download ERA5 pressure-level data."""
    yearStart = 2010
    yearEnd = 2010
    monthStart = 7
    monthEnd = 12

    y, m, d = yearStart, monthStart, 1

    while y < yearEnd or (y == yearEnd and m <= monthEnd):
        target = f"era5_daily_pl_{y:04d}{m:02d}{d:02d}.grb"
        era5_request(y, m, d, target)

        edate = dt.datetime(y, m, d) + dt.timedelta(days=1)
        y, m, d = edate.year, edate.month, edate.day


def era5_request(year, month, day, target):
    c.retrieve(
        "reanalysis-era5-pressure-levels",
        {
            "product_type": "reanalysis",
            "format": "grib",
            "variable": [
                "geopotential",
                "temperature",
                "u_component_of_wind",
                "relative_humidity",
                "v_component_of_wind",
            ],
            "pressure_level": [
                "1",
                "2",
                "3",
                "5",
                "7",
                "10",
                "20",
                "30",
                "50",
                "70",
                "100",
                "125",
                "150",
                "175",
                "200",
                "225",
                "250",
                "300",
                "350",
                "400",
                "450",
                "500",
                "550",
                "600",
                "650",
                "700",
                "750",
                "775",
                "800",
                "825",
                "850",
                "875",
                "900",
                "925",
                "950",
                "975",
                "1000",
            ],
            "year": f"{year}",
            "month": f"{month:02d}",
            "day": f"{day:02d}",
            "time": ["00:00", "06:00", "12:00", "18:00"],
            "grid": [0.3, 0.3],
        },
        target,
    )


if __name__ == "__main__":
    retrieve_era5()
