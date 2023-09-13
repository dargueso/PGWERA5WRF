# PGWERA5WRF
Software to modify ERA5 files and add a large-scale climate change signal from CMIP6 ensemble. 
Create boundary conditions from ERA5+PGW for WRF.

# Instructions

## Download and prepare CMIP6 data

1. Data can be downloaded from [ESGF](https://esgf-node.llnl.gov/projects/esgf-llnl/), where login is required. The best option is to use Globus - the use of wget scripts is not very straight forward. You need to impose a series of conditions to get the monthly data that is required by WRF. First it must have both historical and ssp585 (or the desired scenario), then select monthly data, and finally the variables required (hur, hurs, ps, psl, ta, tas, tos, ts, ua, uas, va, vas, zg). You can also select the variant label. Check [CMIP6 Models](#cmip6-models) for a complete list of models that were downloaded. 


2. Once the data is downloaded, it must be organized into folders. We initially organized them into two folders: historical and ssp585. Within those two folders, they are organized into directories with the name pattern as follows: GCMname_variantlabel (ej: ACCESS-CM2_r1i1p1f1). All variables files are inside as downloaded from ESGF. An example on how to organize files this way is provided here: [reorganize_CMIP6_folders.py](reorganize_CMIP6_folders.py)

3. Check that all models has a complete set of data ready for PGW processing using `check_completeness_CMIP6_PGW.py`

4. Create a list of the models to process. For example within historical: `ls -d *>list_CMIP6.txt`


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