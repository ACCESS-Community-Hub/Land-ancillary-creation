import yaml
import xarray as xr
import met_preprocessor.standard_param as standard_param
import met_preprocessor.opt_param as opt_param
from met_preprocessor.unit_conv import UnitConversion
from met_preprocessor.utils import list_nc_files
import itertools

xr.set_options(keep_attrs=True)

OUTPUT_FILE_FORMAT = "NETCDF4"
CONFIG_FILE_NAME = "config.yaml"
PARAM_MAP_FILE_NAME = "param_map.yaml"


def get_rename_param_criteria(params, param_map):
    """All input_param act as keys with the original key as value."""
    param_criteria = {}
    for param, param_info in param_map.items():
        for input_value in param_info.get("input_param", []):
            if input_value in params:
                param_criteria[input_value] = param
    return param_criteria


def get_unit_conv_params(param_map):
    """Units conversions are to be done for all params having unit in mapping."""
    return [
        param
        for param, param_attrs in param_map.items()
        if param_attrs.get("unit") is not None
    ]


with open(PARAM_MAP_FILE_NAME) as file:
    param_map = yaml.safe_load(file)


def process_dependencies(param_map):
    """Lists set of possible dependencies and their callable functions
    for a param."""
    dependencies = {}
    for param, param_info in param_map.items():
        ans = []
        for pi_calc in param_info.get("calc", []):
            func = None
            if param_info["type"] == "standard":
                func = getattr(standard_param, pi_calc["func"])
            elif param_info["type"] == "optional":
                func = getattr(opt_param, pi_calc["func"])
            else:
                raise Exception("Not yet defined for just conversion params")
            parsed_deps = pi_calc.get("deps", "").split(",")
            ans.append((parsed_deps, func))
        dependencies[param] = ans

    return dependencies


def cycle_check(node: str, visited: dict[str, bool], adj_list: dict[str, list[str]]):
    """Cycle checks using DFS."""

    # Already visited node
    if visited.get(node):
        return True

    visited[node] = True
    res = any([cycle_check(dep, visited, adj_list) for dep in adj_list.get(node, [])])
    if not res:
        del visited[node]

    return res


def replace_tup(tup_list, val, new_tup):
    for i, tup in enumerate(tup_list):
        if tup[0] == val:
            tup_list[i] = new_tup
            return tup_list
    return tup_list + [new_tup]


def order_load_dep(res, dependencies, input_list):
    """
    Given a DAG, convert which order to calculate values.
    Eg: input_list = {1, 3}  dependencies = {2 : [[1, 4], [1, 3]], 4 : 1}
    Here answer should be {4 : [1] , 2 : [1, 4]} based on priority
    """
    for param, dep_list in dependencies.items():
        for i, (deps, func) in enumerate(dep_list):
            if set(deps).issubset(set(input_list)):
                # Remove on/after param
                dependencies[param] = dependencies[param][:i]
                # Replace param in res if present otherwise append
                updated_res = replace_tup(res, param, (param, deps, func))
                return order_load_dep(updated_res, dependencies, input_list + [param])
    # If no extra dependencies found, then return the accumulated result
    return res


def generate_calculations(dataset, param_map):
    pd = process_dependencies(param_map)
    is_cycle_chain = {
        k: list(set(itertools.chain.from_iterable([vi[0] for vi in v])))
        for k, v in pd.items()
    }
    for node in pd.keys():
        if cycle_check(node, {}, is_cycle_chain):
            raise Exception(f"Cycle detected near {node}")
    return order_load_dep([], pd, list(dataset.keys()) + ["none"])


def run_met():
    """Run preprocessor for meteorological forcing dataset(s)."""

    with open(CONFIG_FILE_NAME) as file:
        config = yaml.safe_load(file)

    with open(PARAM_MAP_FILE_NAME) as file:
        param_map = yaml.safe_load(file)

    ## REVIEW: Have validator like cerberus
    file_list = []
    for dir in config.get("directories"):
        file_list += list_nc_files(dir)

    ## TODO: Have to combine everything as provenance
    ## TODO: Look more into parameter options for open_mfdataset
    ## (correctness in merging data, parallel processing)
    print(f"Loading combined dataset from {file_list}")
    dataset = xr.open_mfdataset(file_list, compat="override", coords="minimal")
    print("Loaded combined dataset")
    print(dataset)

    # Rename parameters
    param_criteria = get_rename_param_criteria(list(dataset.keys()), param_map)
    dataset = dataset.rename(param_criteria)

    # Unit conversions
    ## List of all params for unit conversions
    params = get_unit_conv_params(param_map)
    param_conv = UnitConversion(params)

    for param in params:
        if dataset.get(param) is not None:
            dataset[param] = param_conv.convert_param(
                dataset[param], param_map[param]["unit"]
            )
        else:
            print(f"Standard Stage: Skipping {param}")

    # Doing all possible calculations (Params)
    ## For strict ordering, resulting graph must be DAGs
    ## Can used memoisation + greedy approach
    dep_list = generate_calculations(dataset, param_map)

    for param, deps, func in dep_list:
        if deps == []:
            dep_attrs = [dataset.coords, dataset.dims]
        else:
            dep_attrs = list(map(lambda x: dataset[x], deps))
        # TODO: Try just base unit conversion
        dataset[param] = func(*dep_attrs)
        dataset[param] = dataset[param].metpy.dequantify()
        # After convert to actual units needed
        dataset[param] = param_conv.convert_param(
            dataset[param], param_map[param]["unit"]
        )

    # Only keep standard/optional variables (not including index variables)
    dataset = dataset.drop_vars(
        list(
            filter(
                lambda x: param_map.get(x, {}).get("type", "")
                not in ["standard", "optional"],
                list(dataset.keys()),
            )
        )
    )

    print("Saving dataset")

    # Combine filtered params
    dataset.to_netcdf(config["output_file"], format="NETCDF4")


if __name__ == "__main__":
    run_met()
