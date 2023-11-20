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
    yearEnd = 2023


    y = yearStart


    while y <= yearEnd:

        target = f"era5_monthly_pl_{y:04d}.nc" 
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
        "reanalysis-era5-pressure-levels-monthly-means",
        {
            "product_type": "monthly_averaged_reanalysis",
            "format": "netcdf",
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
