WITH pts AS (
SELECT DISTINCT

    -- p.core_demographic_id

    -- ,mrn.mrn_id
    -- ,mrn_to_live.mrn_id AS mrn_id_alt
     mrn.mrn
    ,mrn.nhs_number

    ,vo.hospital_visit_id
    ,vo.encounter CSN

    ,vo.admission_time hospital_admission_datetime
    -- ,vo.arrival_method
    -- ,vo.patient_class
    -- ,vo.presentation_time
    -- ,vo.source_system

    -- ,p.alive
    ,p.date_of_birth
    -- ,p.date_of_death
    -- ,p.ethnicity
    ,p.firstname
    -- ,p.home_postcode
    ,p.lastname
    -- ,p.middlename
    ,p.sex

FROM star.hospital_visit vo
-- get core_demographic id
LEFT JOIN star.core_demographic p ON vo.mrn_id = p.mrn_id
-- get current MRN
LEFT JOIN star.mrn_to_live ON p.mrn_id = mrn_to_live.mrn_id
LEFT JOIN star.mrn ON mrn_to_live.live_mrn_id = mrn.mrn_id

-- where inpatient
WHERE
  vo.patient_class = 'INPATIENT'
  and
  vo.discharge_time IS NULL
  AND
  vo.admission_time IS NOT NULL
  AND p.alive = true

), res AS (
SELECT
   pts.*
  -- vd.location_visit_id
  ,vd.admission_time bed_admission_datetime
  -- ,vd.location_id
  ,loc.location_string

  ,dept.name
  ,dept.speciality
  ,room.name
  --  ,bed."type"


FROM
  star.location_visit vd
INNER JOIN
  pts
  ON vd.hospital_visit_id = pts.hospital_visit_id
INNER JOIN
  star.location loc
  ON vd.location_id = loc.location_id

LEFT JOIN department dept ON loc.department_id = dept.department_id
LEFT JOIN room room ON loc.room_id = room.room_id
LEFT JOIN bed_state bed_state ON loc.bed_id = bed_state.bed_id
-- NOT JOINING bed_state since this is a long list of attributes (>1 per bed)
--INNER JOIN bed_facility bed ON bed_state.bed_state_id = bed.bed_state_id

WHERE
  vd.discharge_time IS NULL
  AND
  bed_state.is_in_census = true
  AND
  bed_state."status" = 'Active'
  AND
  bed_state.valid_until IS NULL
--  AND
--  vd.location_visit_id IS NOT NULL
)

SELECT * FROM res
ORDER BY res.hospital_visit_id DESC

;
