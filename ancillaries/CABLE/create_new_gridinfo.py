# Create a new gridinfo file with just LAI and vegetation type modified

import xarray
import argparse

def _parse_args():
    """Read the command line arguments."""

    parser = argparse.ArgumentParser(
            prog="create_new_gridinfo",
            description="Take the LAI and dominant vegetation type created " +\
                    "created by the ANTS workflow and plug them into the " +\
                    "CABLE gridinfo."
            )

    parser.add_argument(
            "-r",
            "--refgridinfo",
            help="Reference CABLE gridinfo file"
            )
    parser.add_argument(
            "-l",
            "--lai",
            help="File containing the LAI data"
            )
    parser.add_argument(
            "-v",
            "--vegetation",
            help="File containing the vegetation data"
            )
    parser.add_argument(
            "--invertlat",
            help="Whether to invert the latitude axis of the data coming " +\
                    "ANTS. Defaults to True.",
            default=True
            )
    parser.add_argument(
            "-o",
            "--output",
            help="File to write the output to"
            )

    return parser.parse_args()

def create_new_gridinfo(RefGridinfo, LAI, VegMap, OutFile, InvertLat):
    """Take the LAI and vegetation data from the ANTS sources and add them to
    the default CABLE gridinfo file."""

    RefGridinfo = xarray.open_dataset(RefGridinfo)

    VegMap = xarray.open_dataset(VegMap)
    LAI = xarray.open_dataset(LAI)

    # Invert latitudes if required
    if InvertLat:
        VegMap = VegMap.isel(latitude=slice(None, None, -1))
        LAI = LAI.isel(latitude=slice(None, None, -1))

    # Add the variables to original dataset
    RefGridinfo["LAI"].values = LAI["leaf_area_index"].values
    RefGridinfo["iveg"].values = VegMap["iveg"].values

    RefGridinfo.to_netcdf(OutFile, "w")

    return 0

if __name__ == "__main__":
    args = _parse_args()

    create_new_gridinfo(
            args.refgridinfo,
            args.lai,
            args.vegetation,
            args.output,
            args.invertlat
            )
