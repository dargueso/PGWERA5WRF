# PGWERA5WRF
[![DOI](https://zenodo.org/badge/691022503.svg)](https://zenodo.org/badge/latestdoi/691022503)

Software to modify ERA5 files and add a large-scale climate change signal from CMIP6 ensemble to create WRF/CRYOWRF boundary conditions using the Pseudo-Global Warming (PGW) approach.

## Installation

Clone the repository and install the `pgw4era` package in editable mode (requires Python 3.10+):

```bash
git clone https://github.com/dargueso/PGWERA5WRF.git
cd PGWERA5WRF
pip install -e ".[dev]"
```

This installs all runtime dependencies (`netCDF4`, `xarray`, `numpy`, `scipy`, `matplotlib`, `cartopy`, `cdsapi`) and development tools (`ruff`, `pytest`).

## Configuration

Copy the example configuration file and adapt it to your experiment:

```bash
cp pgw4era.toml my_experiment.toml
```

Edit `my_experiment.toml` and adjust the following settings under the `[wrf]` or `[cryowrf]` profile:

| Key | Description |
|-----|-------------|
| `ERA5netcdf_dir` | Directory containing ERA5 NetCDF files |
| `ERA5_sfc_ref_file` | ERA5 surface reference file (for grid info) |
| `ERA5_pl_ref_file` | ERA5 pressure-level reference file |
| `CMIP6_monthly_dir` | Root directory for raw CMIP6 monthly data |
| `CMIP6anom_dir` | Directory for computed CMIP6 anomaly files |
| `figs_path` | Output directory for diagnostic figures |
| `syear` / `eyear` | Start/end year for boundary conditions |
| `smonth` / `emonth` | Start/end month for boundary conditions |
| `experiments` | CMIP6 experiments, e.g. `["historical", "ssp585"]` |
| `periods` | Year ranges for each experiment, e.g. `[[2004, 2023], [2031, 2050]]` |
| `variables_2d` | 2-D CMIP6 variable names to process |
| `variables_3d` | 3-D CMIP6 variable names to process |

To restrict processing to specific CMIP6 models, add:

```toml
models = ["ACCESS-CM2", "MPI-ESM1-2-HR"]
```

Otherwise, model names are read from `list_CMIP6.txt` (default).

### CRYOWRF-specific options

The `[cryowrf]` profile additionally supports:

| Key | Default | Description |
|-----|---------|-------------|
| `one_timestep_files` | `false` | Write one output file per timestep instead of one per day |
| `noahmp` | `false` | Enable NoahMP land-surface fields |

## Fortran Module Compilation

The WRF intermediate file writer is implemented in Fortran and must be compiled with `f2py` before running `scripts/run_pgw.py`.

**WRF profile:**

```bash
cd pgw4era/wrf
f2py -c outputInter.f90 -m outputInter -DF2PY_REPORT_ON_ARRAY_COPY=1000000
```

**CRYOWRF profile:**

```bash
cd pgw4era/cryowrf
f2py -c outputInter_CRYOWRF.f90 -m outputInter_CRYOWRF -DF2PY_REPORT_ON_ARRAY_COPY=1000000
```

On some systems the compiled module will have a version-specific suffix (e.g. `outputInter.cpython-311-x86_64-linux-gnu.so`). Rename it to `outputInter.so` / `outputInter_CRYOWRF.so` if needed.

## Full Workflow

Follow these steps in order to produce PGW WRF/CRYOWRF boundary conditions.

### Step 1 — Download ERA5

1. Install and configure the CDS API: <https://cds.climate.copernicus.eu/api-how-to>

2. Download ERA5 pressure-level and surface data:

   ```bash
   python scripts/Get_ERA5_ECMWF_plevs.py --config my_experiment.toml
   python scripts/Get_ERA5_ECMWF_sfc.py   --config my_experiment.toml
   ```

3. Convert ERA5 GRIB files to NetCDF:

   ```bash
   python scripts/grib2netcdf.py --config my_experiment.toml
   ```

### Step 2 — Download and Prepare CMIP6 Data

1. Download monthly CMIP6 data from [ESGF](https://esgf-node.llnl.gov/projects/esgf-llnl/) (login required). The recommended method is Globus. Required variables:
   - 3-D (`Amon`): `ta`, `ua`, `va`, `zg`, `hur`
   - 2-D (`Amon`): `uas`, `vas`, `tas`, `ts`, `hurs`, `ps`, `psl`

   Only monthly means (`Amon` frequency) are required. Some models provide data beyond 2100; these extra years can cause issues and should be trimmed.

2. Organize downloaded files into the expected folder structure (`<experiment>/<variable>/<model>/`):

   ```bash
   python scripts/reorganize_CMIP6_folders.py --config my_experiment.toml
   ```

3. Verify that all models have a complete set of variables:

   ```bash
   python scripts/check_completeness_CMIP6_PGW.py --config my_experiment.toml
   ```

4. Create a model list file (run inside any variable folder within the `historical` experiment directory):

   ```bash
   ls -d * > list_CMIP6.txt
   ```

### Step 3 — Compute CMIP6 Climate Change Signal

This stage calculates monthly climatologies (annual cycles), computes the climate change delta between future and present periods, regrids to the ERA5 grid, and interpolates to ERA5 pressure levels.

1. Create the ERA5 grid description file (if not already present):

   ```bash
   cdo griddes era5_daily_sfc_YYYYMMDD.nc > era5_grid
   ```

2. Calculate per-model annual cycles, climate change signal, and regrid to ERA5 grid:

   ```bash
   python scripts/Calculate_CMIP6_Annual_cycle-CC_change-regrid_ERA5.py \
       --config my_experiment.toml
   ```

3. Compute the multi-model ensemble mean climate change signal:

   ```bash
   python scripts/Create_CMIP6_AnnualCycleChange_ENSMEAN.py \
       --config my_experiment.toml
   ```

   Alternatively, using CDO directly:

   ```bash
   cdo ensmean ts_* ts_CC_signal_ssp585_2076-2100_1990-2014.nc
   ```

4. Interpolate ensemble means to ERA5 pressure levels:

   ```bash
   python scripts/Interpolate_CMIP6_Annual_cycle-CC_pinterp.py \
       --config my_experiment.toml
   ```

   This step requires a pressure-level reference file. Create it from any ERA5 pressure-level NetCDF:

   ```bash
   ncks -v plev era5_daily_pl_YYYYMMDD.nc era5_plev.nc
   ```

   The resulting `era5_plev.nc` is provided in the repository as a sample.

### Step 4 — Write WRF Intermediate Files

Run the unified entry point, choosing `wrf` or `cryowrf` as the profile:

```bash
# Standard WRF (7 surface fields)
python scripts/run_pgw.py --config my_experiment.toml --profile wrf

# CRYOWRF (same fields + SNOW and SNOWH)
python scripts/run_pgw.py --config my_experiment.toml --profile cryowrf
```

Pass `--overwrite` to regenerate existing output files. The CRYOWRF profile adds two snow fields to each output file:
- `SNOW` — snow water equivalent (kg m⁻²)
- `SNOWH` — physical snow depth (m)

### Step 5 — Create Soil Variables (optional)

WRF with a land-surface model requires soil variable initialization. Create a soil climatology from ERA5 data (example for December):

```bash
cdo ensmean era5_daily_sfc_20??12??.grb soil_clim_dec.grb
```

Then in WPS:

```bash
./link_grib.csh ~/BDY_DATA/ERA5/soil_clim_dec.grb
mv namelist_soilera5_cmip6_pgw.wps namelist.wps
ln -sf Vtable.ERA5.SOIL1ststep Vtable
./ungrib.exe
```

Include the resulting `SOILERA5:YYYY-MM-DD_HH` file as a constant in `namelist.wps`:

```
&metgrid
 constants_name = 'SOILERA5:2005-12-01_00'
```

You may also need the modified METGRID table `METGRID.TBL.ARW_PGW` and the patched `module_initialize_real.F` for correct soil variable handling.

## Output Verification

To verify that the refactored package produces bit-identical results to the original scripts, compare two sets of WRF intermediate output files:

```bash
python scripts/compare_wrf_output.py \
    --ref /path/to/old/output \
    --new /path/to/new/output
```

To compare WRF and CRYOWRF outputs for the same simulation period (the 7 shared fields should be identical; the 2 CRYOWRF-only fields are reported separately):

```bash
python scripts/compare_wrf_cryowrf_output.py \
    --wrf /path/to/wrf/output \
    --cryowrf /path/to/cryowrf/output
```

## Development

Run the linter and test suite:

```bash
ruff check .
ruff format --check .
pytest
```

CI runs automatically on every push and pull request to `main` via GitHub Actions.

## CMIP6 Models

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

## Authors

* [Daniel Argueso](https://github.com/dargueso): Universitat de les Illes Balears
