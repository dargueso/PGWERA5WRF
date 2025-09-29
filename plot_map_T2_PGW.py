import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# Load the data
ds_era5 = xr.open_dataset('/home/dargueso/ERA5/ERA5_netcdf/era5_daily_sfc_20200401.nc')
ds_cmip6 = xr.open_dataset('/home/dargueso/BDY_DATA/CMIP6/tas_CC_signal_ssp585_2070-2099_1985-2014.nc')

month = ds_era5.time.dt.month.isel(time=0).item()
# Select the variable and the time slice

temp_era5 = ds_era5.isel(time=0).squeeze()['2t']
temp_era5 = temp_era5.assign_coords(lon=((temp_era5.lon + 180) % 360) - 180)
temp_era5 = temp_era5.sortby('lon')
temp_cmip6 = ds_cmip6.sel(time=ds_cmip6.time.dt.month == month)['tas']
temp_cmip6 = temp_cmip6.assign_coords(lon=((temp_cmip6.lon + 180) % 360) - 180)
temp_cmip6 = temp_cmip6.sortby('lon')

# Create the figure
fig = plt.figure(figsize=(7, 7))
ax = plt.axes(projection=ccrs.PlateCarree())

# Plot temperature over Europe
ct = ax.contourf(
        temp_era5.lon,
        temp_era5.lat,
        temp_era5,
        levels=np.arange(270, 305, 5),
        cmap="viridis",
        extend="both",
        transform=ccrs.PlateCarree(),
    )
#temp_era5.plot(ax=ax, transform=ccrs.PlateCarree(), cmap="viridis", extend="both", cbar_kwargs={'label': 'Temperature (K)'})

# Add features
ax.coastlines(linewidth=0.4,zorder=102,resolution='50m')
ax.set_extent([60, 110, 15, 50], crs=ccrs.PlateCarree())  # Set the extent to cover Europe
gl = ax.gridlines(
    crs=ccrs.PlateCarree(),
    xlocs=range(60, 115, 5),
    ylocs=range(10, 55, 5),
    draw_labels=True,
    zorder=102,
    x_inline=False,
    y_inline=False,
    linewidth=0.2,
    color="k",
    alpha=1,
    linestyle="-",
)
gl.top_labels = False
gl.right_labels = False
plt.colorbar(ct,label='K',ticks=range(270, 305, 5), shrink=0.62)

plt.title(f'ERA5 ({temp_era5.time.dt.strftime("%d-%m-%Y").item()})')
plt.savefig('ERA5_temperature.png', dpi=300)



# Create the figure for CMIP6
fig = plt.figure(figsize=(7, 7))
ax = plt.axes(projection=ccrs.PlateCarree())

# Plot temperature over Europe for CMIP6
ct = ax.contourf(
        temp_cmip6.lon,
        temp_cmip6.lat,
        temp_cmip6.squeeze(),
        levels=np.arange(0, 7.5, 0.5),
        cmap="inferno",
        extend="both",
        transform=ccrs.PlateCarree(),
    )
#temp_cmip6.plot(ax=ax, transform=ccrs.PlateCarree(), cmap="inferno", extend="both", cbar_kwargs={'label': 'Temperature (K)'})

# Add features
ax.coastlines(linewidth=0.4, zorder=102, resolution='50m')
ax.set_extent([60, 110, 15, 50], crs=ccrs.PlateCarree())  # Set the extent to cover Europe
gl = ax.gridlines(
    crs=ccrs.PlateCarree(),
    xlocs=range(60, 115, 5),
    ylocs=range(10, 55, 5),
    draw_labels=True,
    zorder=102,
    x_inline=False,
    y_inline=False,
    linewidth=0.2,
    color="k",
    alpha=1,
    linestyle="-",
)
gl.top_labels = False
gl.right_labels = False 
plt.colorbar(ct,label='K',ticks=np.arange(0, 7.5, 0.5), shrink=0.62)

plt.title(f'CMIP6 T2 change ({temp_era5.time.dt.strftime("%B").item()})')
plt.savefig('CMIP6_temperature.png', dpi=300)


# Plot temperature over Europe for ERA5
fig = plt.figure(figsize=(7, 7))
ax = plt.axes(projection=ccrs.PlateCarree())

# Plot temperature over Europe
ct = ax.contourf(
        temp_era5.lon,
        temp_era5.lat,
        temp_era5+temp_cmip6.squeeze(),
        levels=np.arange(270, 305, 5),
        cmap="viridis",
        extend="both",
        transform=ccrs.PlateCarree(),
    )
#temp_era5.plot(ax=ax, transform=ccrs.PlateCarree(), cmap="viridis", extend="both", cbar_kwargs={'label': 'Temperature (K)'})

# Add features
ax.coastlines(linewidth=0.4,zorder=102,resolution='50m')
ax.set_extent([60, 110, 15, 50], crs=ccrs.PlateCarree())  # Set the extent to cover Europe
gl = ax.gridlines(
    crs=ccrs.PlateCarree(),
    xlocs=range(60, 115, 5),
    ylocs=range(10, 55, 5),
    draw_labels=True,
    zorder=102,
    x_inline=False,
    y_inline=False,
    linewidth=0.2,
    color="k",
    alpha=1,
    linestyle="-",
)
gl.top_labels = False
gl.right_labels = False
plt.colorbar(ct,label='K',ticks=range(270, 305, 5), shrink=0.62)

plt.title(f'PGW: ERA5 + CMIP6 ({temp_era5.time.dt.strftime("%d-%m-%Y").item()})')
plt.savefig('PGW_temperature.png', dpi=300)

