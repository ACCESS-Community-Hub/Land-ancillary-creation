import numpy
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

    parser.add_argument(
            "-m",
            "--method",
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

    return iris.load(input_file, "vegetation_area_fraction")

def aggregate_vegetation(input_veg_map, agg_config_file):
    """Aggregate the given vegetation map using the specified method, and
    return a Iris Cube representing the new vegetation map."""

    # Read the configuration file
    agg_config = ants.fileformats.json.load(
            agg_config_file,
            keys=['aggregation_method', 'threshold'],
            dtypes=['float', 'int']
            )

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
    else:
        raise ValueError("Invalid option supplied for --method.")

def convert_to_dominant(veg_map):
    """Convert the given Iris Cube representing the map of vegetation fractions
    to a map of the dominant vegetation type."""

    
    dominant vegetation types.
if __name__ == "__main__":

    args = parse_args()
    input_veg_map = load_vegetation(args.input)
    output_veg_map = aggregate_vegetation(input_veg_map, args.method)
    write_to_netcdf(output_veg_map)
