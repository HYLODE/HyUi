-- Identify recent consults arising from ED
SELECT DISTINCT
 cr.valid_from
,cr.cancelled
,cr.closed_due_to_discharge
,cr.comments
,cr.scheduled_datetime
,cr.status_change_time
,cr.hospital_visit_id
,ct.code
,ct.name
-- ,de.name
FROM star.consultation_request cr
LEFT JOIN star.consultation_type ct ON cr.consultation_type_id = ct.consultation_type_id
LEFT JOIN star.location_visit lv ON cr.hospital_visit_id = lv.hospital_visit_id
LEFT JOIN star.location lo ON lv.location_id = lo.location_id
LEFT JOIN star.department de ON lo.department_id = de.department_id
WHERE 
	de.speciality = 'Accident & Emergency'
	AND
	cr.valid_from >= NOW() - INTERVAL '36 HOURS'
ORDER BY cr.valid_from DESC
--LIMIT 3
 ;