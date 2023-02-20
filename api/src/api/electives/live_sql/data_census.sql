SELECT COUNT (DISTINCT hv.mrn_id)
FROM star.location_visit lv
  LEFT JOIN star.hospital_visit hv ON lv.hospital_visit_id = hv.hospital_visit_id
  LEFT JOIN star.location loc ON lv.location_id = loc.location_id
  LEFT JOIN star.department dp ON loc.department_id = dp.department_id
WHERE dp.speciality = %s
  AND (
    DATE(lv.discharge_datetime) > %s
    OR lv.discharge_datetime IS NULL
  )
  AND DATE(lv.admission_datetime) <= %s
