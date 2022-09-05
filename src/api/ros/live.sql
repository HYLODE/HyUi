-- 2022-07-20

-- Heavily based on the following script:
-- https://github.com/HYLODE/HyUi/blob/10b0dce6b874df9f3d04079d213fab2e011d9155/src/beds/last_open_bed_admits.sql

-- Retrieves the patients on a ward along with their most recent ROS and MRSA test order info

WITH



beds AS (
	SELECT
		 lo.location_id
		,lo.location_string
		,lo.bed_id
		,dept.name department
		,b.hl7string
	FROM star.location lo
	LEFT JOIN star.department dept ON lo.department_id = dept.department_id
	LEFT JOIN star.bed b ON lo.bed_id = b.bed_id
	WHERE
		(
		dept.name IN
	-- Built from Tower Report 14 Jun 2022
	-- NAME                        -- n emap locations
		(
-- 		'UCH T01 ACUTE MEDICAL',       -- 86
-- 		'UCH T01 ENHANCED CARE',       -- 20
		'UCH T03 INTENSIVE CARE',      -- 37
-- 		'UCH T06 HEAD (T06H)',         -- 27
-- 		'UCH T06 CENTRAL (T06C)',      -- 25
-- 		'UCH T06 SOUTH PACU',          -- 22
-- 		'UCH T06 GYNAE (T06G)',        -- 18
-- 		'UCH T07 NORTH (T07N)',        -- 45
-- 		'UCH T07 CV SURGE',            -- 37
-- 		'UCH T07 SOUTH',               -- 33
-- 		'UCH T07 SOUTH (T07S)',        -- 23
-- 		'UCH T07 HDRU',                -- 20
-- 		'UCH T08 NORTH (T08N)',        -- 28
-- 		'UCH T08 SOUTH (T08S)',        -- 25
-- 		'UCH T08S ARCU',               --  6
-- 		'UCH T09 SOUTH (T09S)',        -- 34
-- 		'UCH T09 NORTH (T09N)',        -- 32
-- 		'UCH T09 CENTRAL (T09C)',      -- 25
-- 		'UCH T10 SOUTH (T10S)',        -- 34
-- 		'UCH T10 NORTH (T10N)',        -- 32
-- 		'UCH T10 MED (T10M)',          -- 16
-- 		'UCH T11 SOUTH (T11S)',        -- 27
-- 		'UCH T11 NORTH (T11N)',        -- 25
-- 		'UCH T11 EAST (T11E)',         -- 16
-- 		'UCH T11 NORTH (T11NO)',       --  8
-- 		'UCH T12 SOUTH (T12S)',        -- 32
-- 		'UCH T12 NORTH (T12N)',        -- 23
-- 		'UCH T13 SOUTH (T13S)',        -- 31
-- 		'UCH T13 NORTH ONCOLOGY',      -- 26
-- 		'UCH T13 NORTH (T13N)',        -- 26
-- 		'UCH T14 NORTH TRAUMA',        -- 28
-- 		'UCH T14 NORTH (T14N)',        -- 28
-- 		'UCH T14 SOUTH ASU',           -- 22
-- 		'UCH T14 SOUTH (T14S)',        -- 17
-- 		'UCH T15 SOUTH DECANT',        -- 21
-- 		'UCH T15 SOUTH (T15S)',        -- 21
-- 		'UCH T15 NORTH (T15N)',        -- 16
-- 		'UCH T15 NORTH DECANT',        -- 15
-- 		'UCH T16 NORTH (T16N)',        -- 19
-- 		'UCH T16 SOUTH (T16S)',        -- 18
-- 		'UCH T16 SOUTH WINTER',        -- 17
-- 		'GWB L01 ELECTIVE SURG',       -- 37
		'GWB L01 CRITICAL CARE',       -- 12
-- 		'GWB L02 NORTH (L02N)',        -- 19
-- 		'GWB L02 EAST (L02E)',         -- 19
-- 		'GWB L03 NORTH (L03N)',        -- 19
-- 		'GWB L03 EAST (L03E)',         -- 19
-- 		'GWB L04 NORTH (L04N)',        -- 20
-- 		'GWB L04 EAST (L04E)',         -- 17
-- 		'WMS W04 WARD',                -- 28
-- 		'WMS W03 WARD',                -- 27
-- 		'WMS W02 SHORT STAY',          -- 20
 		'WMS W01 CRITICAL CARE'        -- 11
--
-- 		OR lo.location_string IN
-- 		(
-- 		'T06C^T06C BY08^BY08-36'
-- 		)
		)
	)

),

