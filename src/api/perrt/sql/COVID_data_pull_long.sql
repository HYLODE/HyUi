-- Query by D Stein 2022 to pull covid data for Nish

-- First pull patients with positive covid swabs

WITH cov AS (
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
		WHERE hv.hospital_visit_id IN ({csns})
		
		--WHERE lr.stored_from >= NOW() - '1 days'::INTERVAL
		--AND lr.stored_from <= NOW() - '20 days'::INTERVAL
		AND (ltd.test_lab_code LIKE '%%COV%%' OR ltd.test_lab_code = 'RXCC') -- covid tests
		AND ltd.test_lab_code NOT LIKE 'GCOV' -- antibody tests
		
		-- Lots of random text in these - choose only patients with positive tests (POSITIVE or RNA DECTECTED)
		AND (lr.value_as_text LIKE '%%posi%%' OR lr.value_as_text LIKE '%%POSI%%' OR lr.value_as_text LIKE '%%DETECT%%' OR lr.value_as_text LIKE '%%detect%%')
		AND lr.value_as_text NOT LIKE '%%indeterminate%%' -- bin all indeterminate or presumptive tests
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
		
		-- Choose only patients admitted as an inpatient (NOTE this will capture patients seen in ED)
		AND hv.patient_class = 'INPATIENT'
      AND hv.admission_time IS NOT NULL
	),
	
	-- For each patient where there is a positive covid swab, we can then pull the first observation
	bp AS (
	
		-- This pulls only one observation per admission, but and because its valid from ASC its the first observation
		SELECT DISTINCT ON (ob.hospital_visit_id) ob.hospital_visit_id, 
		ob.valid_from, 
		ob.value_as_real,
		ob.value_as_text,
		ob.unit,
		ot.id_in_application,
		
		-- State whether non-invasive or arterial line
		CASE WHEN id_in_application = '5' THEN 'NIBP'
		WHEN id_in_application = '301260' THEN 'ALine'
		END AS art_line
		
		FROM
		star.visit_observation ob
		
		LEFT JOIN
	  		star.visit_observation_type ot
	  		ON ob.visit_observation_type_id = ot.visit_observation_type_id
	  		
	  	-- Only patients which are in our list of positive patients
	  	WHERE ob.hospital_visit_id IN (SELECT csn FROM cov)
	  	
	  	-- These are the codes for NIBP and art line respectively
	  	AND ot.id_in_application IN ('5', '301260')
	  	ORDER BY ob.hospital_visit_id, ob.valid_from ASC
	),
	
	--Resp rate
	rr AS (
		SELECT DISTINCT ON (ob.hospital_visit_id) ob.hospital_visit_id, 
		ob.valid_from, 
		ob.value_as_real,
		ob.value_as_text,
		ob.unit,
		ot.id_in_application
		
	FROM
		star.visit_observation ob
		
		LEFT JOIN
	  		star.visit_observation_type ot
	  		ON ob.visit_observation_type_id = ot.visit_observation_type_id
	  		
	  	-- Only patients which are in our list of positive patients
	  	WHERE ob.hospital_visit_id IN (SELECT csn FROM cov)
	  	AND ot.id_in_application IN ('9')
	  	ORDER BY ob.hospital_visit_id, ob.valid_from ASC
	),
	
	-- Oxygen saturations
	spo2 AS (
		SELECT DISTINCT ON (ob.hospital_visit_id) ob.hospital_visit_id, 
		ob.valid_from, 
		ob.value_as_real,
		ob.value_as_text,
		ob.unit,
		ot.id_in_application
		
		FROM
		star.visit_observation ob
		
		LEFT JOIN
	  		star.visit_observation_type ot
	  		ON ob.visit_observation_type_id = ot.visit_observation_type_id
	  		
	  	-- Only patients which are in our list of positive patients
	  	WHERE ob.hospital_visit_id IN (SELECT csn FROM cov)
	  	AND ot.id_in_application IN ('10')
	  	ORDER BY ob.hospital_visit_id, ob.valid_from ASC
	),
	
	-- FiO2
	fio2 AS (
		SELECT DISTINCT ON (ob.hospital_visit_id) ob.hospital_visit_id, 
		ob.valid_from, 
		ob.value_as_real,
		ob.value_as_text,
		ob.unit,
		ot.id_in_application
		
		FROM
		star.hospital_visit hv
		
		INNER JOIN
		star.visit_observation ob ON hv.hospital_visit_id = ob.hospital_visit_id
			
		LEFT JOIN
	  		star.visit_observation_type ot
	  		ON ob.visit_observation_type_id = ot.visit_observation_type_id
	  		
	  	WHERE hv.hospital_visit_id IN (SELECT csn FROM cov)
	  	AND ot.id_in_application IN ('301550')
	  	ORDER BY ob.hospital_visit_id, ob.valid_from ASC
	),
	
	-- Oxygen Flow rate
	o2_flow AS (
		SELECT DISTINCT ON (ob.hospital_visit_id) ob.hospital_visit_id, 
		ob.valid_from, 
		ob.value_as_real,
		ob.value_as_text,
		ob.unit,
		ot.id_in_application
		
		FROM
		star.visit_observation ob
		
		LEFT JOIN
	  		star.visit_observation_type ot
	  		ON ob.visit_observation_type_id = ot.visit_observation_type_id
	  		
	  	-- Only patients which are in our list of positive patients
	  	WHERE ob.hospital_visit_id IN (SELECT csn FROM cov)
	  	AND ot.id_in_application IN ('250026')
	  	ORDER BY ob.hospital_visit_id, ob.valid_from ASC
	),
	
	gcs AS (
		SELECT DISTINCT ON (ob.hospital_visit_id) ob.hospital_visit_id, 
		ob.valid_from, 
		ob.value_as_real,
		ob.value_as_text,
		ob.unit,
		ot.id_in_application
		
		FROM
		star.visit_observation ob
		
		LEFT JOIN
	  		star.visit_observation_type ot
	  		ON ob.visit_observation_type_id = ot.visit_observation_type_id
	  		
	  	-- Only patients which are in our list of positive patients
	  	WHERE ob.hospital_visit_id IN (SELECT csn FROM cov)
	  	AND ot.id_in_application IN ('401001')
	  	ORDER BY ob.hospital_visit_id, ob.valid_from ASC
	),
	
	acvpu AS (
		SELECT DISTINCT ON (ob.hospital_visit_id) ob.hospital_visit_id, 
		ob.valid_from, 
		ob.value_as_real,
		ob.value_as_text,
		ob.unit,
		ot.id_in_application
		
		FROM
		star.visit_observation ob
		
		LEFT JOIN
	  		star.visit_observation_type ot
	  		ON ob.visit_observation_type_id = ot.visit_observation_type_id
	  		
	  	-- Only patients which are in our list of positive patients
	  	WHERE ob.hospital_visit_id IN (SELECT csn FROM cov)
	  	AND ot.id_in_application IN ('6466')
	  	ORDER BY ob.hospital_visit_id, ob.valid_from ASC
	),
	
	temperature AS (
		SELECT DISTINCT ON (ob.hospital_visit_id) ob.hospital_visit_id, 
		ob.valid_from, 
		ob.value_as_real,
		ob.value_as_text,
		ob.unit,
		ot.id_in_application
		
		FROM
		star.visit_observation ob
		
		LEFT JOIN
	  		star.visit_observation_type ot
	  		ON ob.visit_observation_type_id = ot.visit_observation_type_id
	  		
	  	-- Only patients which are in our list of positive patients
	  	WHERE ob.hospital_visit_id IN (SELECT csn FROM cov)
	  	AND ot.id_in_application IN ('6')
	  	ORDER BY ob.hospital_visit_id, ob.valid_from ASC
	),
	
	admission_oxygen AS (
		SELECT DISTINCT ON (ob.hospital_visit_id) ob.hospital_visit_id, 
		ob.valid_from, 
		ob.value_as_real,
		ob.value_as_text,
		ob.unit,
		ot.id_in_application
		
		FROM
		star.visit_observation ob
		
		LEFT JOIN
	  		star.visit_observation_type ot
	  		ON ob.visit_observation_type_id = ot.visit_observation_type_id
	  		
	  	-- Only patients which are in our list of positive patients
	  	WHERE ob.hospital_visit_id IN (SELECT csn FROM cov)
	  	AND ot.id_in_application IN ('3040109305')
	  	ORDER BY ob.hospital_visit_id, ob.valid_from ASC
	),
	
	dnacpr AS (
		SELECT DISTINCT ON (ad.hospital_visit_id) ad.hospital_visit_id, 
		ad.valid_from,
		adt.name
		
		FROM star.advance_decision ad 

		JOIN star.advance_decision_type adt
		ON adt.advance_decision_type_id = ad.advance_decision_type_id
	  		
	  	WHERE ad.hospital_visit_id IN (SELECT csn FROM cov)
	  	ORDER BY ad.hospital_visit_id, ad.valid_from DESC
	),
	
	ddimer AS (
		SELECT DISTINCT ON (lo.hospital_visit_id) lo.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id

		WHERE def.test_lab_code = 'TDDI'
		AND lo.hospital_visit_id IN (SELECT csn FROM cov)
	  	ORDER BY lo.hospital_visit_id, res.valid_from ASC
	),
	
	albumin AS (
		SELECT DISTINCT ON (lo.hospital_visit_id) lo.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id

		WHERE def.test_lab_code = 'ALB'
		AND lo.hospital_visit_id IN (SELECT csn FROM cov)
	  	ORDER BY lo.hospital_visit_id, res.valid_from ASC
	),
	
	creat AS (
		SELECT DISTINCT ON (lo.hospital_visit_id) lo.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id

		WHERE def.test_lab_code = 'CREA'
		AND lo.hospital_visit_id IN (SELECT csn FROM cov)
	  	ORDER BY lo.hospital_visit_id, res.valid_from ASC
	),
	
	crp AS (
		SELECT DISTINCT ON (lo.hospital_visit_id) lo.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id

		WHERE def.test_lab_code = 'CRP'
		AND lo.hospital_visit_id IN (SELECT csn FROM cov)
	  	ORDER BY lo.hospital_visit_id, res.valid_from ASC
	),
	
	ferritin AS (
		SELECT DISTINCT ON (lo.hospital_visit_id) lo.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id

		WHERE def.test_lab_code = 'FERR'
		AND lo.hospital_visit_id IN (SELECT csn FROM cov)
	  	ORDER BY lo.hospital_visit_id, res.valid_from ASC
	),
	
	bili AS (
		SELECT DISTINCT ON (lo.hospital_visit_id) lo.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id

		WHERE def.test_lab_code = 'BILI'
		AND lo.hospital_visit_id IN (SELECT csn FROM cov)
	  	ORDER BY lo.hospital_visit_id, res.valid_from ASC
	),
	
	trop AS (
		SELECT DISTINCT ON (lo.hospital_visit_id) lo.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
				
		WHERE def.test_lab_code = 'HTRT'
		AND lo.hospital_visit_id IN (SELECT csn FROM cov)
	  	ORDER BY lo.hospital_visit_id, res.valid_from ASC
	),
	
	hb AS (
		SELECT DISTINCT ON (lo.hospital_visit_id) lo.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id

		WHERE def.test_lab_code = 'HBGL'
		AND lo.hospital_visit_id IN (SELECT csn FROM cov)
	  	ORDER BY lo.hospital_visit_id, res.valid_from ASC
	),
	
	lymph AS (
		SELECT DISTINCT ON (lo.hospital_visit_id) lo.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id

		WHERE def.test_lab_code = 'LY'
		AND lo.hospital_visit_id IN (SELECT csn FROM cov)
	  	ORDER BY lo.hospital_visit_id, res.valid_from ASC
	),
	
	neut AS (
		SELECT DISTINCT ON (lo.hospital_visit_id) lo.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id

		WHERE def.test_lab_code = 'NE'
		AND lo.hospital_visit_id IN (SELECT csn FROM cov)
	  	ORDER BY lo.hospital_visit_id, res.valid_from ASC
	),
	
	plt AS (
		SELECT DISTINCT ON(lo.hospital_visit_id) lo.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id

		WHERE def.test_lab_code = 'PLT'
		AND lo.hospital_visit_id IN (SELECT csn FROM cov)
	  	ORDER BY lo.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d1 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		AND AGE(hv.admission_time, res.valid_from)  <=  '1 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d2 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND AGE(hv.admission_time, res.valid_from)  >=  '1 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d3 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		--AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND res.valid_from BETWEEN hv.admission_time + '2 days'::INTERVAL AND hv.admission_time + '3 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d4 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		--AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND res.valid_from BETWEEN hv.admission_time + '3 days'::INTERVAL AND hv.admission_time + '4 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d5 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		--AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND res.valid_from BETWEEN hv.admission_time + '4 days'::INTERVAL AND hv.admission_time + '5 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d6 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		--AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND res.valid_from BETWEEN hv.admission_time + '5 days'::INTERVAL AND hv.admission_time + '6 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d7 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		--AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND res.valid_from BETWEEN hv.admission_time + '6 days'::INTERVAL AND hv.admission_time + '7 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d8 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		--AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND res.valid_from BETWEEN hv.admission_time + '7 days'::INTERVAL AND hv.admission_time + '8 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d9 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		--AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND res.valid_from BETWEEN hv.admission_time + '8 days'::INTERVAL AND hv.admission_time + '9 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d10 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		--AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND res.valid_from BETWEEN hv.admission_time + '9 days'::INTERVAL AND hv.admission_time + '10 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d11 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		--AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND res.valid_from BETWEEN hv.admission_time + '10 days'::INTERVAL AND hv.admission_time + '11 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d12 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		--AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND res.valid_from BETWEEN hv.admission_time + '11 days'::INTERVAL AND hv.admission_time + '12 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d13 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		--AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND res.valid_from BETWEEN hv.admission_time + '12 days'::INTERVAL AND hv.admission_time + '13 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d14 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		--AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND res.valid_from BETWEEN hv.admission_time + '13 days'::INTERVAL AND hv.admission_time + '14 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	crp_d15 AS (
		SELECT DISTINCT ON (hv.hospital_visit_id) hv.hospital_visit_id,
		def.test_lab_code,
		def.test_standard_code,
		res.value_as_real,
		res.valid_from,
		res.units
		
		FROM star.lab_test_definition def

		JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
		JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id
		JOIN star.hospital_visit hv ON lo.hospital_visit_id = hv.hospital_visit_id

		WHERE def.test_lab_code = 'CRP'
		AND hv.hospital_visit_id IN (SELECT csn FROM cov)
		--AND AGE(hv.admission_time, res.valid_from)  <=  '2 days'::INTERVAL
		AND res.valid_from BETWEEN hv.admission_time + '14 days'::INTERVAL AND hv.admission_time + '15 days'::INTERVAL
	  	ORDER BY hv.hospital_visit_id, res.valid_from ASC
	),
	
	respiratory_support AS (SELECT

	CASE
	    WHEN COUNT(CASE WHEN vo.value_as_text = 'Tracheostomy' THEN 1 END) > 0 THEN 'Trache'
		 WHEN COUNT(CASE WHEN vo.value_as_text = 'Endotracheal tube' THEN 1 END) > 0 THEN 'ETT'
	    WHEN COUNT(CASE WHEN vo.value_as_text = 'CPAP/Bi-PAP mask' THEN 1 END) > 0 THEN 'NIV'
	    WHEN COUNT(CASE WHEN vo.value_as_text = 'High-flow nasal cannula (HFNC)' THEN 1 END) > 0 THEN 'HFNO'
	    ELSE 'false'
	END AS respiratory_support,
	vo.hospital_visit_id
	
	FROM star.visit_observation vo 
	
	LEFT JOIN
	star.visit_observation_type vot ON vo.visit_observation_type_id = vot.visit_observation_type_id
	
	WHERE (vot.id_in_application = '3040109305' OR vot.display_name = 'O2 delivery device')
	AND vo.hospital_visit_id IN (SELECT csn FROM cov)
	GROUP BY vo.hospital_visit_id
	),
	
	hfno AS (SELECT DISTINCT ON (vo.hospital_visit_id) vo.hospital_visit_id,
	vo.observation_datetime
	
	FROM star.visit_observation vo 
	
	LEFT JOIN
	star.visit_observation_type vot ON vo.visit_observation_type_id = vot.visit_observation_type_id
	
	WHERE (vot.id_in_application = '3040109305' OR vot.display_name = 'O2 delivery device')
	AND vo.value_as_text = 'High-flow nasal cannula (HFNC)'
	AND vo.hospital_visit_id IN (SELECT csn FROM cov)
	ORDER BY vo.hospital_visit_id, vo.observation_datetime ASC
	),
	
	niv AS (SELECT DISTINCT ON (vo.hospital_visit_id) vo.hospital_visit_id,
	vo.observation_datetime
	
	FROM star.visit_observation vo 
	
	LEFT JOIN
	star.visit_observation_type vot ON vo.visit_observation_type_id = vot.visit_observation_type_id
	
	WHERE (vot.id_in_application = '3040109305' OR vot.display_name = 'O2 delivery device')
	AND vo.value_as_text = 'CPAP/Bi-PAP mask'
	AND vo.hospital_visit_id IN (SELECT csn FROM cov)
	ORDER BY vo.hospital_visit_id, vo.observation_datetime ASC
	),
	
	intubated AS (SELECT DISTINCT ON (vo.hospital_visit_id) vo.hospital_visit_id,
	vo.observation_datetime
	
	FROM star.visit_observation vo 
	
	LEFT JOIN
	star.visit_observation_type vot ON vo.visit_observation_type_id = vot.visit_observation_type_id
	
	WHERE (vot.id_in_application = '3040109305' OR vot.display_name = 'O2 delivery device')
	AND vo.value_as_text = 'Endotracheal tube'
	AND vo.hospital_visit_id IN (SELECT csn FROM cov)
	ORDER BY  vo.hospital_visit_id, vo.observation_datetime ASC
	),
	
	extubated AS (SELECT DISTINCT ON (vo.hospital_visit_id) vo.hospital_visit_id,
	vo.observation_datetime
	
	FROM star.visit_observation vo 
	
	LEFT JOIN
	star.visit_observation_type vot ON vo.visit_observation_type_id = vot.visit_observation_type_id
	
	WHERE (vot.id_in_application = '3040109305' OR vot.display_name = 'O2 delivery device')
	AND vo.value_as_text = 'Endotracheal tube'
	AND vo.hospital_visit_id IN (SELECT csn FROM cov)
	ORDER BY vo.hospital_visit_id, vo.observation_datetime DESC
	),
	
	icu AS (SELECT 

	CASE 
			WHEN COUNT(CASE WHEN SPLIT_PART(loc.location_string,'^',1) IN ('T03', 'T06PACU') THEN 1 END) > 0 THEN 'ICU'
            WHEN COUNT(CASE WHEN loc.location_string LIKE '%%GWB L01W%%' THEN 1 END) > 0 THEN 'ICU'
			WHEN COUNT(CASE WHEN SPLIT_PART(loc.location_string,'^',1) = 'T01ECU' THEN 1 END) > 0 THEN 'HDU'
	ELSE 'No ICU'
	END AS max_care,
	lv.hospital_visit_id
	
	FROM star.location_visit lv
	LEFT JOIN star.location loc ON lv.location_id = loc.location_id
	WHERE lv.hospital_visit_id IN (SELECT csn FROM cov)
	GROUP BY lv.hospital_visit_id),
	
	rrt AS (SELECT 

	CASE WHEN COUNT(CASE WHEN flo_meas_name LIKE '%%CRRT%%' THEN 1 END) > 0 THEN 'CRRT'
	ELSE 'No CRRT' END AS crrt,
	pat_enc_csn_id csn
	FROM icu_audit.flowsheets
	GROUP BY pat_enc_csn_id)
	
SELECT DISTINCT
cov.csn,
cov.mrn,
cov.valid_from,
cov.lab_sample_id,
cov.variant,
cov.time_to_test,
cov.admission_time,
cov.discharge_time,
cov.arrival_method,
cov.discharge_disposition,
cov.discharge_destination,
cov.date_of_birth,
cov.date_of_death,
cov.ethnicity,
cov.sex,
bp.valid_from bp_date,
bp.value_as_text BP,
bp.art_line,
rr.valid_from rr_date,
rr.value_as_real rr,
spo2.valid_from sats_date,
spo2.value_as_real sats,
fio2.valid_from fio2_date,
fio2.value_as_real fio2,
o2_flow.valid_from o2_flow_date,
o2_flow.value_as_real o2_flow,
gcs.valid_from gcs_date,
gcs.value_as_real gcs,
acvpu.valid_from acvpu_date,
acvpu.value_as_text acvpu,
temperature.valid_from temp_date,
temperature.value_as_real temperature,
admission_oxygen.valid_from oxygen_date,
admission_oxygen.value_as_real oxygen_delivery_device,
respiratory_support.respiratory_support,
hfno.observation_datetime hfno_start,
niv.observation_datetime niv_start,
intubated.observation_datetime intubated,
extubated.observation_datetime extubated,
dnacpr.valid_from dnacpr_date,
dnacpr.name dnacpr,
ddimer.valid_from ddimer_date,
ddimer.value_as_real ddimer,
albumin.valid_from albumin_date,
albumin.value_as_real albumin,
creat.valid_from creat_date,
creat.value_as_real creatinine,
creat.units units,
crp.valid_from admit_crp_date,
crp.value_as_real admit_crp,
ferritin.valid_from ferritin_date,
ferritin.value_as_real ferritin,
bili.valid_from bili_date,
bili.value_as_real bili,
trop.valid_from trop_date,
trop.value_as_real trop,
hb.valid_from hb_date,
hb.value_as_real hb,
lymph.valid_from lymph_date,
lymph.value_as_real lymph,
neut.valid_from neut_date,
neut.value_as_real neut,
plt.valid_from plt_date,
plt.value_as_real plt,
crp_d1.valid_from crp_d1_date,
crp_d1.value_as_real crp_d1,
crp_d2.valid_from crp_d2_date,
crp_d2.value_as_real crp_d2,
crp_d3.valid_from crp_d3_date,
crp_d3.value_as_real crp_d3,
crp_d4.valid_from crp_d4_date,
crp_d4.value_as_real crp_d4,
crp_d5.valid_from crp_d5_date,
crp_d5.value_as_real crp_d5,
crp_d6.valid_from crp_d6_date,
crp_d6.value_as_real crp_d6,
crp_d7.valid_from crp_d7_date,
crp_d7.value_as_real crp_d7,
crp_d8.valid_from crp_d8_date,
crp_d8.value_as_real crp_d8,
crp_d9.valid_from crp_d9_date,
crp_d9.value_as_real crp_d9,
crp_d10.valid_from crp_d10_date,
crp_d10.value_as_real crp_d10,
crp_d11.valid_from crp_d11_date,
crp_d11.value_as_real crp_d11,
crp_d12.valid_from crp_d12_date,
crp_d12.value_as_real crp_d12,
crp_d13.valid_from crp_d13_date,
crp_d13.value_as_real crp_d13,
crp_d14.valid_from crp_d14_date,
crp_d14.value_as_real crp_d14,
crp_d15.valid_from crp_d15_date,
crp_d15.value_as_real crp_d15,
icu.max_care,
stay.icu_department icu_dept, 
stay.icu_stay_start_dttm icu_start,
stay.icu_stay_end_dttm icu_end,
rrt.crrt

FROM cov

LEFT JOIN bp ON cov.csn = bp.hospital_visit_id
LEFT JOIN rr ON cov.csn = rr.hospital_visit_id
LEFT JOIN spo2 ON cov.csn = spo2.hospital_visit_id
LEFT JOIN fio2 ON cov.csn = fio2.hospital_visit_id
LEFT JOIN o2_flow ON cov.csn = o2_flow.hospital_visit_id
LEFT JOIN gcs ON cov.csn = gcs.hospital_visit_id
LEFT JOIN acvpu ON cov.csn = acvpu.hospital_visit_id
LEFT JOIN temperature ON cov.csn = temperature.hospital_visit_id
LEFT JOIN admission_oxygen ON cov.csn = admission_oxygen.hospital_visit_id
FULL JOIN dnacpr ON cov.csn = dnacpr.hospital_visit_id
LEFT JOIN ddimer ON cov.csn = ddimer.hospital_visit_id
LEFT JOIN albumin ON cov.csn = albumin.hospital_visit_id
LEFT JOIN creat ON cov.csn = creat.hospital_visit_id
LEFT JOIN crp ON cov.csn = crp.hospital_visit_id
LEFT JOIN ferritin ON cov.csn = ferritin.hospital_visit_id
LEFT JOIN bili ON cov.csn = bili.hospital_visit_id
LEFT JOIN trop ON cov.csn = trop.hospital_visit_id
LEFT JOIN hb ON cov.csn = hb.hospital_visit_id
LEFT JOIN lymph ON cov.csn = lymph.hospital_visit_id
LEFT JOIN neut ON cov.csn = neut.hospital_visit_id
LEFT JOIN plt ON cov.csn = plt.hospital_visit_id
LEFT JOIN crp_d1 ON cov.csn = crp_d1.hospital_visit_id
LEFT JOIN crp_d2 ON cov.csn = crp_d2.hospital_visit_id
LEFT JOIN crp_d3 ON cov.csn = crp_d3.hospital_visit_id
LEFT JOIN crp_d4 ON cov.csn = crp_d4.hospital_visit_id
LEFT JOIN crp_d5 ON cov.csn = crp_d5.hospital_visit_id
LEFT JOIN crp_d6 ON cov.csn = crp_d6.hospital_visit_id
LEFT JOIN crp_d7 ON cov.csn = crp_d7.hospital_visit_id
LEFT JOIN crp_d8 ON cov.csn = crp_d8.hospital_visit_id
LEFT JOIN crp_d9 ON cov.csn = crp_d9.hospital_visit_id
LEFT JOIN crp_d10 ON cov.csn = crp_d10.hospital_visit_id
LEFT JOIN crp_d11 ON cov.csn = crp_d11.hospital_visit_id
LEFT JOIN crp_d12 ON cov.csn = crp_d12.hospital_visit_id
LEFT JOIN crp_d13 ON cov.csn = crp_d13.hospital_visit_id
LEFT JOIN crp_d14 ON cov.csn = crp_d14.hospital_visit_id
LEFT JOIN crp_d15 ON cov.csn = crp_d15.hospital_visit_id
LEFT JOIN respiratory_support ON cov.csn = respiratory_support.hospital_visit_id
LEFT JOIN icu ON cov.csn = icu.hospital_visit_id
LEFT JOIN icu_audit.icu_stay stay ON cov.csn = stay.pat_enc_csn_id
LEFT JOIN rrt ON cov.csn = rrt.csn
LEFT JOIN hfno ON cov.csn = hfno.hospital_visit_id
LEFT JOIN niv ON cov.csn = niv.hospital_visit_id
LEFT JOIN intubated ON cov.csn = intubated.hospital_visit_id
LEFT JOIN extubated ON cov.csn = extubated.hospital_visit_id