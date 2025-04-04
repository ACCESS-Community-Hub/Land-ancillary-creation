import numpy
import xarray
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

def convert_to_dominant(InputFile):
    """Convert a map of vegetation fractions per PFT to a dominant vegetation
    index."""

    # Take the old veg map, find the dominant type
    VegMap = InputFile["vegetation_area_fraction"].to_numpy()
    DominantMap = numpy.argmax(VegMap, axis=0) + 1
    DominantMap = numpy.ma.masked_where(VegMap[0, :, :] > 1.0, DominantMap)

    # Create the dictionary of attributes to attack to each of the variables
    VegAttrs = {
            "long_name"     : "CSIRO classification of vegetation type",
            "units"         : 1,
            "flag_values"   : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15,
                               16, 17],
            "flag_meanings" : "Evergreen_Needleleaf Evergreen_Broadleaf "+\
                              "Deciduous Needleleaf Deciduous Broadleaf "+\
                              "Shrub C3_Grassland C4_Grassland Tundra "+\
                              "C3_Cropland C4_Cropland Wetland Barren "+\
                              "Urban Lakes Ice",
            "missing_value": -1
            }

    # Create the output dataarray
    OutDataVariable = xarray.DataArray(
            data = DominantMap,
            coords = {
                "latitude": InputFile["latitude"],
                "longitude": InputFile["longitude"],
                },
            attrs = VegAttrs
            )

    return OutDataVariable

def write_to_disk(DominantVeg, OutFile):
    """Write the DataArray describing the dominant vegetation type to NetCDF
    file."""

    OutDataset = xarray.Dataset(
            data_vars = {"iveg": DominantVeg}
            )

    OutDataset.to_netcdf(OutFile, "w")

if __name__ == "__main__":
    args = _parse_args()

    DominantVeg = convert_to_dominant(xarray.open_dataset(args.input))

    write_to_disk(DominantVeg, args.output)
