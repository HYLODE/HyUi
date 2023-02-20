SELECT lv.location_visit_id,
    lv.admission_datetime AS admission_time,
    lv.discharge_datetime AS discharge_time,
    lv.discharge_datetime - lv.admission_datetime AS duration,
    lv.hospital_visit_id,
    lv.location_id,
    hv.mrn_id,
    mrn.mrn,
    loc.location_string,
    loc.bed_id,
    dp.name,
    dp.speciality
FROM star.location_visit lv
    LEFT JOIN star.hospital_visit hv ON lv.hospital_visit_id = hv.hospital_visit_id
    LEFT JOIN star.location loc ON lv.location_id = loc.location_id
    LEFT JOIN star.department dp ON loc.department_id = dp.department_id
    LEFT JOIN star.mrn ON hv.mrn_id = mrn.mrn_id
    INNER JOIN (
        SELECT DISTINCT hospital_visit_id
        FROM star.location_visit lv
        WHERE lv.location_id IN { }
    ) surgpts ON surgpts.hospital_visit_id = lv.hospital_visit_id
WHERE lv.admission_datetime::date >= %s::date
    AND lv.admission_datetime::date < %s::date
