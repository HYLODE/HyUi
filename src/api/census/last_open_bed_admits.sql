-- 2022-07-09
-- takes around 20s to run but returns essentially a census for each ward
-- for each location
-- last open visit
-- last closed visit
-- number of open visits

-- for each location
-- last open visit
-- last closed visit
-- number of open visits

-- for each location
-- last open visit
-- last closed visit
-- number of open visits

-- Bugs and Issues
-- T06C^T06C BY08^BY08-36 does not exist in the department table

WITH



beds AS (
	SELECT
		 lo.location_id
		,lo.location_string
		,dept.name department
	FROM star.location lo
	LEFT JOIN star.department dept ON lo.department_id = dept.department_id
	WHERE
		(
		dept.name IN
	-- Built from Tower Report 14 Jun 2022
	-- NAME                        -- n emap locations
		(
		'UCH T01 ACUTE MEDICAL',       -- 86
		'UCH T01 ENHANCED CARE',       -- 20
		'UCH T03 INTENSIVE CARE',      -- 37
		'UCH T06 HEAD (T06H)',         -- 27
		'UCH T06 CENTRAL (T06C)',      -- 25
		'UCH T06 SOUTH PACU',          -- 22
		'UCH T06 GYNAE (T06G)',        -- 18
		'UCH T07 NORTH (T07N)',        -- 45
		'UCH T07 CV SURGE',            -- 37
		'UCH T07 SOUTH',               -- 33
		'UCH T07 SOUTH (T07S)',        -- 23
		'UCH T07 HDRU',                -- 20
		'UCH T08 NORTH (T08N)',        -- 28
		'UCH T08 SOUTH (T08S)',        -- 25
		'UCH T08S ARCU',               --  6
		'UCH T09 SOUTH (T09S)',        -- 34
		'UCH T09 NORTH (T09N)',        -- 32
		'UCH T09 CENTRAL (T09C)',      -- 25
		'UCH T10 SOUTH (T10S)',        -- 34
		'UCH T10 NORTH (T10N)',        -- 32
		'UCH T10 MED (T10M)',          -- 16
		'UCH T11 SOUTH (T11S)',        -- 27
		'UCH T11 NORTH (T11N)',        -- 25
		'UCH T11 EAST (T11E)',         -- 16
		'UCH T11 NORTH (T11NO)',       --  8
		'UCH T12 SOUTH (T12S)',        -- 32
		'UCH T12 NORTH (T12N)',        -- 23
		'UCH T13 SOUTH (T13S)',        -- 31
		'UCH T13 NORTH ONCOLOGY',      -- 26
		'UCH T13 NORTH (T13N)',        -- 26
		'UCH T14 NORTH TRAUMA',        -- 28
		'UCH T14 NORTH (T14N)',        -- 28
		'UCH T14 SOUTH ASU',           -- 22
		'UCH T14 SOUTH (T14S)',        -- 17
		'UCH T15 SOUTH DECANT',        -- 21
		'UCH T15 SOUTH (T15S)',        -- 21
		'UCH T15 NORTH (T15N)',        -- 16
		'UCH T15 NORTH DECANT',        -- 15
		'UCH T16 NORTH (T16N)',        -- 19
		'UCH T16 SOUTH (T16S)',        -- 18
		'UCH T16 SOUTH WINTER',        -- 17
		'GWB L01 ELECTIVE SURG',       -- 37
		'GWB L01 CRITICAL CARE',       -- 12
		'GWB L02 NORTH (L02N)',        -- 19
		'GWB L02 EAST (L02E)',         -- 19
		'GWB L03 NORTH (L03N)',        -- 19
		'GWB L03 EAST (L03E)',         -- 19
		'GWB L04 NORTH (L04N)',        -- 20
		'GWB L04 EAST (L04E)',         -- 17
		'WMS W04 WARD',                -- 28
		'WMS W03 WARD',                -- 27
		'WMS W02 SHORT STAY',          -- 20
		'WMS W01 CRITICAL CARE'        -- 11
		)
		OR lo.location_string IN
		(
		'T06C^T06C BY08^BY08-36'
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
)


SELECT
	 beds.location_id
	,beds.department
	,beds.location_string
	,ovl.admission_datetime ovl_admission
	,ovl.hospital_visit_id ovl_hv_id
	,ovc.open_visits_n
	,cvl.admission_datetime cvl_admission
	,cvl.discharge_datetime cvl_discharge
	,cvl.hospital_visit_id cvl_hv_id

	,CASE
	 	WHEN cvl.discharge_datetime > ovl.admission_datetime THEN 1 ELSE 0
	 END ovl_ghost
	,CASE
	 	WHEN cvl.discharge_datetime > ovl.admission_datetime OR ovl.admission_datetime IS NULL THEN 0 ELSE 1
	 END occupied

	,hv.patient_class
	,live_mrn.mrn
	,cd.lastname
	,cd.firstname
	,cd.date_of_birth

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

WHERE beds.location_string = 'T06C^T06C BY08^BY08-36'

ORDER BY beds.location_string

;
