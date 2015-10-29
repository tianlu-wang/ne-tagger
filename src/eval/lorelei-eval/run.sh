#!/usr/bin/env bash
set -e

usage="Usage: $0 GOLD SRC_DOC_DIR INPUT_DIR OUT_DIR [VISUALIZATION -v](Please use absolute path)"

if [ "$#" -lt 4 ]; then
    echo $usage
    exit 1
fi

SCRIPT=`basename ${BASH_SOURCE[0]}`
SCRIPTDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
GOLD=$1
SRC_DOC_DIR=$2
INPUT_DIR=$3
OUTPUT_DIR=$4

mkdir -p $OUTPUT_DIR
cd $SCRIPTDIR/neleval
scripts/run_tac15_evaluation.sh "${GOLD}" "${INPUT_DIR}" "${OUTPUT_DIR}" "1"

if [ ! -z $5 ]
then
    cd $SCRIPTDIR/edl-err-ana
    for f in $INPUT_DIR/*.tab
    do
	mkdir -p $OUTPUT_DIR/$(basename $f)
	python edl_err_ana.py $SRC_DOC_DIR $GOLD $f $OUTPUT_DIR/$(basename $f)
    done
fi
