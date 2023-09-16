# PGWERA5WRF
Software to modify ERA5 files and add a large-scale climate change signal from CMIP6 ensemble. 
Create boundary conditions from ERA5+PGW for WRF.

This is for the EPICC experiments, where soil variables are taken directly from ERA5 to initialize the model (no climatology is used)

# Instructions

## Download ERA5

1. Download ERA5 data using [Get_ERA5_ECMWF_plevs.py](Get_ERA5_ECMWF_plevs.py) and [Get_ERA5_ECMWF_sfc.py](Get_ERA5_ECMWF_sfc.py) scripts (you need to install and set up the cdsapi: https://cds.climate.copernicus.eu/api-how-to)
   
2. Convert original ERA5 in GRIB into NetCDF. Use [grib2netcdf.py](grib2netcdf.py). Depending on the cdo version, the outputs may change (variable names, order of pressure levels). This can be adapted later on when merging ERA5 and CMIP6 data.

## Download and organize CMIP6 data

In this section, we download available CMIP6 data at monthly frequency for the periods and the scenarios requested. We also organize the files into folders and check that all the variables are available for all models and over the period requested.

1. Data can be downloaded from [ESGF](https://esgf-node.llnl.gov/projects/esgf-llnl/), where login is required. The best option is to use Globus - the use of wget scripts is not very straight forward. You need to impose a series of conditions to get the monthly data that is required by WRF. First it must have both historical and ssp585 (or the desired scenario), then select monthly data, and finally the variables required (hus, hurs, ps, psl, ta, tas, tos, ts, ua, uas, va, vas, zg). You can also select the variant label. Check [CMIP6 Models](#cmip6-models) for a complete list of models that were downloaded. 

 - Only monthly means are needed ("Amon")
  - Required var:
    * 3D: ta, ua, va, zg, hur
    * 2D: uas, vas, tas, ts, hurs,ps, psl


2. Once the data is downloaded, it must be organized into folders. We initially organized them into two folders: historical and ssp585. Within those two folders, they are organized into directories for each variable. Finally, the files are distributed in folders for each model (ej: $WORKDIR/historical/va/ACCESS-CM2). All variables files are inside as downloaded from ESGF. An example on how to organize files this way is provided here: [reorganize_CMIP6_folders.py](reorganize_CMIP6_folders.py)

3. Check that all models has a complete set of data ready for PGW processing using [check_completeness_CMIP6_PGW.py](check_completeness_CMIP6_PGW.py)

4. Create a list of the models to process. For example within historical and any of the variable folders: `ls -d *>list_CMIP6.txt`

## Create monthly annual cycles and CC from CMIP6 models, interpolate to ERA5 grid and to pressure levels.

In this section, we calculate means for every calendar months to create files with an "annual cycle" (also called "seasonal cycles"). Then we will make the difference between future and present files for the requested periods to calculate the climate change signal (delta) for every GCM, variable and calendar month. We will create the corresponding netCDF files (one for each GCM and variable). Finally, we will interpolate these netCDF files from the original GCM grid to a common ERA5 grid ([era5_grid](era5_grid)) and to ERA5 pressure levels so that they can be merged together and added to ERA5.

Note: the common ERA5 grid is created from a sample era5 file using:

        cdo griddes era5_daily_sfc_20171130.nc > era5_grid

1. Calculate the annual cycles, calculate the climate change signal (deltas) and interpolate to era5 grid for each model and varaible using [Calculate_CMIP6_Annual_cycle-CC_change-regrid_ERA5.py](Calculate_CMIP6_Annual_cycle-CC_change-regrid_ERA5.py). This script may be edited to select the periods and the scenarios to be processed. It also let you select the models to be processed or use the list_CMIP.txt created above (default). It also takes input and output directories as arguments. Finally you can process one variable at a time by specifying it as an argument. 

Note: Some GCMs provide data up to year 2300 or 2400, which create some problems. We have removed those years and process only until 2100.

2. Then, we create the definitive netCDF files with the climate change signal using [Create_CMIP6_AnnualCycleChange_ENSMEAN.py](Create_CMIP6_AnnualCycleChange_ENSMEAN.py)

or manually with cdo:

        cdo ensmean ts_* ts_CC_signal_ssp585_2076-2100_1990-2014.nc

3. Finally, interpolate the ensemble means to ERA5 pressure levels using [Interpolate_CMIP6_Annual_cycle-CC_pinterp.py](Interpolate_CMIP6_Annual_cycle-CC_pinterp.py)

This script needs a sample ERA5 netcdf data to get the plevs. We created it from a grib file downloaded from ECMWF (see [Download ERA5](#download-era5)) and converted to netCDF using [grib2netcdf.py](grib2netcdf.py), from which the pressure levels are then extracted using:

        ncks -v plev era5_daily_pl_20120101.nc era5_plev.nc

The resulting file is provided here [era5_plev.nc](era5_plev.nc)

## Merge ERA5 and CMIP5 anomalies into single WRF-intermediate files

In this section we combine ERA5 data and the CMIP6 Climate Change Signal to create the PGW WRF-intermediate files. We use a fortran routine from Python to write the FORTRAN WRF-intermediate files.  

1. We need to convert the Fortran routine [outputInter.f90](outputInter.f90) to a Python module using f2py:

        f2py -c -m outputInter outputInter.f90 -DF2PY_REPORT_ON_ARRAY_COPY=1000000
2. Rename mv outputInter.[cpython-37m-x86_64-linux-gnu].so to outputInter.so

3. Run [write_intermediate_ERA5_CMIP6anom.py](write_intermediate_ERA5_CMIP6anom.py) which makes use of [outputInter.f90](outputInter.f90) (as a python module), [constanst.py](constanst.py). It basically interpolates CMIP6 anomalies to every 3 or 6 hours (from monthly) and builds the WRF-Intermediate adding CMIP6 anomalies to ERA5 fields (ERA5 netcdf files are needed - see [Download ERA5](#download-era5) to see how to create them). Depending on CDO version variables in the ERA5 netCDF files may have names or codes, modify the vars2d_codes and vars3d_codes accordingly. Currently working with names.

## Create soil variables

Create a file with soil variables to initalize. Most GCMs do not write out soil variables. We create a sample intermediate file for each simulation with the state of the soil using:

        python myrunWPSandreal_UIB_daily_EPICC_2km_ERA5_CMIP6anom_SOILERA.py 

which relies on [namelist_wps_EPICC_2km_ERA5_CMIP6anom_SOILERA.deck](namelist_wps_EPICC_2km_ERA5_CMIP6anom_SOILERA.deck).
This creates only a snapshot of soil variables at the starting date.

# CMIP6 Models

| Global Model     | Downloaded | Completeness | Scenarios          | Exp (realization) |
| ---------------- | ---------- | ------------ | ------------------ | ----------------- |
| ACCESS-CM2       | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| ACCESS-ESM1-5    | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| CanESM5          | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| CMCC-CM2-SR5     | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| CMCC-ESM2        | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| CNRM-CM6-1       | Downloaded | Complete     | historical, ssp585 | r1i1p1f2          |
| CNRM-CM6-1-HR    | Downloaded | Complete     | historical, ssp585 | r1i1p1f2          |
| CNRM-ESM2-1      | Downloaded | Complete     | historical, ssp585 | r1i1p1f2          |
| EC-Earth3        | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| EC-Earth3-CC     | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| EC-Earth3-Veg    | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| EC-Earth3-Veg-LR | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| FGOALS-f3-L      | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| GFDL-ESM4        | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| GISS-E2-1-G      | Downloaded | Complete     | historical, ssp585 | r1i1p1f2          |
| GISS-E2-1-H      | Downloaded | Complete     | historical, ssp585 | r1i1p1f2          |
| HadGEM3-GC31-LL  | Downloaded | Complete     | historical, ssp585 | r1i1p1f3          |
| HadGEM3-GC31-MM  | Downloaded | Complete     | historical, ssp585 | r1i1p1f3          |
| INM-CM4-8        | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| INM-CM5-0        | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| IPSL-CM6A-LR     | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| KACE-1-0-G       | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| KIOST-ESM        | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| MCM-UA-1-0       | Downloaded | Complete     | historical, ssp585 | r1i1p1f2          |
| MIROC-ES2L       | Downloaded | Complete     | historical, ssp585 | r1i1p1f2          |
| MIROC6           | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| MPI-ESM1-2-HR    | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| MPI-ESM1-2-LR    | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| MRI-ESM2-0       | Downloaded | Complete     | historical, ssp585 | r1i1p1f1          |
| UKESM1-0-LL      | Downloaded | Complete     | historical, ssp585 | r1i1p1f2          |

# Authors

* [Daniel Argueso](https://github.com/dargueso): Universitat de les Illes Balears