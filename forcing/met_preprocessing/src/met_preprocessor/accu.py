from xarray import DataArray
import xarray as xr


def daily_to_hourly_acc(da: DataArray) -> DataArray:
    gpd = da.groupby("time.date")
    diff_da = xr.concat(
        [
            gpd.first(keep_attrs=True).rename({"date": "time"}),
            gpd.apply(lambda x: x.diff("time")),
        ],
        dim="time",
    )
    diff_da.attrs["units"] = f"{diff_da.attrs['units']} hr**-1"
    return diff_da
