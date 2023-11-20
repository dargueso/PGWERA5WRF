# ERA5 Counterfactual

Software to modify ERA5 files and create a counterfactual
Create boundary conditions from ERA5 and the climate change signal from 1940-1959 to 2000-2019

# Instructions

## Download ERA5


1. Download ERA5 data using [Get_ERA5_ECMWF_plevs.py](Get_ERA5_ECMWF_plevs.py) and [Get_ERA5_ECMWF_sfc.py](Get_ERA5_ECMWF_sfc.py) scripts (you need to install and set up the cdsapi: https://cds.climate.copernicus.eu/api-how-to)

2. Convert original ERA5 in GRIB into NetCDF. Use [grib2netcdf.py](grib2netcdf.py). Depending on the cdo version, the outputs may change (variable names, order of pressure levels). This can be adapted later on when merging ERA5 and CMIP6 data.

## Download monthly ERA5

1. Download ERA5 monthly data using [Get_ERA5_ECMWF_plevs_monthly_counterfactual.py](Get_ERA5_ECMWF_plevs_monthly_counterfactual.py) and [Get_ERA5_ECMWF_sfc_monthly_counterfactual.py](Get_ERA5_ECMWF_sfc_monthly_counterfactual.py), which downloads monthly data for pressure levels and surface variables.

2. Calculate the recent climate change signal to subtract it from ERA5 and create the counterfactual.

```
cdo -b F32 ensmean era5_monthly_sfc_19[4-5]?.nc era5_monthly_sfc_1940-1959.nc
cdo -b F32 ensmean era5_monthly_sfc_20[0-1]?.nc era5_monthly_sfc_2000-2019.nc

cdo -b F32 ensmean era5_monthly_pl_19[4-5]?.nc era5_monthly_pl_1940-1959.nc
cdo -b F32 ensmean era5_monthly_pl_20[0-1]?.nc era5_monthly_pl_2000-2019.nc

cdo sub era5_monthly_sfc_2000-2019.nc era5_monthly_sfc_1940-1959.nc era5_monthly_sfc_2000-2019_1940-1959.nc
cdo sub era5_monthly_pl_2000-2019.nc era5_monthly_pl_1940-1959.nc era5_monthly_pl_2000-2019_1940-1959.nc
```

## Create WRF-Intermediate files merging ERA5 and the monthly data

Using [pywinter](https://pywinter.readthedocs.io/en/latest/#) and [Create_WRF-Intermediate-from-nc.py](Create_WRF-Intermediate-from-nc.py)


An example is provided for Storm Daniel (02 to 12 September 2023):


```
python Create_WRF-Intermediate-from-nc.py -s 2023 -e 2023
```

Once the WRF-intermediate files are generated, use just like with ERA5 (no additional modifications required. except those for ERA5), starting from metgrid.exe

# Authors

* [Daniel Argueso](https://github.com/dargueso): Universitat de les Illes Balears