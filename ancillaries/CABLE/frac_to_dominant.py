import numpy
import xarray
import iris
import argparse

def _parse_args():
    """Read the command line arguments."""

    parser = argparse.ArgumentParser(
            prog="convert_to_dominant",
            description="Convert a vegetation map created by ANTS to a " +\
                "dominant vegetation type usable by CABLE"
            )

    parser.add_argument(
            "-i",
            "--input",
            help="Input file containing the original vegetation map"
            )
    parser.add_argument(
            "-o",
            "--output",
            help="Output file for the new dominant vegetation map"
            )

    return parser.parse_args()

def convert_to_dominant(fname):
    """Convert a map of vegetation fractions per PFT to a dominant vegetation
    index.
    
    Args:
        fname (str): the input filename
    """

    # load through iris for mask
    cb = iris.load_cube(fname)
    mask = cb[0,...].data.mask

    # Take the old veg map, find the dominant type
    VegMap = cb.data.data
    DominantMap = numpy.argmax(VegMap, axis=0) + 1

    # Create the dictionary of attributes to attack to each of the variables
    VegAttrs = {
            "long_name"     : "CSIRO classification of vegetation type",
            "units"         : 1,
            "flag_values"   : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15,
                               16, 17],
            "flag_meanings" : "Evergreen_Needleleaf Evergreen_Broadleaf "+\
                              "Deciduous_Needleleaf Deciduous_Broadleaf "+\
                              "Shrub C3_Grassland C4_Grassland Tundra "+\
                              "C3_Cropland C4_Cropland Wetland Empty Empty "+\
                              "Barren Urban Lakes Ice",
            "missing_value": -1
            }

    # Create the output dataarray
    OutDataVariable = xarray.DataArray(
            data = DominantMap,
            coords = {
                "longitude": cb.coord("longitude").points,
                "latitude": cb.coord("latitude").points,
                },
            dims=["latitude", "longitude"],
            attrs = VegAttrs
            )

    # set the mask
    OutDataVariable = OutDataVariable.where(~mask)

    return OutDataVariable

def save_to_netcdf(da, fname):
    """Save the data array to a NetCDF file.
    
    Args:
        da (xarray.DataArray): the data array to save
        fname (str): the output filename
    """

    ds = xarray.Dataset({"iveg": da})

    # set encoding
    ds["iveg"].encoding["dtype"] = "int32"
    ds["iveg"].encoding["zlib"] = True
    ds["iveg"].encoding["_FillValue"] = -1

    # save to NetCDF
    ds.to_netcdf(fname, format="NETCDF4", unlimited_dims="time")
    print(f"Saved dominant vegetation map to {fname}")

    return

if __name__ == "__main__":

    args = _parse_args()
    iveg = convert_to_dominant(args.input)
    save_to_netcdf(iveg, args.output)
    
