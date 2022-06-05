-- Retrieve the ICU episode slices on the ward from HyFlow that were active as at horizon timestamp
--
-- param horizon_dt: horizon timestamp
-- param ward: ward code

WITH q AS
       (
         SELECT ep.*
         FROM hyflow.icu_episode_slices_log ep
                INNER JOIN hydef.beds beds ON ep.bed_id = beds.id
                INNER JOIN hydef.bays bays ON beds.bay_id = bays.id
         WHERE bays.ward_code = %(ward)s
         AND ep.horizon_dt <=  %(horizon_dt)s                                -- check the future is opaque
         AND ep.admission_dt <= %(horizon_dt)s                               -- check admission happened at or before horizon
         AND (ep.discharge_dt IS NULL OR ep.discharge_dt > %(horizon_dt)s)   -- check patient still present at horizon
)
SELECT id AS episode_slice_id,
       episode_key,
       csn,
       admission_dt,
       discharge_dt,
       bed_id,
       horizon_dt,
       log_dt
FROM (
       SELECT *,
              ROW_NUMBER() OVER (PARTITION BY csn ORDER BY horizon_dt DESC, log_dt DESC) AS position
       FROM q
     ) s
WHERE s.position = 1