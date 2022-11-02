-- Pulling additional data for patients on wards
-- D Stein 2022

-- First list all possible ED locations:
WITH ed_locations AS (
SELECT DISTINCT * FROM star.location

-- Possible ED strings - either 'ED^...' or null^ED ... or ED^UCHED or SDEC present
WHERE (SPLIT_PART(location_string , '^', 1) = 'ED'
OR SPLIT_PART(location_string , '^', 2) LIKE 'ED %%'
OR location_string LIKE '%%SDEC%%'
OR SPLIT_PART(location_string, '^', 2) LIKE 'UCHED%%')

-- Don't want to inclued eastman dental or national ENT hospital
AND location_string NOT LIKE '%%ENTED%%'
AND location_string NOT LIKE '%%EDH%%'
ORDER BY location_string),


-- Now pull the surgical referrals
surgical AS (
SELECT DISTINCT ON (cr.hospital_visit_id) cr.hospital_visit_id,
cr.valid_from,
ct.name

FROM star.consultation_type ct
RIGHT JOIN star.consultation_request cr ON ct.consultation_type_id = cr.consultation_type_id
INNER JOIN star.location_visit lv ON cr.hospital_visit_id = lv.hospital_visit_id
INNER JOIN star.location loc ON lv.location_id = loc.location_id

WHERE ct.name IN ('Inpatient consult to General Surgery',
						'Inpatient consult to Urology',
						'Inpatient consult to Vascular Surgery',
						'Inpatient consult to ENT',
						'Inpatient consult to Oral & Maxillofacial Surgery',
						'Inpatient consult to Stoma Care Nursing')
AND cr.cancelled = 'false'
AND cr.closed_due_to_discharge = 'false'
AND cr.scheduled_datetime >= lv.admission_time
AND (cr.valid_from <= lv.discharge_time OR lv.discharge_time IS NULL)
AND loc.location_string IN (SELECT location_string FROM ed_locations)
ORDER BY cr.hospital_visit_id, cr.valid_from, ct.name DESC),


-- Now pull the medical referrals (note including haem and onc here)
medical AS (
SELECT DISTINCT ON (cr.hospital_visit_id) cr.hospital_visit_id,
cr.valid_from,
ct.name

FROM star.consultation_type ct
RIGHT JOIN star.consultation_request cr ON ct.consultation_type_id = cr.consultation_type_id
INNER JOIN star.location_visit lv ON cr.hospital_visit_id = lv.hospital_visit_id
INNER JOIN star.location loc ON lv.location_id = loc.location_id

WHERE ct.name IN ('Inpatient consult to Acute Medicine',
						'ED consult to Ambulatory Medicine',
						'Inpatient consult to Internal Medicine',
						'Inpatient consult to Haematology',
						'Inpatient consult to Cardiology',
						'Inpatient consult to Renal Medicine',
						'Inpatient consult to Care of the Elderly',
						'Inpatient consult to Tropical Medicine',
						'Inpatient consult to Endocrinology',
						'Inpatient consult to Rheumatology',
						'Inpatient consult to Nuclear Medicine',
						'Inpatient consult to Oncology',
						'Inpatient consult to Adult Endocrine & Diabetes',
						'Inpatient consult to Respiratory Medicine',
						'Inpatient consult to Gastroenterology'
						)
AND cr.cancelled = 'false'
AND cr.closed_due_to_discharge = 'false'
AND cr.valid_from >= lv.admission_time
AND (cr.valid_from <= lv.discharge_time OR lv.discharge_time IS NULL)
AND loc.location_string IN (SELECT location_string FROM ed_locations)
ORDER BY cr.hospital_visit_id, cr.valid_from, ct.name DESC),


