import numpy
import iris
import argparse
import ants
import json
import xarray

IVEG_ATTRS = { 
            "long_name"     : "CSIRO classification of vegetation type",
            "units"         : 1,
            "flag_values"   : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15,
                               16, 17],
            "flag_meanings" : "Evergreen_Needleleaf Evergreen_Broadleaf "+\
                              "Deciduous_Needleleaf Deciduous_Broadleaf "+\
                              "Shrub C3_Grassland C4_Grassland Tundra "+\
                              "C3_Cropland C4_Cropland Wetland Empty Empty "+\
                              "Barren Urban Lakes Ice",
            "missing_value" : -1,
            "_FillValue"    : -1
            }

PATCHFRAC_ATTRS = {
            "long_name"     : "vegetation_area_fraction",
            "units"         : 1,
            "missing_value" : 1e20,
            "_FillValue"    : 1e20
            }

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

    parser.add_argument(
            "-c",
            "--config",
            help="Method by which to aggregate the vegetation fractions",
            default="dominant"
            )

    return parser.parse_args()

def load_vegetation(input_file):
    """Retrieve the Iris Cube corresponding to the vegetation_area_fraction
    from the file provided.

    Args:
        input_file (str): File containing the vegetation_area_fraction cube.
    """

    return iris.load(input_file, "vegetation_area_fraction")[0]

def aggregate_vegetation(input_veg_map, agg_config_file):
    """Aggregate the given vegetation map using the specified method, and
    return a Iris Cube representing the new vegetation map."""

    # Read the configuration file
    #agg_config = ants.fileformats.json.load(agg_config_file)
    with open(agg_config_file) as conf_file:
        agg_config = json.load(conf_file)

    # Execute the given aggregation method
    if agg_config['aggregation_method'] == 'dominant':
        new_veg_map, veg_fractions = convert_to_dominant(input_veg_map)
    elif agg_config['aggregation_method'] == '1tree1grass':
        new_veg_map, veg_fractions = convert_to_1tree_1grass(input_veg_map)
    elif agg_config['aggregation_method'] == 'min_threshold':
        new_veg_map, veg_fractions = apply_min_threshold(
                input_veg_map,
                agg_config['threshold']
                )
    elif agg_config['aggregation_method'] == 'none':
        new_veg_map, veg_fractions = apply_min_threshold(
                input_veg_map,
                0.0
                )
    else:
        raise ValueError("Invalid option supplied for method.")

    # Convert the arrays into an xarray Dataset
    return iveg_and_patchfrac_to_dataset(
            input_veg_map,
            new_veg_map,
            veg_fractions
            )

def convert_to_dominant(veg_map):
    """Convert the given Iris Cube representing the map of vegetation fractions
    to a map of the dominant vegetation type, by taking the vegetation type
    with the largest fraction."""

    dominant_map = numpy.argmax(veg_map.data.data, axis=0) + 1

    # Add the patch dimension
    dominant_map = dominant_map[numpy.newaxis, :, :]

    # Apply the mask
    dominant_map = numpy.ma.masked_array(
            dominant_map,
            veg_map.data.mask[0, :, :],
            dtype=numpy.int32
            )
    patch_frac = numpy.ma.ones_like(dominant_map, dtype=numpy.float32)

    return dominant_map, patch_frac

def convert_to_1tree_1grass(veg_map):
    """Convert the vegetation map to a map in which a grid cell can only
    contain a single tree and grass type."""

    # Approach here is unclear- what do we do about the other tiles? Do we just
    # use the full 17? Mark this as unimplemented for now

    raise NotImplementedError("1tree1grass conversion is not yet implemented.")

    return None, None

def apply_min_threshold(veg_map, threshold):
    """Apply a minimum threshold to the vegetation map. All tiles with a
    fraction lower than the given threshold are set to 0.0 fraction."""

    # Zero out anything less than the threshold
    veg_map.data.data[veg_map.data.data < threshold] = 0.0

    # Rescale the fractions
    ants.analysis.cover_mapping.normalise_fractions(veg_map)

    # We use a value of -1 to indicate "no tile"- so set everywhere with a 0.0
    # patch fraction
    tile_map = numpy.empty(veg_map.data.data.shape, dtype=numpy.int32)

    for tile in range(tile_map.shape[0]):
        tile_map[:, :, tile] = tile+1

    # Now set the tiles with zero patch fraction to -1
    tile_map = numpy.where(veg_map.data.data == 0.0, -1, tile_map)

    # NOTE: The commented out section below was built forgetting that CABLE
    # ignores any tile with a vegetation type of -1 (I think)- so there's no
    # need to do the tailored cutting of array elements

    # # Set up the tile map- only include tiles which have a non-zero fraction
    # # somewhere. To do this, take the maximum over the spatial dimensions, so
    # # we end with a length 17 array of maxima. Then we can use that compared to
    # # the threshold as a "mask" to reduce the number of tiles to only those
    # # necessary
    # nonzero_tiles = numpy.max(veg_map.data.data, axis=(0,1)) >= threshold
    # veg_map.data.data = veg_mag.data.data[:, :, nonzero_tiles]

    # # Now we have the map of patch fractions- now create the associated
    # # vegetation type matrix. Take the spatial dimensions, and then the number
    # # of active tiles as the dimensions
    # tile_map = numpy.empty(
            # veg_map.data.data.shape[0:2] + (numpy.count(nonzero_tiles),),
            # dtype=numpy.int32
            # )

    # # Walk through each of the tiles, and if the tile is active somewhere, fill
    # # that page of the tile array with the desired vegetation type
    # tile_indx = 0
    # for tile, is_nonzero in enumerate(nonzero_tiles):
        # # Only include tiles which have non-zero fraction somewhere
        # if is_nonzero:
            # tile_map[:, :, tile_indx] = tile+1
            # tile_indx += 1

    # End superfluous section
    
    # Apply the mask to the tile map
    masked_tile_map = numpy.ma.masked_array(tile_map, veg_map.data.mask)

    return masked_tile_map, veg_map.data

def iveg_and_patchfrac_to_dataset(ref_dataset, iveg, patchfrac):
    """Convert the given arrays denoting the tile PFTs and respective fractions
    into a single xarray.Dataset. Retrieve the dimensions from the reference
    dataset, which is in the form of an iris Cube."""

    num_tiles = iveg.shape[0]
    out_dataset = xarray.Dataset(
            coords = {
                "longitude": ref_dataset.coord("longitude").points,
                "latitude": ref_dataset.coord("latitude").points,
                "patch": numpy.arange(num_tiles)
                },
            data_vars=dict(
                iveg        = (
                    ["patch", "latitude", "longitude"],
                    iveg,
                    IVEG_ATTRS
                    ),
                patchfrac   = (
                    ["patch", "latitude", "longitude"],
                    patchfrac,
                    PATCHFRAC_ATTRS
                    )
                )
            )

    return out_dataset

def write_to_netcdf(output_veg_map, out_filename):
    """Write the Dataset to NetCDF at the given out_filename."""

    output_veg_map.to_netcdf(out_filename)

if __name__ == "__main__":

    args = _parse_args()
    input_veg_map = load_vegetation(args.input)
    output_veg_map = aggregate_vegetation(input_veg_map, args.config)
    write_to_netcdf(output_veg_map, args.output)
