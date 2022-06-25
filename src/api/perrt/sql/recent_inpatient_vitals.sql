-- 2022-06-24
-- return recent vitals
-- V simple view that finds recent observations
-- for current inpatients in the last few minutes
-- runs within a few seconds

-- return recent vitals
--

-- Example script showing how to work with observations

-- V simple view that finds recent observations
-- for current inpatients in the last few minutes


SELECT
  -- observation details
   ob.visit_observation_id
  -- location details
  ,ward.name
  ,ward.location_string
  -- patient details
  ,ward.mrn
  ,ward.lastname
  ,ward.firstname
  ,ward.sex
  ,ward.date_of_birth
  -- ,vd.location_id
  -- ugly HL7 location string
  ,ward.location_string
  ,ward.name
  -- time admitted to that bed/theatre/scan etc.
  ,ob.hospital_visit_id
  ,ob.observation_datetime

  ,ob.visit_observation_type_id
  ,ot.id_in_application

  ,ob.value_as_real
  ,ob.value_as_text
  ,ob.unit


FROM
  star.visit_observation ob
-- observation look-up
LEFT JOIN
    star.visit_observation_type ot
    ON ob.visit_observation_type_id = ot.visit_observation_type_id
LEFT JOIN
    star.hospital_visit vo
    ON ob.hospital_visit_id = vo.hospital_visit_id
-- subquery to identify only those patients in a certain ward/department
INNER JOIN
    (
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

    ) ward
    ON vo.hospital_visit_id = ward.hospital_visit_id
WHERE
     ob.observation_datetime > NOW() - '30 HOURS'::INTERVAL
AND vo.admission_time IS NOT NULL
AND vo.discharge_time IS NULL
AND vo.patient_class = 'INPATIENT'
AND ot.id_in_application in

  (
   '10'            --'SpO2'                  -- 602063230
  ,'5'            --'BP'                    -- 602063234
  ,'3040109304'   --'Room Air or Oxygen'    -- 602063268
  ,'6'            --'Temp'                  -- 602063248
  ,'8'            --'Pulse'                 -- 602063237
  ,'9'            --'Resp'                  -- 602063257
  ,'6466'         -- Level of consciousness
  ,'28315'        -- NEWS score Scale 1     -- 47175382
  ,'28316'        -- NEWS score Scale 2     -- 47175920
)

ORDER BY ob.observation_datetime DESC
;
