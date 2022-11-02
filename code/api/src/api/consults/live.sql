-- src/api/consults/live.sql
WITH
consults AS (
-- get all details on consultation requests
-- regardless of where the patient is now
SELECT

 cd.firstname
,cd.lastname
,cd.date_of_birth
,mrn.mrn
,mrn.nhs_number

,cr.consultation_request_id
,cr.valid_from
,cr.cancelled
,cr.closed_due_to_discharge
,cr.comments
,cr.scheduled_datetime
,cr.status_change_datetime
,cr.hospital_visit_id
,ct.code
,ct.name
,loc.admission_datetime
,loc.discharge_datetime
,loc.location_string
,loc.name AS dept_name

FROM star.consultation_request cr
LEFT JOIN star.consultation_type ct ON cr.consultation_type_id = ct.consultation_type_id

INNER JOIN (
	SELECT
	*
	FROM
	star.location_visit lv
	LEFT JOIN star.location lo ON lv.location_id = lo.location_id
	LEFT JOIN star.department de ON lo.department_id = de.department_id
--	WHERE lv.admission_datetime >= NOW() - INTERVAL '24 HOURS'
	WHERE lv.discharge_datetime IS NULL
) loc ON cr.hospital_visit_id = loc.hospital_visit_id


LEFT JOIN star.hospital_visit hv ON cr.hospital_visit_id = hv.hospital_visit_id
LEFT JOIN star.core_demographic cd ON hv.mrn_id = cd.mrn_id
LEFT JOIN star.mrn ON cd.mrn_id = mrn.mrn_id

WHERE
--	loc.speciality = 'Accident & Emergency'
--	AND
	hv.patient_class IN ('INPATIENT', 'EMERGENCY')
	AND
	cr.closed_due_to_discharge = false
	AND
	cr.cancelled = false
	AND
	cr.scheduled_datetime > NOW() - INTERVAL '7 DAYS'
ORDER BY
cr.consultation_request_id
),
loc_now AS (
-- now number these by descending location admit time
-- so '1' represents the current location of that patient
SELECT
 *
,row_number() over (partition BY consults.hospital_visit_id ORDER BY consults.admission_datetime DESC) loc_i
FROM consults
)
-- now return the consult and the most recent location
SELECT
-- select only those fields you wish to model and validate
 loc_now.firstname
,loc_now.lastname
,loc_now.date_of_birth
,loc_now.mrn
,loc_now.nhs_number
,loc_now.valid_from
--,loc_now.cancelled
--,loc_now.closed_due_to_discharge
,loc_now.comments
,loc_now.scheduled_datetime
,loc_now.status_change_datetime
,loc_now.name
,loc_now.admission_datetime
,loc_now.discharge_datetime
,loc_now.dept_name
,loc_now.location_string
FROM loc_now
WHERE loc_i = 1
ORDER BY loc_now.scheduled_datetime ASC
 ;
