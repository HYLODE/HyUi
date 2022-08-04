-- Query to join with deterioration data to get some up to date data


-- Get last location
WITH last_location AS (
	SELECT DISTINCT ON (lv.hospital_visit_id) lv.hospital_visit_id,
	loc.location_string,
	-- define building / physical site
	CASE
		-- THP3 includes podium theatres
		WHEN SPLIT_PART(location_string,'^',1) ~ '^(T0|T1|THP3|ED(?!H))'  THEN 'tower'
		WHEN SPLIT_PART(location_string,'^',2) ~ '^(UCH T|T0|T1)'  THEN 'tower'
		WHEN SPLIT_PART(location_string,'^',2) ~ '^E0'  THEN 'EGA' -- this is a guess
		WHEN SPLIT_PART(location_string,'^',2) ~ '^GWB'  THEN 'GWB' -- Grafton way building
	END AS building,

	-- define bed type
	CASE
		WHEN SUBSTR(SPLIT_PART(location_string,'^',3),1,2) IN ('BY', 'CB') then 'bay'
		WHEN SUBSTR(SPLIT_PART(location_string,'^',3),1,2) IN ('SR') then 'sideroom'
		WHEN SUBSTR(SPLIT_PART(location_string,'^',3),1,2) IN ('CH') then 'chair'
		WHEN SUBSTR(SPLIT_PART(location_string,'^',3),1,2) IN ('TR') then 'treatment room'
		WHEN SUBSTR(SPLIT_PART(location_string,'^',3),1,2) IN ('PR') then 'procedure room'
		WHEN location_string ~ '.*(SURGERY|THR|PROC|ENDO|TREAT|ANGI).*|.+(?<!CHA)IN?R\^.*' then 'procedure'
		WHEN location_string ~ '.*XR.*|.*MRI.*|.+CT\^.*|.*SCANNER.*' then 'imaging'
	END AS bed_type,

	CASE
		WHEN SPLIT_PART(location_string,'^',1) = 'ACU' THEN 'E03 Antenatal Care Unit' -- maternity
		WHEN SPLIT_PART(location_string,'^',1) = 'BBNU' THEN 'E03 Birth Centre' -- maternity
		WHEN SPLIT_PART(location_string,'^',1) = 'BCN' THEN 'E03 Birth Care Nursery' -- neonates
		WHEN SPLIT_PART(location_string,'^',1) = 'COB' THEN 'E02 Close Observation Unit' -- maternity
		WHEN SPLIT_PART(location_string,'^',1) = 'COBN' THEN 'E02 Close Observation Unit Nursery' -- neonates
		WHEN SPLIT_PART(location_string,'^',1) = 'CRF' THEN 'Tottenham Court Road CRF' --
		WHEN SPLIT_PART(location_string,'^',1) = 'EAU' THEN 'T00 EAU'
		WHEN SPLIT_PART(location_string,'^',1) = '1020100172' THEN 'T07SWH'
		WHEN SPLIT_PART(location_string,'^',1) = 'F3NU' THEN 'E03MCU Maternity'
		WHEN SPLIT_PART(location_string,'^',1) = 'LW' THEN 'E02LW Labour Ward'
		WHEN SPLIT_PART(location_string,'^',1) = 'LWN' THEN 'E02LWN Labour Ward Nursery'
		WHEN SPLIT_PART(location_string,'^',1) = 'MCUN' THEN 'E03 MCU Nursery'
		WHEN SPLIT_PART(location_string,'^',1) = 'MFAW' THEN 'EGA Maternal and Fetal Assessment Unit'
		WHEN SPLIT_PART(location_string,'^',1) = 'TO1ECU' THEN 'ECU'
		WHEN SPLIT_PART(location_string,'^',1) = 'T1DC' THEN 'T1DC infusion clinic'
		WHEN SPLIT_PART(location_string,'^',1) = 'UCHT00CDU' THEN 'CDU'
		WHEN SPLIT_PART(location_string,'^',1) = 'HS15' THEN SPLIT_PART(SPLIT_PART(location_string, '^', 2), ' ', 1)
		WHEN SPLIT_PART(SPLIT_PART(location_string,'^',2), ' ', 1) = 'GWB' THEN SPLIT_PART(SPLIT_PART(location_string, '^', 2), ' ', 2)
		--WHEN SUBSTR(SPLIT_PART(lo.location_string,'^',2), 1, 6) = 'T07SWH' THEN 'T07SWH'
		ELSE SPLIT_PART(location_string,'^',1)
	END AS ward_purpose,
	lv.admission_datetime

	FROM star.location_visit lv
	LEFT JOIN star.location loc ON lv.location_id = loc.location_id
	WHERE lv.hospital_visit_id IN ({csns})
	ORDER BY lv.hospital_visit_id, lv.admission_datetime DESC),


-- Get last resus status
dnacpr AS (
		SELECT DISTINCT ON (ad.hospital_visit_id) ad.hospital_visit_id,
		ad.valid_from,
		adt.name

		FROM star.advance_decision ad

		JOIN star.advance_decision_type adt
		ON adt.advance_decision_type_id = ad.advance_decision_type_id

	  	WHERE ad.hospital_visit_id IN ({csns})
	  	ORDER BY ad.hospital_visit_id, ad.valid_from DESC
		),

-- Get most recent news
news AS (SELECT DISTINCT ON (vo.hospital_visit_id) vo.hospital_visit_id,
		vo.observation_datetime,
		vo.value_as_text

		FROM star.visit_observation vo

		LEFT JOIN
		star.visit_observation_type vot ON vo.visit_observation_type_id = vot.visit_observation_type_id

		WHERE vot.id_in_application IN ('28315', '28316')
		AND vo.hospital_visit_id IN ({csns})
		--AND vo.value_as_real IS NOT NULL
		ORDER BY vo.hospital_visit_id, vo.observation_datetime DESC
		)

SELECT

cd.firstname,
cd.lastname,
hv.hospital_visit_id,
hv.encounter AS csn,
mrn.mrn,
last_location.ward_purpose,
last_location.location_string,
last_location.admission_datetime,
dnacpr.name dnacpr,
news.value_as_text news_score,
news.observation_datetime news_time


FROM star.hospital_visit hv

LEFT JOIN last_location ON hv.hospital_visit_id = last_location.hospital_visit_id
LEFT JOIN dnacpr ON hv.hospital_visit_id = dnacpr.hospital_visit_id
LEFT JOIN star.mrn ON hv.mrn_id = mrn.mrn_id
LEFT JOIN star.core_demographic cd ON mrn.mrn_id = cd.mrn_id
LEFT JOIN news ON hv.hospital_visit_id = news.hospital_visit_id

WHERE hv.hospital_visit_id IN ({csns});
