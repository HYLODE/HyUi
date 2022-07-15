-- SELECT
-- *
-- FROM star.lab_battery lb
-- WHERE lb.battery_code LIKE '%%ROS%%'
-- LIMIT 3
-- ;
-- lab_battery_id 29846 for ROS and 337045 for ROSR

-- looks like 29846 is the right code

WITH icupts AS (
	SELECT
	 lv.admission_time
	--,lv.discharge_time
	--,lo.location_string
	,lv.hospital_visit_id

	  -- original MRN
	--  ,original_mrn.mrn AS original_mrn
	  -- live MRN
	  ,live_mrn.mrn AS live_mrn

	  -- core demographics
	  ,cd.date_of_birth
	  -- convert dob to age in years
	 -- ,date_part('year', AGE(cd.date_of_birth)) AS AGE

	  --,cd.sex
	  --,cd.home_postcode
	  -- grab initials from first and last name
	  --,CONCAT(LEFT(cd.firstname, 1), LEFT(cd.lastname, 1)) AS initials
		,cd.firstname
		,cd.lastname

	--,bed.hl7string
	--,bed.room_id
	--,room.hl7string
	,room.name
	--,room.department_id
	--,department.hl7string
-- 	,department.name
-- 	,department.speciality


	FROM star.location_visit lv
	LEFT JOIN star.location lo ON lv.location_id = lo.location_id
	LEFT JOIN star.bed ON lo.bed_id = bed.bed_id
	LEFT JOIN star.room ON lo.room_id = room.room_id
	LEFT JOIN star.department ON room.department_id = department.department_id

	LEFT JOIN star.hospital_visit vo ON lv.hospital_visit_id = vo.hospital_visit_id
	INNER JOIN star.core_demographic cd ON vo.mrn_id = cd.mrn_id

	-- get original mrn
	INNER JOIN star.mrn original_mrn ON vo.mrn_id = original_mrn.mrn_id
	-- get mrn to live mapping
	INNER JOIN star.mrn_to_live mtl ON vo.mrn_id = mtl.mrn_id
	-- get live mrn
	INNER JOIN star.mrn live_mrn ON mtl.live_mrn_id = live_mrn.mrn_id

	WHERE SPLIT_PART(lo.location_string,'^',1) ~ '^(T03)'
		AND lv.discharge_time IS NULL
	ORDER BY lv.admission_time DESC
),
icu_labs AS
(
	SELECT
	  icupts.hospital_visit_id
-- 	 ,lor.lab_order_id
-- 	 ,lor.lab_battery_id
	 ,lor.order_datetime
-- 	 ,lor.request_datetime
-- 	 ,lor.internal_lab_number

	 ,lre.lab_result_id
-- 	 ,lre.result_last_modified_time
-- 	 ,lre.value_as_text
-- 	 ,lre.abnormal_flag
-- 	 ,lre."comment"
-- 	 ,lre.result_status


	FROM icupts
	LEFT JOIN star.lab_order lor ON icupts.hospital_visit_id = lor.hospital_visit_id
	LEFT JOIN star.lab_result lre ON lor.lab_order_id = lre.lab_order_id

	WHERE lor.lab_battery_id IN (29846, 337045)
),

latest_labs AS
(
	SELECT
		icu_labs_ordered.*
	FROM (
	SELECT *,
	           ROW_NUMBER() OVER (PARTITION BY hospital_visit_id ORDER BY lab_result_id DESC) AS position
	    FROM icu_labs
	  ) icu_labs_ordered

	WHERE icu_labs_ordered.position = 1
)

SELECT
	icupts.*
-- 	,ll.*
	,ll.order_datetime
	,ll.lab_result_id
FROM icupts
	LEFT JOIN latest_labs ll ON icupts.hospital_visit_id = ll.hospital_visit_id


 -- LIMIT 200
;
