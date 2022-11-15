-- 2022-06-24t14:26:45
-- query manually checked - seems a good rough approx
-- prob need something like a recent vital sign join to get rid of patients not in hosp
-- query returns ghosts b/c bed and hospital discharge datetime sometimes missing
SELECT
  --vd.location_visit_id
   vd.hospital_visit_id
  ,live_mrn.mrn
  ,cd.lastname
  ,cd.firstname
  ,cd.sex
  ,cd.date_of_birth
  -- ,vd.location_id
  -- ugly HL7 location string
  ,lo.location_string
  ,dept.name
  -- time admitted to that bed/theatre/scan etc.
  ,vo.admission_time hosp_admit_dt
  ,vd.admission_time bed_admit_dt
  -- time discharged from that bed
  ,vd.discharge_time bed_discharge_dt

FROM star.location_visit vd
-- location label
INNER JOIN star.location lo ON vd.location_id = lo.location_id
INNER JOIN star.department dept ON lo.department_id = dept.department_id
INNER JOIN star.hospital_visit vo ON vd.hospital_visit_id = vo.hospital_visit_id
INNER JOIN star.core_demographic cd ON vo.mrn_id = cd.mrn_id
-- get current hospital number
INNER JOIN star.mrn original_mrn ON vo.mrn_id = original_mrn.mrn_id
-- get mrn to live mapping
INNER JOIN star.mrn_to_live mtl ON vo.mrn_id = mtl.mrn_id
-- get live mrn
INNER JOIN star.mrn live_mrn ON mtl.live_mrn_id = live_mrn.mrn_id
WHERE
vo.admission_time IS NOT NULL
AND
vo.discharge_time IS NULL
AND
vo.patient_class = ANY('{INPATIENT,DAY_CASE,EMERGENCY}')
AND
cd.date_of_death IS NULL

-- last few hours
AND
vd.admission_time IS NOT NULL
-- just CURRENT patients
AND
vd.discharge_time IS NULL
-- filter out just ED and Resus or Majors
AND
-- unpacking the HL7 string formatted as
-- Department^Ward^Bed string
--SPLIT_PART(lo.location_string,'^',1) = 'T03'
dept.name LIKE 'UCH%'
-- sort
ORDER BY dept.name, lo.location_string
;
