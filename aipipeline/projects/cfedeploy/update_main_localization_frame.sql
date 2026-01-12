-- ============================================================
-- Update main_localization.frame from CSV via UUID
-- Handles extra CSV columns and type conversion
-- PostGIS / Docker-friendly
-- ============================================================
DROP TABLE IF EXISTS tmp_main_localization_frame;

CREATE UNLOGGED TABLE tmp_main_localization_frame (
                                                      frame INTEGER,
                                                      elemental_id UUID PRIMARY KEY
);

-- 4️⃣ Populate staging table with proper UUID type
INSERT INTO tmp_main_localization_frame (frame, elemental_id)
SELECT frame, uuid::uuid
FROM tmp_raw_csv
WHERE uuid IS NOT NULL;

-- 5️⃣ Ensure index on target table for faster update
CREATE INDEX IF NOT EXISTS idx_main_localization_elemental_id
    ON main_localization (elemental_id);

-- 6️⃣ Update target table safely
BEGIN;

UPDATE main_localization m
SET frame = t.frame
FROM tmp_main_localization_frame t
WHERE m.elemental_id = t.elemental_id
  AND m.frame IS DISTINCT FROM t.frame;

COMMIT;

-- 7️⃣ Optional verification
SELECT COUNT(*) AS rows_updated
FROM main_localization m
         JOIN tmp_main_localization_frame t
              ON m.elemental_id = t.elemental_id
WHERE m.frame = t.frame;

-- 8️⃣ Check for UUIDs missing in DB
SELECT COUNT(*) AS missing_ids
FROM tmp_main_localization_frame t
         LEFT JOIN main_localization m USING (elemental_id)
WHERE m.elemental_id IS NULL;

-- 9️⃣ Cleanup staging tables
DROP TABLE tmp_raw_csv;
DROP TABLE tmp_main_localization_frame;
