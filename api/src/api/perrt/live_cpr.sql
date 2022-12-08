-- noinspection SqlNoDataSourceInspectionForFile

SELECT
	 ad.advance_decision_id
	,ad.requested_datetime
	,ad.status_change_datetime
	,adt.care_code
	,adt.name
	,ad.cancelled
	,ad.closed_due_to_discharge
	,ad.hospital_visit_id
	,hv.encounter
FROM advance_decision ad
LEFT JOIN advance_decision_type adt ON ad.advance_decision_type_id = adt.advance_decision_type_id
LEFT JOIN hospital_visit hv ON ad.hospital_visit_id = hv.hospital_visit_id
WHERE hv.encounter = ANY( :encounter_ids )
;
