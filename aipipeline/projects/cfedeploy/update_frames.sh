#!/bin/bash
# update_frames.sh
SQL_FILE="./update_main_localization_frame.sql"
CSV_FILE="$1"

if [ -z "$CSV_FILE" ]; then
    echo "Usage: $0 <csv_file>"
    exit 1
fi

if [ ! -f "$CSV_FILE" ]; then
    echo "Error: CSV file '$CSV_FILE' not found"
    exit 1
fi

# Create a modified SQL file that doesn't drop tmp_raw_csv at the beginning
TEMP_SQL=$(mktemp)

# Copy SQL file but remove the first DROP TABLE command for tmp_raw_csv
sed '/DROP TABLE IF EXISTS tmp_raw_csv;/d' "$SQL_FILE" > "$TEMP_SQL"

echo "Step 1: Creating temporary table..."
docker exec -i postgis \
    psql -U django -d tator_online \
    -c "DROP TABLE IF EXISTS tmp_raw_csv; CREATE UNLOGGED TABLE tmp_raw_csv (frame INTEGER, uuid UUID);"

echo "Step 2: Loading CSV data..."
docker exec -i postgis \
    psql -U django -d tator_online \
    -c "\copy tmp_raw_csv FROM STDIN CSV HEADER" \
    < "$CSV_FILE"

echo "Step 3: Running update operations..."
docker exec -i postgis \
    psql -U django -d tator_online \
    -v ON_ERROR_STOP=1 \
    < "$TEMP_SQL"

echo "Step 4: Cleaning up..."
rm "$TEMP_SQL"

echo "Done!"
