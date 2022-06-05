SELECT --DISTINCT
		
		lbe.lab_battery_element_id, 
		 lbe.lab_battery_id,
		 lbe.lab_test_definition_id,
		 lb.battery_code,
		 lb.battery_name,
		 lo.lab_order_id,
		 lo.lab_battery_id,
		 lo.lab_sample_id,
		 lr.lab_test_definition_id,
		 lr.valid_from,
		 lr.value_as_real, 
		 lr.value_as_text,
		 -- lr.value_as_bytes,
		 --lr.units --,
		 ltd.test_lab_code tlc,
		mrn.mrn,
		hv.hospital_visit_id csn,
		hv.admission_time,
		hv.discharge_time,
		hv.arrival_method,
		hv.discharge_destination,
		hv.discharge_disposition,
		cd.date_of_birth,
		cd.date_of_death,
		cd.ethnicity,
		cd.sex,
		 
		 -- Pick out if a variant is stated
		 CASE
		 WHEN lr.value_as_text LIKE '%%omicron%%' THEN 'omicron'
		 WHEN lr.value_as_text LIKE '%%OMICRON%%' THEN 'omicron'
		 WHEN lr.value_as_text LIKE '%%Omicron%%' THEN 'omicron'
		 WHEN lr.value_as_text LIKE '%%B.1.1.529%%' THEN 'omicron'
		 WHEN lr.value_as_text LIKE '%%DELTA%%' THEN 'delta'
		 WHEN lr.value_as_text LIKE '%%delta%%' THEN 'delta'
		 WHEN lr.value_as_text LIKE '%%Delta%%' THEN 'delta'
		 END AS variant,
		 
		 AGE(lr.valid_from, hv.admission_time) AS time_to_test
		
		FROM star.lab_battery_element lbe 
		
		-- Join all the relevant tables together
		INNER JOIN star.lab_battery lb ON lbe.lab_battery_id = lb.lab_battery_id
		INNER JOIN star.lab_order lo ON lb.lab_battery_id = lo.lab_battery_id--
		INNER JOIN star.lab_result lr ON lo.lab_order_id = lr.lab_order_id
		INNER JOIN star.lab_test_definition ltd ON lbe.lab_test_definition_id = ltd.lab_test_definition_id
		INNER JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id
		INNER JOIN star.mrn mrn ON hv.mrn_id = mrn.mrn_id
		INNER JOIN star.core_demographic cd ON mrn.mrn_id = cd.mrn_id
		
		-- Choose some very recent patients
		WHERE lr.valid_from BETWEEN {start_date} AND {end_date}
		AND (ltd.test_lab_code LIKE '%%COV%%' OR ltd.test_lab_code IN ('RXCC', 'CCOC', 'NCVC', 'NCVL', 'NCVP', 'RCVC', 'CVOC')) -- covid tests
		AND ltd.test_lab_code NOT LIKE 'GCOV' -- antibody tests
		
		-- Lots of random text in these - choose only patients with positive tests (POSITIVE or RNA DECTECTED)
		AND (lr.value_as_text LIKE '%%posi%%' OR lr.value_as_text LIKE '%%POSI%%' OR lr.value_as_text LIKE '%%DETECT%%' OR lr.value_as_text LIKE '%%detect%%'
            OR lr.value_as_text LIKE '%%omicron%%' OR lr.value_as_text LIKE '%%OMICRON%%' OR lr.value_as_text LIKE '%%Omicron%%' OR lr.value_as_text LIKE '%%B.1.1.529%%' 
            OR lr.value_as_text LIKE '%%DELTA%%' OR lr.value_as_text LIKE '%%delta%%' OR lr.value_as_text LIKE '%%Delta%%' OR lr.value_as_text LIKE '%%B.1.617.2%%' 
            OR lr.value_as_text LIKE '%%Alpha%%' OR lr.value_as_text LIKE '%%alpha%%' OR lr.value_as_text LIKE '%%ALPHA%%' OR lr.value_as_text LIKE '%%B.1.1.7%%')
    
        -- bin all indeterminate or presumptive tests
		AND lr.value_as_text NOT LIKE '%%indeterminate%%' 
		AND lr.value_as_text NOT LIKE '%%INDETERMINATE%%'
		AND lr.value_as_text NOT LIKE '%%presumptive%%' 
		AND lr.value_as_text NOT LIKE '%%preumptive%%'
		
		-- They only seem to write NOT when NOT DETECTED or NOT POSITIVE (note case sensitive)
		AND lr.value_as_text NOT LIKE '%%NOT%%'
		
		-- Bin all the cases where the sample wasn't good enought
		AND lr.value_as_text NOT LIKE '%%Please repeat the sample%%'
		AND lr.value_as_text NOT LIKE '%%Please repeat thesample%%'
		AND lr.value_as_text NOT LIKE '%%No internal control%%'
		
		-- Bin references to antibodies
		AND lr.value_as_text NOT LIKE '%%total Ab%%'
		AND lr.value_as_text NOT LIKE '%%Anti-N%%'
    
        -- Bin specific one for RCVC
        AND lr.value_as_text NOT LIKE '%%Seasonal CoV OC43 detected ONLY%%'
		
		-- Choose only patients admitted as an inpatient (NOTE this will capture patients seen in ED)
		AND hv.patient_class IN ('INPATIENT', 'EMERGENCY')
        AND hv.admission_time IS NOT NULL