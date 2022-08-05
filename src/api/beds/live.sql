-- 2022-07-18
-- parameterised version

-- pass in
-- wards : python list of strings
-- e.g. ['WMS W01 CRITICAL CARE', 'WMS W02 SHORT STAY']
-- locations: python list of strings
-- e.g. ['T06C^T06C BY08^BY08-36']

-- locations allows hand editing where departments are not attached to locations
-- see Bugs and Issues:
-- T06C^T06C BY08^BY08-36 does not exist in the department table

-- takes around 20s to run but returns essentially a census for each ward
-- for each location
-- last open visit
-- last closed visit
-- number of open visits

WITH

beds AS (
	SELECT
		 lo.location_id
		,lo.location_string
		,dept.name department
	FROM star.location lo
	LEFT JOIN star.department dept ON lo.department_id = dept.department_id
	WHERE (
		dept.name = ANY ( :departments )
		OR
		lo.location_string = ANY ( :locations )
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

    ,NOW() modified_at

	,hv.patient_class
	,hv.encounter
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

ORDER BY beds.location_string

;