-- Now pull O+G
gynae AS (
SELECT DISTINCT ON (cr.hospital_visit_id) cr.hospital_visit_id,
ct.name,
cr.valid_from

FROM star.consultation_type ct
RIGHT JOIN star.consultation_request cr ON ct.consultation_type_id = cr.consultation_type_id
INNER JOIN star.location_visit lv ON cr.hospital_visit_id = lv.hospital_visit_id
INNER JOIN star.location loc ON lv.location_id = loc.location_id


WHERE ct.name IN ('Inpatient consult to Gynaecology', 'Inpatient consult to Obstetrics')
AND cr.cancelled = 'false'
AND cr.closed_due_to_discharge = 'false'
AND cr.valid_from >= lv.admission_time
AND (cr.valid_from <= lv.discharge_time OR lv.discharge_time IS NULL)
AND loc.location_string IN (SELECT location_string FROM ed_locations)
ORDER BY cr.hospital_visit_id, cr.valid_from, ct.name DESC),



-- Now pull ortho referrals
ortho AS (
SELECT DISTINCT ON (cr.hospital_visit_id) cr.hospital_visit_id,
 ct.name,
cr.valid_from

FROM star.consultation_type ct
RIGHT JOIN star.consultation_request cr ON ct.consultation_type_id = cr.consultation_type_id
INNER JOIN star.location_visit lv ON cr.hospital_visit_id = lv.hospital_visit_id
INNER JOIN star.location loc ON lv.location_id = loc.location_id

WHERE ct.name = 'Inpatient consult to Orthopedic Surgery'
AND cr.cancelled = 'false'
AND cr.closed_due_to_discharge = 'false'
AND cr.valid_from >= lv.admission_time
AND (cr.valid_from <= lv.discharge_time OR lv.discharge_time IS NULL)
AND loc.location_string IN (SELECT location_string FROM ed_locations)
ORDER BY cr.hospital_visit_id, cr.valid_from, ct.name DESC),



-- Here we are pulling haemonc referrals
oncology AS (
SELECT DISTINCT ON (cr.hospital_visit_id) cr.hospital_visit_id,
ct.name,
cr.valid_from

FROM star.consultation_type ct
RIGHT JOIN star.consultation_request cr ON ct.consultation_type_id = cr.consultation_type_id
INNER JOIN star.location_visit lv ON cr.hospital_visit_id = lv.hospital_visit_id
INNER JOIN star.location loc ON lv.location_id = loc.location_id

WHERE ct.name IN ('Inpatient consult to Oncology', 'Inpatient consult to Haematology')
AND cr.cancelled = 'false'
AND cr.closed_due_to_discharge = 'false'
AND cr.valid_from >= lv.admission_time
AND (cr.valid_from <= lv.discharge_time OR lv.discharge_time IS NULL)
AND loc.location_string IN (SELECT location_string FROM ed_locations)
ORDER BY cr.hospital_visit_id, cr.valid_from, ct.name DESC),

-- Now pull some other things that we are interested in
	dnacpr AS (
		SELECT DISTINCT ON (ad.hospital_visit_id) ad.hospital_visit_id,
		ad.valid_from,
		adt.name

		FROM star.advance_decision ad

		JOIN star.advance_decision_type adt
		ON adt.advance_decision_type_id = ad.advance_decision_type_id

	  	WHERE ad.hospital_visit_id IN ({hv_ids})
	  	ORDER BY ad.hospital_visit_id, ad.valid_from DESC
	),

-- Now pull first location
	emergency_admission AS (SELECT DISTINCT ON (lv.hospital_visit_id) lv.hospital_visit_id,
	loc.location_string,

	SPLIT_PART(loc.location_string, '^', 1) ward_raw

	FROM star.location_visit lv
	LEFT JOIN star.location loc ON lv.location_id = loc.location_id
	WHERE lv.hospital_visit_id IN ({hv_ids})
	AND loc.location_string IN (SELECT location_string FROM ed_locations)
	ORDER BY lv.hospital_visit_id, lv.admission_time ASC),


