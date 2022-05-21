WITH 
q1 AS (
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
,cr.status_change_time
,cr.hospital_visit_id
,ct.code
,ct.name
,loc.admission_time
,loc.discharge_time
,loc.name AS dept_name

FROM star.consultation_request cr
LEFT JOIN star.consultation_type ct ON cr.consultation_type_id = ct.consultation_type_id

LEFT JOIN (
	SELECT 
	*
	FROM 
	star.location_visit lv
	LEFT JOIN star.location lo ON lv.location_id = lo.location_id
	LEFT JOIN star.department de ON lo.department_id = de.department_id
	WHERE lv.admission_time >= NOW() - INTERVAL '24 HOURS'
) loc ON cr.hospital_visit_id = loc.hospital_visit_id


LEFT JOIN star.hospital_visit hv ON cr.hospital_visit_id = hv.hospital_visit_id 
LEFT JOIN star.core_demographic cd ON hv.mrn_id = cd.mrn_id
LEFT JOIN star.mrn ON cd.mrn_id = mrn.mrn_id

WHERE 
	loc.speciality = 'Accident & Emergency'
--	AND 
--	cr.closed_due_to_discharge = false
--	AND
--	cr.cancelled = false
ORDER BY 
cr.consultation_request_id
),
q2 AS (
-- now number these by descending location admit time
-- so '1' represents the current location of that patient
SELECT
 *
,row_number() over (partition BY q1.hospital_visit_id ORDER BY q1.admission_time DESC) loc_i 
FROM q1
)
-- now return the consult and the most recent location
SELECT 
-- select only those fields you wish to model and validate
 q2.firstname
,q2.lastname
,q2.date_of_birth
,q2.mrn
,q2.nhs_number
,q2.valid_from
,q2.cancelled
,q2.closed_due_to_discharge
,q2.comments
,q2.scheduled_datetime
,q2.status_change_time
,q2.name
,q2.admission_time
,q2.discharge_time
,q2.dept_name
FROM q2
WHERE loc_i = 1
 ;