open_visits AS (
	SELECT
		 lv.location_id
		,lv.admission_datetime
		,lv.hospital_visit_id
		,row_number() over (partition BY lv.location_id ORDER BY lv.admission_datetime DESC) admission_tail
	FROM star.location_visit lv
	INNER JOIN beds on lv.location_id = beds.location_id
	WHERE lv.discharge_datetime IS NULL

),

open_visits_last AS (
	SELECT
	*
	FROM open_visits
	WHERE admission_tail = 1
),

open_visits_count AS (
	SELECT
		 ov.location_id
		,MAX(ov.admission_tail) open_visits_n
	FROM open_visits ov
	GROUP BY ov.location_id
),

closed_visits AS (
	SELECT
		 lv.location_id
		,lv.admission_datetime
		,lv.discharge_datetime
		,lv.hospital_visit_id
		,row_number() over (partition BY lv.location_id ORDER BY lv.discharge_datetime DESC) discharge_tail
	FROM star.location_visit lv
	INNER JOIN beds on lv.location_id = beds.location_id
	WHERE lv.discharge_datetime IS NOT NULL

),

closed_visits_last AS (
	SELECT
	*
	FROM closed_visits
	WHERE discharge_tail = 1
),

all_beds_annotated AS (
	SELECT
		beds.department
		,beds.hl7string AS bed_name
		,live_mrn.mrn
		,cd.lastname
		,cd.firstname
		,cd.date_of_birth
		,ovl.hospital_visit_id
		,hv.encounter
		,hv.admission_datetime AS hospital_admission_datetime
		,ovl.admission_datetime AS location_admission_datetime
	FROM beds
	-- details of the last open visit to that bed
	LEFT JOIN open_visits_last ovl ON ovl.location_id = beds.location_id
	LEFT JOIN open_visits_count ovc ON ovc.location_id = beds.location_id
	LEFT JOIN closed_visits_last cvl ON cvl.location_id = beds.location_id
	LEFT JOIN star.hospital_visit hv ON hv.hospital_visit_id = ovl.hospital_visit_id
	LEFT JOIN star.core_demographic cd ON hv.mrn_id = cd.mrn_id
	-- get current hospital number
	LEFT JOIN star.mrn original_mrn ON hv.mrn_id = original_mrn.mrn_id
	-- get mrn to live mapping
	LEFT JOIN star.mrn_to_live mtl ON hv.mrn_id = mtl.mrn_id
	-- get live mrn
	LEFT JOIN star.mrn live_mrn ON mtl.live_mrn_id = live_mrn.mrn_id

	-- filter out "unoccupied" beds based on closed and open visits
	WHERE	NOT (cvl.discharge_datetime > ovl.admission_datetime OR ovl.admission_datetime IS NULL)

),

lab_battery_ids AS
(
	SELECT
		ltd.test_lab_code,
		lbe.lab_battery_id
		FROM star.lab_battery_element lbe
		LEFT JOIN star.lab_test_definition ltd ON lbe.lab_test_definition_id = ltd.lab_test_definition_id
		WHERE ltd.test_lab_code IN ('ROS', 'MRSA', 'NCOV', 'XCOV', 'RFLU')
),

-- NCOV -> Standard PCR
-- XCOV -> Rapid PCR
-- RFLU -> combined flu PCR

