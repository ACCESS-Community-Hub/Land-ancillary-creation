from ants/fileformats/namelist/umgrid.py

UM grid regular grid namelist ('GRID') interpreter.
--------------------------------------------------

See the following specification::

    points_lambda_targ
        - Number of columns (longitudes).
        - Optional: Parameter is derived if `delta_lambda_targ` specified.

    points_phi_targ:
        - Number of rows (latitudes).
        - Optional: Parameter is derived if `phi_lambda_targ` specified.

    lambda_origin_targ
        - Longitude origin.
        - Default: 0.0 if not specified.

    phi_origin_targ:
        - Latitude origin.
        - Default: 90.0 if not specified. This parameter should be specified
            for ENDgame grids.

    delta_lambda_targ:
        - Longitude spacing (degrees).
        - Optional: Parameter is derived if `points_lambda_targ` specified.

    delta_phi_targ:
        - Latitutde spacing (degrees).
        - Optional: Parameter is derived if `points_phi_targ` specified.

    phi_pole:
        - Real latitude of North Pole of the rotated grid.
        - Default: 90.0

    lambda_pole:
        - Real longitude of North Pole of the rotated grid.
        - Default: 0.0

    global:
        - Global grid.
        - Default: T (True).

    igrid_targ:
        - Grid indicator (2=ArwakawaB, 3=ArwakawaC, 6=ENDgame).
        - Default: 6

    inwsw:
        - ==0 if phi origin specified as NW corner. ==1 if SW corner.
        - Default: 1

Raises
------
RuntimeError
    If the grid is overspecified, and the number of points is not
    consistent with the spacing between the points, a RunTimeError will be
    raised.

RuntimeError
    In the case where grids are underspecified, a suitable RuntimeError
    exception will be raised.

    defaults = {
        "grid": {
            "points_lambda_targ": None,
            "points_phi_targ": None,
            "lambda_origin_targ": 0.0,
            "phi_origin_targ": 90.0,
            "delta_lambda_targ": None,
            "delta_phi_targ": None,
            "phi_pole": 90.0,
            "lambda_pole": 0.0,
            "global": True,
            "igrid_targ": GRIDS["endgame"],
            "inwsw": 0,
            "rotated_interp": None,
        }
    }