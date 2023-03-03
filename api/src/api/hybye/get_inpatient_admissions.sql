SELECT
    DATE (hv.admission_datetime) AS admission_date, COUNT (*)
FROM star.hospital_visit hv
    JOIN star.location_visit lv
ON lv.hospital_visit_id = hv.hospital_visit_id
    JOIN star.location lo
    ON lo.location_id = lv.location_id
    JOIN star.department dpt
    ON dpt.department_id = lo.department_id
WHERE hv.admission_datetime
    > NOW() - INTERVAL ':days DAYS'
  AND
    dpt.name = ANY (:departments)
  AND hv.patient_class = 'INPATIENT'
GROUP BY DATE (hv.admission_datetime)
ORDER BY DATE (hv.admission_datetime) DESC;