-- Now pull whether they have recently been in theatres
	recent_surgery AS (SELECT DISTINCT ON (lv.hospital_visit_id) lv.hospital_visit_id,
	loc.location_string,

	SPLIT_PART(loc.location_string, '^', 1) ward_raw

	FROM star.location_visit lv
	LEFT JOIN star.location loc ON lv.location_id = loc.location_id
	WHERE lv.hospital_visit_id IN ({hv_ids})

	--Choose theatres
	AND SPLIT_PART(loc.location_string, '^', 1) IN ('THP3', 'T02THR')

	--Make sure they were only in theatres in the past
	AND lv.discharge_time <= {end_time}
	AND lv.discharge_time >= {end_time} - '{horizon}'::INTERVAL

	ORDER BY lv.hospital_visit_id, lv.admission_time ASC),

-- Now pull whether they have ever been in theatres
	ever_surgery AS (SELECT DISTINCT ON (lv.hospital_visit_id) lv.hospital_visit_id,
	loc.location_string,

	SPLIT_PART(loc.location_string, '^', 1) ward_raw

	FROM star.location_visit lv
	LEFT JOIN star.location loc ON lv.location_id = loc.location_id
	WHERE lv.hospital_visit_id IN ({hv_ids})

	--Choose theatres
	AND SPLIT_PART(loc.location_string, '^', 1) IN ('THP3', 'T02THR')

	--Make sure they were only in theatres in the past
	AND lv.admission_time <= {end_time}
	ORDER BY lv.hospital_visit_id, lv.admission_time ASC),

-- Recent ICU discharge
	recent_ICU AS (SELECT DISTINCT ON (lv.hospital_visit_id) lv.hospital_visit_id,
	loc.location_string,

	SPLIT_PART(loc.location_string, '^', 1) ward_raw

	FROM star.location_visit lv
	LEFT JOIN star.location loc ON lv.location_id = loc.location_id
	WHERE lv.hospital_visit_id IN ({hv_ids})

	--Choose theatres
	AND ( loc.location_string LIKE 'T03%%' OR
			loc.location_string LIKE '%%T06PACU%%' OR
			loc.location_string LIKE '%%GWB L01W%%')

	--Make sure they were only in theatres in the past
	AND lv.discharge_time <= {end_time}
	AND lv.discharge_time >= {end_time} - '{horizon}'::INTERVAL

	ORDER BY lv.hospital_visit_id, lv.admission_time ASC)


SELECT hv.hospital_visit_id,
hv.admission_time,
surgical.valid_from surg_ref,
medical.valid_from med_ref,
gynae.valid_from OG_ref,
oncology.valid_from haem_onc_ref,
ortho.valid_from ortho_ref,

	-- Resus status
    dnacpr.name AS dnacpr

    --Were they elective?
	 ,emergency_admission.ward_raw first_ward

	 --Have they had surgery
	 ,recent_surgery.ward_raw recent_surgery
	 ,ever_surgery.ward_raw ever_surgery

	 -- Recent ICU admission
	 ,recent_ICU.location_string recent_icu

FROM star.hospital_visit hv

-- Now add resus status
FULL JOIN dnacpr ON hv.hospital_visit_id = dnacpr.hospital_visit_id

-- First location (did they come through ED?)
FULL JOIN emergency_admission ON hv.hospital_visit_id = emergency_admission.hospital_visit_id

-- Have they had surgery
FULL JOIN recent_surgery ON hv.hospital_visit_id = recent_surgery.hospital_visit_id
FULL JOIN ever_surgery ON hv.hospital_visit_id = ever_surgery.hospital_visit_id

-- Recent ICU admission
FULL JOIN recent_icu ON hv.hospital_visit_id = recent_icu.hospital_visit_id

-- What different referrals have they had (ever)?
FULL JOIN medical ON hv.hospital_visit_id = medical.hospital_visit_id
FULL JOIN surgical ON hv.hospital_visit_id = surgical.hospital_visit_id
FULL JOIN gynae ON hv.hospital_visit_id = gynae.hospital_visit_id
FULL JOIN oncology ON hv.hospital_visit_id = oncology.hospital_visit_id
FULL JOIN ortho ON hv.hospital_visit_id = ortho.hospital_visit_id

WHERE hv.hospital_visit_id IN ({hv_ids})

ORDER BY hv.hospital_visit_id;
