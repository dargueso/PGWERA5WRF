#!/usr/bin/env python
import datetime as dt
from dateutil.relativedelta import relativedelta
import cdsapi
import calendar

c = cdsapi.Client()


def retrieve_era5():
    """
    A function to demonstrate how to iterate efficiently over several years and months etc
    for a particular era5 request.
    Change the variables below to adapt the iteration to your needs.
    You can use the variable 'target' to organise the requested data in files as you wish.
    In the example below the data are organised in files per day. (eg "era5_daily_20151001.grb")
    """
    yearStart = 1940
    yearEnd = 2022


    y = yearStart


    while y <= yearEnd:

        target = f"era5_monthly_sfc_{y:04d}.nc"
        era5_request(y, target)
        y +=1



def era5_request(year, target):
    """
    An ERA5 request for analysis pressure level data.
    Change the keywords below to adapt it to your needs.
    (eg to add or to remove  levels, parameters, times etc)
    Request cost per day is 112 fields, 14.2326 Mbytes
    """

    c.retrieve(
        "reanalysis-era5-single-levels-monthly-means",
        {
            "product_type": "monthly_averaged_reanalysis",
            "format": "netcdf",
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
            "year": "%s" % (year),
            'month': [
            '01', '02', '03',
            '04', '05', '06',
            '07', '08', '09',
            '10', '11', '12',
            ],
            'time': '00:00',
            "grid": [0.3, 0.3],
        },
        target,
    )


if __name__ == "__main__":
    retrieve_era5()
