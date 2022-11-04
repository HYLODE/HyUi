--Pull most common consults - D Stein 2022

SELECT ct.name,
cr.hospital_visit_id,
cr.scheduled_datetime valid_from

FROM star.consultation_type ct
RIGHT JOIN star.consultation_request cr ON ct.consultation_type_id = cr.consultation_type_id

--WHERE cr.valid_from BETWEEN NOW() - '10 DAYS'::INTERVAL AND NOW()
WHERE ct.name IN (
 'Inpatient consult to PERRT',
 'Inpatient Consult to Symptom Control and Palliative Care',
 'Inpatient Consult to Transforming end of life care team',
 'Inpatient consult to Intensivist',
 'Inpatient consult to Social Work')

AND cr.cancelled = 'false'
AND cr.closed_due_to_discharge = 'false'

AND cr.scheduled_datetime BETWEEN {end_time} - '{horizon}'::INTERVAL AND {end_time}

AND cr.hospital_visit_id IN ({hv_ids})
ORDER BY cr.hospital_visit_id DESC
