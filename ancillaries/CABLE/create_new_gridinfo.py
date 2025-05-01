# Create a new gridinfo file with just LAI and vegetation type modified

import xarray
import argparse

JULES_TO_CABLE_MAPPING = {
        "soil_albedo"   : "albedo2",
        "T_CLAY"        : "clay",
        "T_SILT"        : "silt",
        "T_SAND"        : "sand",
        "BD"            : "bch",
        "sm_wilt"       : "swilt",
        "sm_crit"       : "sfc",
        "sm_sat"        : "ssat",
        "sathh"         : "sucs",
        "hcon"          : "cnds",
        "satcon"        : "hyds"
        }

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
            "--inputdir",
            help="Directory containing the results of the ANTS ancillary suite"
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

def create_new_gridinfo(RefGridinfo, InputDir, OutFile, InvertLat):
    """Take the LAI and vegetation data from the ANTS sources and add them to
    the default CABLE gridinfo file."""

    # Open the reference gridinfo that we're going to write to
    RefGridinfo = xarray.open_dataset(RefGridinfo)

    # We know the names of the relevant files in the output directory
    VegMap = xarray.open_dataset(InputDir + "qrparm.veg.dominant_cci_cable.nc")
    LAI = xarray.open_dataset(InputDir + "lai_cable.nc")
    JULESSoil = xarray_open_dataset(InputDir + "qrparm.soil_cci.nc")

    # Invert latitudes if required
    if InvertLat:
        VegMap = VegMap.isel(latitude=slice(None, None, -1))
        LAI = LAI.isel(latitude=slice(None, None, -1))
        JULESSoil = JULESSoil.isel(latitude=slice(None, None, -1))

    # Add the variables to original dataset
    RefGridinfo["LAI"].values = LAI["leaf_area_index"].values
    RefGridinfo["iveg"].values = VegMap["iveg"].values

    for JULESVar, CABLEVar in JULES_TO_CABLE_MAPPING.items():
        RefGridinfo[CABLEVar].values = JULESSoil[JULESVar].values

    RefGridinfo.to_netcdf(OutFile, "w")

    return 0

if __name__ == "__main__":
    args = _parse_args()

    create_new_gridinfo(
            args.refgridinfo,
            args.inputdir,
            args.output,
            args.invertlat
            )
