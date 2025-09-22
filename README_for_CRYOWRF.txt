Steps to proceed for PGW with PGWERA5WRF:

---------------------------------------------------------
0 INITIAL NOTES -----------------------------------------
---------------------------------------------------------

You have to activate conda environment
conda activate pgw4
If pyhton calls to the pip one, suggest using the direct path: /users/gsergi/miniconda3/bin/python

---------------------------------------------------------
1 DOWNLOAD AND ORGANIZE CMIP6 ---------------------------
---------------------------------------------------------

1a.download_CEMIP6 - download for all the CMIP6 models we want the data for the historical (hist 1985-2014), past (1950-1979) and ssp scenarios (2070-2099)
    - reorganize data with folders: 
        + mkdir 1b.organize_CMIP6
        + find 1a.download_CEMIP6/. -name '*.nc' -exec mv {} 
        
1b.organize_CEMIP6
    - reorganize data with folders:
        + python reorganize_CMIP6_folders.py
    
    - check completeness: 
        + python check_completeness_CMIP6_PGW.py
    
    - create a list of the models to process: 
        + ls -d *>list_CMIP6.txt


---------------------------------------------------------
2 DOWNLOAD AND ERA5 and SEA ICE -------------------------
---------------------------------------------------------

2a.download_ERA5_20221212
    - execute cds_surface_era5.ipynb 
    
    - execute cds_sigma_era5.ipynb

2b.download_SeaIce- download Sea Ice with Michael script


---------------------------------------------------------
3 GENERATE PGW INPUT DATA -------------------------------
---------------------------------------------------------
    
3.PGWERA5WRF   
    - change ERA5 gribs to netcdf:
        + ml cray cpeGNU CDO
        + [Modify grib2netcdf.py]
        + python grib2netcdf.py
    
    - regrid 
        + cdo griddes ../2a.download_ERA5/DATA_AP_202214/ap_surface_2022-12-10_00.nc > era5_grid
        
        + python Calculate_CMIP6_Annual_cycle-CC_change-regrid_ERA5.py -i ../1b.organize_CEMIP6/ --o ../1c.extract_regrid_deltas_CMIP6/AP_20221212_s585/ -f ssp585 -p historical -fy 2070,2099 -py 1985,2014 -v "hurs,tas,ps,ts,vas,uas,psl,ta,hur,ua,va,zg,tos,siconc"
        
        + python Create_CMIP6_AnnualCycleChange_ENSMEAN.py -i ../1c.extract_regrid_deltas_CMIP6/AP_20221212_ssp585-hist/regrid_ERA5 -cp ../1c.extract_regrid_deltas_CMIP6/AP_20221212_ssp585-hist/corrected_plevs/ -o ../1d.delta_ensembles/AP_20221212_ssp585-hist/ -s ssp585-hist -d 2070-2099_1985-2014 -v "hurs,tas,ps,ts,vas,uas,psl,ta,hur,ua,va,zg,tos,siconc"
        
        + copy era5_plev.nc file into the ERA5 file folder
        
        + python Interpolate_CMIP6_Annual_cycle-CC_pinterp.py -i ../1d.delta_ensembles/AP_20221212_ssp585-hist/ -e ../2a.download_ERA5/DATA_AP_202212/ -s ssp585-hist -d 2070-2099_1985-2014
    
    - Create intermediate files with ERA5 and CC signal
        +  f2py -c -m outputInter outputInter.f90 -DF2PY_REPORT_ON_ARRAY_COPY=1000000
    
        + mv
 outputInter.cpython-39-x86_64-linux-gnu.so outputInter.so
 
        + python write_intermediate_ERA5_CMIP6anom.py (modify file first)
    

	+ python write_intermediate_ERA5_CMIP6anom_CRYOWRF.py -i /capstor/store/cscs/userlab/s1308/gsergi/PGW_Simulations/1d.delta_ensembles/PAMIR_SEAS_2022_ssp585-hist/ -e /capstor/store/cscs/userlab/s1308/gsergi/PGW_Simulations/2a.download_ERA5/DATA_PAMIR_SEAS_2022/ -o /capstor/store/cscs/userlab/s1308/gsergi/PGW_Simulations/3b.Intermediate_WRF_files/PAMIR_SEAS_2022_ssp585-hist -s ssp585-hist -d 2070-2099_1985-2014 -di 2021-09-20T00 -de 2022-07-31T00 -ds 6 -df %Y-%m-%d_%H -fr pamir_surface_2021-09-20_00.nc
