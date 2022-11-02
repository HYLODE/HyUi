--- Query to determine if a patient is going to be admitted to ICU in a given time window
--- D Stein 2021, adapted from HyFLOW query

WITH rough_census AS
       (
        SELECT 	hv.encounter AS csn,
   		hv.hospital_visit_id AS hv_id,
         lv.admission_time    AS admission_dt,
         lv.discharge_time AS discharge_dt,
         loc.location_string  AS hl7_location,
			m.mrn AS mrn

         FROM star.hospital_visit hv
                LEFT JOIN star.mrn m
                          ON hv.mrn_id = m.mrn_id
                LEFT JOIN star.core_demographic pt
                          ON m.mrn_id = pt.mrn_id
                LEFT JOIN star.location_visit lv
                          ON hv.hospital_visit_id = lv.hospital_visit_id
                LEFT JOIN star.location loc
                          ON lv.location_id = loc.location_id


         WHERE (loc.location_string IN (SELECT loc FROM flow.ward_location))--(loc.location_string LIKE 'T03%%' OR loc.location_string LIKE '%%T06PACU%%' OR loc.location_string LIKE '%%GWB L01 CC%%')
           AND hv.patient_class = 'INPATIENT'
           AND hv.admission_time IS NOT NULL -- check a valid hospital visit
           AND lv.admission_time <= NOW() - '48 HOURS'::INTERVAL - '0 HOURS'::INTERVAL                                     -- check location admission happened at or before horizon
           AND (hv.discharge_time IS NULL OR hv.discharge_time > NOW() - '48 HOURS'::INTERVAL - '0 HOURS'::INTERVAL)       -- check patient is still in hospital at horizon
           AND (lv.discharge_time IS NULL OR lv.discharge_time > NOW() - '48 HOURS'::INTERVAL)       -- check patient is still at location at horizon
           AND (pt.date_of_death IS NULL OR pt.date_of_death > NOW() - '48 HOURS'::INTERVAL) -- check patient is alive at horizon

       ),
     census AS
       (
         SELECT csn,
                hv_id,
                admission_dt,
                hl7_location,
                mrn
         FROM (
                SELECT csn,
                       hv_id,
                       admission_dt,
                       hl7_location,
                       ROW_NUMBER() OVER (PARTITION BY hl7_location ORDER BY admission_dt DESC) AS POSITION,
                       mrn
                FROM rough_census
              ) occupant_ordered
         WHERE occupant_ordered.position = 1 -- filters ghosts who may be lingering in a bed
       )
SELECT csn,
       lv.admission_time   AS admission_dt,
       lv.discharge_time   AS discharge_dt,
       loc.location_string AS hl7_location,
       mrn
FROM census
       LEFT JOIN star.location_visit lv
                 ON census.hv_id = lv.hospital_visit_id
       LEFT JOIN star.location loc
                 ON lv.location_id = loc.location_id
WHERE loc.location_string IN (SELECT loc FROM flow.ward_location) -- LIKE 'T03%%' OR loc.location_string LIKE '%%T06PACU%%' OR loc.location_string LIKE '%%GWB L01 CC%%'
ORDER BY csn, admission_dt
