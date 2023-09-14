#!/usr/bin/env python
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
    yearStart = 2010
    yearEnd = 2010
    monthStart =1
    monthEnd = 12

    for year in list(range(yearStart, yearEnd + 1)):
        for month in list(range(monthStart, monthEnd + 1)):
            for day in list(range(1, calendar.monthrange(year, month)[1] + 1)):
            #for day in list(range(1,)):
                startDate = '%04d%02d%02d' % (year, month, day)
                #numberOfDays = calendar.monthrange(year, month)[1]
                lastDate = '%04d%02d%02d' % (year, month, day)#numberOfDays)
                target = "era5_daily_sfc_%04d%02d%02d.grb" % (year, month, day)
                #requestDates = (startDate + "/TO/" + lastDate)

                era5_request(year,month,day,target)

def era5_request(year,month,day,target):
    """
        An ERA5 request for analysis pressure level data.
        Change the keywords below to adapt it to your needs.
        (eg to add or to remove  levels, parameters, times etc)
        Request cost per day is 112 fields, 14.2326 Mbytes
    """

    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type':'reanalysis',
            'format':'grib',
            'variable':[
                '10m_u_component_of_wind','10m_v_component_of_wind','2m_dewpoint_temperature',
                '2m_temperature','land_sea_mask','mean_sea_level_pressure',
                'sea_ice_cover','sea_surface_temperature','skin_temperature',
                'snow_depth','soil_temperature_level_1','soil_temperature_level_2',
                'soil_temperature_level_3','soil_temperature_level_4','surface_pressure',
                'volumetric_soil_water_layer_1','volumetric_soil_water_layer_2','volumetric_soil_water_layer_3',
                'volumetric_soil_water_layer_4'
            ],
            'year':'%s' %(year),
            'month':'%02d' %(month),
            'day':'%02d' %(day),
            'time':['00:00','06:00','12:00','18:00'],
            'grid'          : [0.3, 0.3]
        },
        target)

if __name__ == '__main__':
    retrieve_era5()