icu_labs AS
(
	SELECT
	  all_beds_annotated.encounter
	 ,lor.lab_order_id
	 ,lre.abnormal_flag
	 ,lre.result_status

	FROM all_beds_annotated
	LEFT JOIN star.lab_order lor ON all_beds_annotated.hospital_visit_id = lor.hospital_visit_id
	LEFT JOIN star.lab_result lre ON lor.lab_order_id = lre.lab_order_id

	WHERE lor.lab_battery_id IN (SELECT lab_battery_id FROM lab_battery_ids)
),

lab_result_status AS (
	SELECT
		lab_order_id
		,CASE
			WHEN 'A' = ANY(ARRAY_AGG(abnormal_flag)) THEN 'A' ELSE NULL
		END abnormal_flag
		,CASE
			WHEN 'FINAL' = ANY(ARRAY_AGG(result_status)) THEN 'FINAL' ELSE NULL
		END result_status
		FROM icu_labs
		GROUP BY lab_order_id
),

labs_agg AS (
	SELECT
		DISTINCT lor.lab_order_id
		,all_beds_annotated.encounter
		,lrs.abnormal_flag
		,lrs.result_status
		,lor.order_datetime
		,lor.lab_battery_id
		FROM all_beds_annotated
		LEFT JOIN star.lab_order lor ON all_beds_annotated.hospital_visit_id = lor.hospital_visit_id
		LEFT JOIN lab_result_status lrs ON lrs.lab_order_id = lor.lab_order_id
		WHERE lor.lab_battery_id IN (SELECT lab_battery_id FROM lab_battery_ids)
			AND lor.order_datetime IS NOT NULL
),


ros_mrsa_results AS (
	SELECT *
	FROM
			(
				SELECT
						encounter
						,json_agg
							(
								json_build_object
									(
										'order_datetime', labs_agg.order_datetime,
										'result_status', labs_agg.result_status,
										'abnormal_flag', labs_agg.abnormal_flag
									)
								ORDER BY labs_agg.lab_order_id DESC
							)
							AS ros_orders
				FROM labs_agg
				WHERE lab_battery_id IN (SELECT lab_battery_id FROM lab_battery_ids WHERE test_lab_code = 'ROS')
				GROUP BY encounter
				ORDER BY encounter
			) AS ros
		FULL JOIN
			(
				SELECT
						encounter
						,json_agg
							(
								json_build_object
									(
										'order_datetime', labs_agg.order_datetime,
										'result_status', labs_agg.result_status,
										'abnormal_flag', labs_agg.abnormal_flag
									)
								ORDER BY labs_agg.lab_order_id DESC
							)
							AS mrsa_orders
				FROM labs_agg
				WHERE lab_battery_id = (SELECT lab_battery_id FROM lab_battery_ids WHERE test_lab_code = 'MRSA')
				GROUP BY encounter
				ORDER BY encounter
			) AS mrsa
		USING ("encounter")
		FULL JOIN
			(
				SELECT
						encounter
						,json_agg
							(
								json_build_object
									(
										'order_datetime', labs_agg.order_datetime,
										'result_status', labs_agg.result_status,
										'abnormal_flag', labs_agg.abnormal_flag
									)
								ORDER BY labs_agg.lab_order_id DESC
							)
							AS covid_orders
				FROM labs_agg
				WHERE lab_battery_id IN (SELECT lab_battery_id FROM lab_battery_ids WHERE test_lab_code IN ('NCOV', 'XCOV', 'RFLU'))
				GROUP BY encounter
				ORDER BY encounter
			) AS covid
		USING ("encounter")
)

SELECT
		 ab.department
		,ab.bed_name
		,ab.mrn
		,ab.firstname
		,ab.lastname
		,ab.encounter
		,ab.date_of_birth
		,ab.hospital_admission_datetime
		,ab.location_admission_datetime
		,r.ros_orders
		,r.mrsa_orders
		,r.covid_orders
	FROM all_beds_annotated ab
	LEFT JOIN ros_mrsa_results r ON ab.encounter = r.encounter
	ORDER BY department, bed_name
