SELECT ct.name,
COUNT(ct.name)
/*cr.valid_from,
cr.cancelled,
cr.closed_due_to_discharge,
cr.hospital_visit_id*/

FROM star.consultation_type ct
RIGHT JOIN star.consultation_request cr ON ct.consultation_type_id = cr.consultation_type_id 

WHERE cr.valid_from BETWEEN NOW() - '10 DAYS'::INTERVAL AND NOW() 
GROUP BY ct.name
ORDER BY COUNT DESC

LIMIT 2000;