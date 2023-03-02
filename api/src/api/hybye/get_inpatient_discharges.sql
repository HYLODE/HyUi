SELECT
  DATE(hv.discharge_datetime) AS discharge_date,
  COUNT(*)
FROM star.hospital_visit hv
WHERE hv.discharge_datetime > NOW() - INTERVAL ':days DAYS'
AND hv.patient_class = 'INPATIENT'
GROUP BY DATE(hv.discharge_datetime)
ORDER BY DATE(hv.discharge_datetime) DESC
;
