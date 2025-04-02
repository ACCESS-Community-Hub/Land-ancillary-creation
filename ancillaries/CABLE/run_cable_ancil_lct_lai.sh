#!/bin/bash
#PBS -q normal
#PBS -l ncpus=4
#PBS -l mem=16GB
#PBS -l walltime=01:00:00
#PBS -l storage=gdata/hh5+gdata/access+gdata/rp23
#PBS -l wd
#PBS -l jobfs=1GB
#PBS -P rp23

# Generate CABLE land cover types (LCT) and leaf area index (LAI) ancillaries from CCI
# This script emulates the rose/cycl workflows that generate ancillaries 
# required to run JULES offline or with the UM-JULES Regional Ancillary Suite (RAS). 
# It is based on RAS suite (u-bu503) but uses ants/1.1.0 per 
# Siyuan's offline code. The main difference between the RAS (1.0) and Siyuan's (1.1)
# is the use of --use-new-saver, and the merging of soil roughness ancil with general
# soil parameters ancil

set -e
module purge
module use /g/data/access/ngm/modules
module load ants/1.1.0

ANTS_SRC_PATH=/g/data/rp23/experiments/2024-10-10_LWG_workingbee/mjl561/ants_src/ants_1p1
ANCIL_MASTER=/g/data/access/TIDS/UM/ancil/atmos/master
INPUT_PATH=/home/561/mjl561/git/LWG-Workshop-Day2-Scripts/ancillaries/ants_lct_inputs
ANCIL_TARGET_PATH=/g/data/rp23/experiments/2024-10-10_LWG_workingbee/mjl561/outputs_cable
ANCIL_PREPROC_PATH=/g/data/access/TIDS/RMED/ANTS/preproc

# check if the output directory exists
if [ ! -d ${ANCIL_TARGET_PATH} ]; then
    mkdir -p ${ANCIL_TARGET_PATH}
else 
    echo "following files exist in ${ANCIL_TARGET_PATH}"
    ls -l ${ANCIL_TARGET_PATH}
fi

# ============================================================================
# config based on RAS (u-bu503) app/ancil_lct/rose-app.conf, walltime ~ 1 min
source=${ANCIL_MASTER}/vegetation/cover/cci/v3/vegetation_fraction.nc
target_grid=${INPUT_PATH}/grid.nl
# transformpath=/g/data/access/TIDS/UM/ancil/data/transforms/cci2jules_ra1.json
transformpath=${INPUT_PATH}/cci2cable.json
output_vegfrac=${ANCIL_TARGET_PATH}/qrparm.veg.frac_cci_pre_c4_cable
output_lsm=${ANCIL_TARGET_PATH}
ANTS_CONFIG=${INPUT_PATH}/ancil_lct-app.conf

# ancil_lct.py takes the global categorical land cover product CCI [source]
# and converts it to JULES tiles using a crosswalking table [transformpath]
# it outputs landcover ancillary file [output_vegfrac], but as CCI does not 
# distinguish between c3/c4 grasses, another step is required (see below).
# see: https://code.metoffice.gov.uk/doc/ancil/ants/1.1/bin/ancil_lct.html
# outputs:
#   qrparm.veg.frac_cci_pre_c4.nc (intermediate file)
#   qrparm.mask_sea.nc (unknown use)
#   qrparm.mask.nc (land-sea mask)
python ${ANTS_SRC_PATH}/ancil_lct.py ${source} \
         --target-grid ${target_grid} --transform-path ${transformpath} \
         -o ${output_vegfrac} --landseamask-output ${output_lsm}       \
         --use-new-saver --ants-config ${ANTS_CONFIG}

# ============================================================================
# config based on RAS app/ancil_lct_postproc_c4/rose-app.conf, walltime ~ 1 min
source=${ANCIL_TARGET_PATH}/qrparm.veg.frac_cci_pre_c4_cable.nc
target_lsm=${ANCIL_TARGET_PATH}/qrparm.mask
output=${ANCIL_TARGET_PATH}/qrparm.veg.frac_cci_cable
c4source=${ANCIL_MASTER}/vegetation/cover/cci/v3/c4_percent_1d.nc
ANTS_CONFIG=${INPUT_PATH}/ancil_lct_postproc_c4-app.conf
c3level=6
c4level=7

# ancil_general_regrid.py regrids the c4 fraction [c4source] to the target grid [target_lsm]
# The config [ANTS_CONFIG] defines a linear horizontal regriddin scheme because the source
# data is very low resolution (1 degree) where normal area-weighted regridding results in
# sharp changes to c3/c4 fractions.
# see: https://code.metoffice.gov.uk/doc/ancil/ants/1.1/bin/ancil_general_regrid.html

# Then ancil_lct_postproc_c4.py uses the intermediate regridded c4 fraction source 
# [c4_percent_1d.nc] and includes it in a new 9 tile landcover fraction ancillary [output]
# see: https://code.metoffice.gov.uk/doc/ancil/ants/1.1/bin/ancil_lct_postproc_c4.html
# original 1 degree source for C3/C4 partitioning: ISLSCP II C4 Vegetation Percentage
# http://doi.org/10.3334/ORNLDAAC/932 (this being converted to nc on gadi)
# outputs: 
#   c4_percent_1d.nc (intermediate file)
#   qrparm.veg.frac_cci.nc (land fraction including c3 & c4 partition)

python ${ANTS_SRC_PATH}/ancil_general_regrid.py --ants-config ${ANTS_CONFIG} \
       ${c4source} --target-lsm ${target_lsm} -o ${ANCIL_TARGET_PATH}/c4_percent_1d.nc

python ${ANTS_SRC_PATH}/ancil_lct_postproc_c4.py \
       ${source} --islscpiic4 ${ANCIL_TARGET_PATH}/c4_percent_1d.nc \
       --c3level ${c3level} --c4level ${c4level} --use-new-saver -o ${output}

# ============================================================================
# config based on RAS (u-bu503) app/ancil_lai/rose-app.conf, walltime ~ 1 min
source=${ANCIL_MASTER}/vegetation/lai/modis_4km/v2/lai_preprocessed.nc
ANTS_CONFIG=${INPUT_PATH}/ancil_lai-app.conf
target_lsm=${ANCIL_TARGET_PATH}/qrparm.mask

# CABLE uses a single LAI value for each tile, so we only need to regrid MODIS
python ${ANTS_SRC_PATH}/ancil_general_regrid.py --ants-config ${ANTS_CONFIG} \
       ${source} --target-lsm ${target_lsm} -o ${ANCIL_TARGET_PATH}/lai_cable.nc