#!/usr/bin/env python
"""Get_ERA5_ECMWF_sfc.py — Download ERA5 single-level (surface) data via CDS API.

Edit the year/month/day ranges inside this script to match your target period.
"""

import calendar

import cdsapi

c = cdsapi.Client()


def retrieve_era5():
    """Iterate over days and download ERA5 surface data."""
    yearStart = 2010
    yearEnd = 2010
    monthStart = 1
    monthEnd = 12

    for year in range(yearStart, yearEnd + 1):
        for month in range(monthStart, monthEnd + 1):
            for day in range(1, calendar.monthrange(year, month)[1] + 1):
                target = f"era5_daily_sfc_{year:04d}{month:02d}{day:02d}.grb"
                era5_request(year, month, day, target)


def era5_request(year, month, day, target):
    c.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            "format": "grib",
            "variable": [
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
                "2m_dewpoint_temperature",
                "2m_temperature",
                "land_sea_mask",
                "mean_sea_level_pressure",
                "sea_ice_cover",
                "sea_surface_temperature",
                "skin_temperature",
                "snow_depth",
                "soil_temperature_level_1",
                "soil_temperature_level_2",
                "soil_temperature_level_3",
                "soil_temperature_level_4",
                "surface_pressure",
                "volumetric_soil_water_layer_1",
                "volumetric_soil_water_layer_2",
                "volumetric_soil_water_layer_3",
                "volumetric_soil_water_layer_4",
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
