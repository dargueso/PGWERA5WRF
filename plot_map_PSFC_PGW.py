import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# Load datasets
ds_era5 = xr.open_dataset('/home/dargueso/ERA5/ERA5_netcdf/era5_daily_sfc_20200401.nc')
ds_cmip6 = xr.open_dataset('/home/dargueso/BDY_DATA/CMIP6/ps_CC_signal_ssp585_2070-2099_1985-2014.nc')
month = ds_era5.time.dt.month.isel(time=0).item()

# --- ERA5: Surface Pressure ---
psfc_era5 = ds_era5.isel(time=0)['sp'] / 100  # Convert Pa to hPa
psfc_era5 = psfc_era5.assign_coords(lon=((psfc_era5.lon + 180) % 360) - 180)
psfc_era5 = psfc_era5.sortby('lon')

# --- CMIP6: Climate change signal in PSFC (mocked as tas delta) ---
# Using tas as proxy unless you have a CMIP6 pressure signal
psfc_cmip6 = ds_cmip6.sel(time=ds_cmip6.time.dt.month == month)['ps'] / 100
psfc_cmip6 = psfc_cmip6.assign_coords(lon=((psfc_cmip6.lon + 180) % 360) - 180)
psfc_cmip6 = psfc_cmip6.sortby('lon')

# --- Plot 1: ERA5 PSFC ---
fig = plt.figure(figsize=(7, 7))
ax = plt.axes(projection=ccrs.PlateCarree())
ct = ax.contourf(psfc_era5.lon, psfc_era5.lat, psfc_era5, levels=np.arange(500, 1050, 10),
                 cmap="Spectral_r", extend="both", transform=ccrs.PlateCarree())
ax.coastlines(linewidth=0.4, resolution='50m')
ax.set_extent([60, 110, 15, 50], crs=ccrs.PlateCarree())
gl = ax.gridlines(draw_labels=True, x_inline=False, y_inline=False, linewidth=0.2)
gl.top_labels = False; gl.right_labels = False
plt.colorbar(ct, label='PSFC (hPa)', shrink=0.6)
plt.title(f'ERA5 PSFC ({psfc_era5.time.dt.strftime("%d-%m-%Y").item()})')
plt.savefig('ERA5_PSFC_Himalayas.png', dpi=300)

# --- Plot 2: CMIP6 PSFC delta (mock) ---
fig = plt.figure(figsize=(7, 7))
ax = plt.axes(projection=ccrs.PlateCarree())
ct = ax.contourf(psfc_cmip6.lon, psfc_cmip6.lat, psfc_cmip6.squeeze(),
                 levels=np.arange(-5, 6, 1), cmap="RdBu_r", extend="both", transform=ccrs.PlateCarree())
ax.coastlines(linewidth=0.4, resolution='50m')
ax.set_extent([60, 110, 15, 50], crs=ccrs.PlateCarree())
gl = ax.gridlines(draw_labels=True, x_inline=False, y_inline=False, linewidth=0.2)
gl.top_labels = False; gl.right_labels = False
plt.colorbar(ct, label='ΔPSFC (hPa)', shrink=0.6)
plt.title('CMIP6 PSFC signal (PGW: 2070–2099 - 1985–2014)')
plt.savefig('CMIP6_PSFC_signal_Himalayas.png', dpi=300)

# --- Plot 3: Combined ERA5 + signal (PGW-style future PSFC) ---
psfc_future = psfc_era5 + psfc_cmip6

fig = plt.figure(figsize=(7, 7))
ax = plt.axes(projection=ccrs.PlateCarree())
ct = ax.contourf(psfc_future.lon, psfc_future.lat, psfc_future.squeeze(),
                 levels=np.arange(500, 1050, 10), cmap="Spectral_r", extend="both", transform=ccrs.PlateCarree())
ax.coastlines(linewidth=0.4, resolution='50m')
ax.set_extent([60, 110, 15, 50], crs=ccrs.PlateCarree())
gl = ax.gridlines(draw_labels=True, x_inline=False, y_inline=False, linewidth=0.2)
gl.top_labels = False; gl.right_labels = False
plt.colorbar(ct, label='Future PSFC (hPa)', shrink=0.6)
plt.title('Future PSFC = ERA5 + CMIP6 signal')
plt.savefig('PGW_PSFC_Himalayas.png', dpi=300)


