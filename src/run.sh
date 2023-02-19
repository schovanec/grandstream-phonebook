#!/usr/bin/env bash

export VDIRSYNCER_CONFIG=${VDIRSYNCER_CONFIG:-$BASE_PATH/data/config}
DB_PATH=${DB_PATH:-$BASE_PATH/db/card}
OUTPUT_PATH=${OUTPUT_PATH:-$BASE_PATH/output/phonebook.xml}
VDIRSYNCER_PAIR=${VDIRSYNCER_PAIR:-contacts}

echo "vdirsyncer config: $VDIRSYNCER_CONFIG"
echo "vdirsyncer pair: $VDIRSYNCER_PAIR"
echo "database path: $DB_PATH"
echo "output path: $OUTPUT_PATH"

case $1 in 
  discover)
    vdirsyncer discover "${@:2}"
    ;;

  repair)
    vdirsyncer repair "${@:2}"
    ;;

  sync)
    update-phonebook.py "$DB_PATH" "$OUTPUT_PATH" "$VDIRSYNCER_PAIR"
    ;;

  *)
    SYNC_SCHEDULE=${SYNC_SCHEDULE:-* 3 * * *}
    echo "schedule: $SYNC_SCHEDULE"
    simple-scheduler.py "$SYNC_SCHEDULE" update-phonebook.py "$DB_PATH" "$OUTPUT_PATH" "$VDIRSYNCER_PAIR"
    ;;
esac
