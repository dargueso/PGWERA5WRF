#File with configuration parameters for the pgw4era package

# Path to the directory where the ERA5 data is stored

ERA5netcdf_dir = "/home/dargueso/BDY_DATA/ERA5/ERA5_netcdf/BALEARS_1km_CC/"
ERA5_pl_ref_file = "./era5_plev.nc" 
CMIP6_monthly_dir = "/home/dargueso/BDY_DATA/CMIP6/"
CMIP6anom_dir = "./" #/home/dargueso/BDY_DATA/CMIP6anom/"

experiments = ["historical", "ssp585"]
periods = [[2004,2023],[2031,2050]]
variables_all = ["hurs","tas","ps","ts","vas","uas","psl","ta","hur","ua","va","zg"]
variables_2d = ["hurs","tas","ps","ts","vas","uas","psl"]
variables_3d = ["ta", "ua", "va", "zg", "hur"] 
models = None