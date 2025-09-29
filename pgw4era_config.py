#File with configuration parameters for the pgw4era package

# Path to the directories where the data is stored

ERA5netcdf_dir = "/home/dargueso/BDY_DATA/ERA5/ERA5_netcdf/"
ERA5_sfc_ref_file = "era5_daily_sfc_20090601.nc"
ERA5_pl_ref_file = "./era5_plev.nc" 
CMIP6_monthly_dir = "/home/dargueso/BDY_DATA/CMIP6/"
CMIP6anom_dir = "/home/dargueso/BDY_DATA/CMIP6/" #/home/dargueso/BDY_DATA/CMIP6anom/"
figs_path = "/home/dargueso/BDY_DATA/CMIP6/Figs"

# Years for which the boundary conditions will be generated
syear = 2009
eyear = 2009
smonth = 6
emonth = 7

# Configuration parameters for the CMIP6 data processing
experiments = ["historical", "ssp585"] #Experiments to create the PGW climate change signal
periods = [[2004,2023],[2031,2050]] #Periods for the historical and future experiments to calculate the climate change signal
variables_all = ["hurs","tas","ps","ts","vas","uas","psl","ta","hur","ua","va","zg"] #Variables to be processed (ALL)
variables_2d = ["hurs","tas","ps","ts","vas","uas","psl"] #Variables to be processed (2D)
variables_3d = ["ta", "ua", "va", "zg", "hur"] #Variables to be processed (3D)
models = None