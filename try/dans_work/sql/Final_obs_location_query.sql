-- D Stein Oct 2021

-- Query to pull obs from adult inpatients currently on the wards
-- Adapted from S Harris example obs query
-- This is not a flexible query and will now only pull obs from patients on wards that we are interested in

WITH ward_location AS (
    SELECT DISTINCT location_string loc

        ,location_id
        ,location_string

        ,SPLIT_PART(location_string,'^',3) bed
        ,SPLIT_PART(location_string,'^',1) ward_raw

        -- define building / physical site
        ,CASE
            -- THP3 includes podium theatres
            WHEN SPLIT_PART(location_string,'^',1) ~ '^(T0|T1|THP3|ED(?!H))'  THEN 'tower'
            WHEN SPLIT_PART(location_string,'^',2) ~ '^(UCH T|T0|T1)'  THEN 'tower'
            WHEN SPLIT_PART(location_string,'^',2) ~ '^E0'  THEN 'EGA' -- this is a guess
            WHEN SPLIT_PART(location_string,'^',2) ~ '^GWB'  THEN 'GWB' -- Grafton way building
        END AS building

        -- define bed type
        ,CASE
            WHEN SUBSTR(SPLIT_PART(location_string,'^',3),1,2) IN ('BY', 'CB') then 'bay'
            WHEN SUBSTR(SPLIT_PART(location_string,'^',3),1,2) IN ('SR') then 'sideroom'
            WHEN SUBSTR(SPLIT_PART(location_string,'^',3),1,2) IN ('CH') then 'chair'
            WHEN location_string ~ '.*(SURGERY|THR|PROC|ENDO|TREAT|ANGI).*|.+(?<!CHA)IN?R\^.*' then 'procedure'
            WHEN location_string ~ '.*XR.*|.*MRI.*|.+CT\^.*|.*SCANNER.*' then 'imaging'
        END AS bed_type

    FROM star.location



    -- A note about location_string:
    -- Location strings appear as 3 part HL7 strings separated by ^ (e.g. ___^___^___). Different parts appear in differnt bits of the string
    -- SR, BY usually refer to side room or bay and appear in the second or third split hence in some places these are split up
    -- However some things are binned in general because they obviously pertain to something we want to exclude


    WHERE
    -- Bin split 1
    SPLIT_PART(location_string,'^',1) NOT IN ('ED')

    AND
    -- This comes from the build view location sql file (BVL)
    SPLIT_PART(location_string,'^',1) !~ '^(T03|WSCC|SINQ|MINQ|P03CV)'
    AND SUBSTR(location_string,1,2) NOT IN ('WM', 'WS') -- Westmoreland street

    -- Bin all irrelevant wards/ sub areas in split 2
    AND
    SPLIT_PART(location_string, '^', 2) NOT IN ('NICU', 'NURSERY', 'RESUS', 'MAJORS')
    AND SPLIT_PART(location_string,'^',2) !~ '^(T07CV.*)' -- from BVL

    -- Bin anything beginning with ED, NHNN (national hospital for neurology and neursurgery), Chalfont epilepsy centre
    -- Mortimer market centre

    -- Bin the first split of split 2 (word space word) as this often pertains to a building or useful location)
    AND SPLIT_PART(SPLIT_PART(location_string, '^', 2), ' ', 1) NOT IN 	('ED', 'SDEC', 'RLHIM',
                                                                         'SCBU', 'RLHIMDCU', 'GWBPATLNGE', 'ICU',
                                                                         'T06PACU', 'NHNN', 'NHNNTHR', 'NICU',
																		 'UCHPATLNGE', 'CHALF', 'CHALFDC', 'MMKT')
    AND SPLIT_PART(location_string, '^', 2) NOT LIKE '%%SDEC%%' -- Same day emergency care
    AND SPLIT_PART(location_string, '^', 2) NOT LIKE '%%RLHIM%%' -- Royal london hospital for integrative medicine
    AND SPLIT_PART(location_string, '^', 2) NOT LIKE '%%SCBU%%' -- Special care baby unit
    AND SPLIT_PART(location_string, '^', 2) NOT LIKE 'TRIAGE%%' -- Triage
    AND SPLIT_PART(location_string, '^', 2) NOT LIKE 'OFF%%' -- Think this is offsite

    -- Now bin things that are in split 3
    -- Cot implies baby I think
    AND SPLIT_PART(location_string, '^', 3) NOT IN ('WMS', 'UCHED', 'RLHIM', 'NICU', 'CHAIR', 'COT')
    AND SPLIT_PART(location_string, '^', 3) NOT LIKE 'DO NOT%%'
    AND SPLIT_PART(location_string, '^', 3) NOT LIKE 'ENT ROOM%%'
    AND SPLIT_PART(location_string, '^', 3) NOT LIKE 'HOME%%' -- Not interested in patients at home
    AND SPLIT_PART(location_string, '^', 3) NOT LIKE 'HOTEL%%' -- Some people consider the hospital to be a hotel


    -- Now just generally bin locations that are clearly not within scope
    AND location_string NOT LIKE '%%CHALF%%' -- Chalfont epilepsy centre
    AND location_string NOT LIKE '%%ZZZ%%'
    AND location_string NOT LIKE '%%zzz%%' -- Test locations
    AND location_string NOT LIKE '%%RNTNE%%' -- royal national ent and eastman dental hospitals
    AND location_string NOT LIKE '%%WMS%%' -- Westmoreland street
    AND location_string NOT LIKE '%%OUT%%' -- Anything pertaining to outpatients
    AND location_string NOT LIKE '%%NICU%%' -- Neonatal intensive care
    AND location_string NOT LIKE '%%Paediatric%%' -- Anything pertaining to children
    AND location_string NOT LIKE '%%PAEDIATRIC%%'
    AND location_string NOT LIKE '%%THEATRE%%' -- Anything pertaining to theatres
    AND location_string NOT LIKE '%%THR%%'
    AND location_string NOT LIKE '%%TELE%%' -- Anything remote
    AND location_string NOT LIKE '%%Tele%%'
    AND location_string NOT LIKE '%%HOME%%'
    AND location_string NOT LIKE '%%WAIT%%' -- Waiting rooms suggest outpatients
    AND location_string NOT LIKE '%%Wait%%'
    AND location_string NOT LIKE '%%CLIN%%' -- clinic
    AND location_string NOT LIKE '%%Clin%%'
    AND location_string NOT LIKE '%%SURGERY%%' -- surgery
    AND location_string NOT LIKE '%%ENTED%%' -- ent/ eastman dental
    AND location_string NOT LIKE 'EDH%%' -- Eastman Dental
    AND location_string NOT LIKE '%%MCC%%' -- macmillan cancer care
    AND location_string NOT LIKE '%%LOUNGE%%'
    AND location_string NOT LIKE '%%Lounge%%'
    AND location_string NOT LIKE '%%ICU%%' -- Intensive care
    AND location_string NOT LIKE '%%ITU%%'
    AND location_string NOT LIKE '%%RECOVERY%%'
    AND location_string NOT LIKE '%%RCVY%%' -- recovery
    AND location_string NOT LIKE '%%CHAIR%%' -- Chairs aren't locatiosn on wards
    AND location_string NOT LIKE '%%PATLNG%%' -- Think this is patient loungre
    AND location_string NOT LIKE '%%DAY%%' -- Day cases aren't inpatients
    AND location_string NOT LIKE '%%IR%%' -- Interventional radiology
    AND location_string NOT LIKE '%%Mother%%' -- Don't think we're interested in things pertaining to mother as I think this implies that the mother is not the patient? - should possibly consider this
    AND location_string NOT LIKE '%%Mum%%'
    AND location_string NOT LIKE '%%NEONATAL%%'
    AND location_string NOT LIKE '%%ENDO%%' -- Endocrinology
    AND location_string NOT LIKE '%%Discharge%%'
    AND location_string NOT LIKE '%%DISCHARGE%%'
    AND location_string NOT LIKE '%%EMERG%%' -- Think this is emergency department
    AND location_string NOT LIKE '%%null%%null%%' -- there are lots that don't appear to be real locations with loc^null^null
    AND location_string NOT LIKE 'EDH%%'
    AND location_string NOT LIKE '%%OUTSC%%' -- external
    AND location_string NOT LIKE '%%CC%%' -- removes all critical care units


    --- Also only include places which have ever had a patient or visit:
    AND location_id IN (SELECT location_id FROM star.location_visit)


    ORDER BY loc
    )

SELECT
  	-- observation details
	ob.visit_observation_id,
  	ob.hospital_visit_id,
  	ob.observation_datetime,

  	--,ob.visit_observation_type_id
  	ot.id_in_application,

  	-- label nicely: currently not using as will subsequently label in python
  CASE
    WHEN ot.id_in_application = '10' THEN 'SpO2'
    WHEN ot.id_in_application = '5' THEN 'BP'
    WHEN ot.id_in_application = '3040109304' THEN 'Oxygen'
    WHEN ot.id_in_application = '6' THEN 'Temp'
    WHEN ot.id_in_application = '8' THEN 'Pulse'
    WHEN ot.id_in_application = '9' THEN 'Resp'
    WHEN ot.id_in_application = '6466' THEN 'AVPU'
    WHEN ot.id_in_application = '28315' THEN 'NEWS Score'
    WHEN ot.id_in_application = '401001' THEN 'GCS Total'
    WHEN ot.id_in_application = '3040109305' THEN 'Oxygen delivery device'
    WHEN ot.id_in_application = '250026' THEN 'Oxygen therapy flow rate'
    WHEN ot.id_in_application = '301550' THEN 'FiO2'
    WHEN ot.id_in_application = '28316' THEN 'NEWS2 Score'

  	END AS vital,

  	ob.value_as_real,
  	ob.value_as_text,
  	ob.unit,

  	-- Admisssion time, discharge time, location, age can probably be removed when happy with this string
  	loc.admission_time,
  	loc.discharge_time,
  	lo.location_string,
  	demog.date_of_birth,

  	-- Can think about making this a decimal?
  	EXTRACT(YEAR FROM AGE(ob.observation_datetime, demog.date_of_birth)) AS age_at_obs,

  	-- Time to ICU admission
  	CASE
	  	WHEN loc.admission_time > ob.observation_datetime THEN AGE(loc.admission_time, ob.observation_datetime)
  		ELSE NULL
	END AS time_to_ICU

    -- Include MRN
    ,mrn.mrn

    --Include some other demographics as well
    ,demog.ethnicity
    ,demog.home_postcode -- for index of multiple deprivation
    ,demog.sex

FROM
  star.visit_observation ob

-- observation look-up
	LEFT JOIN
  		star.visit_observation_type ot
  		ON ob.visit_observation_type_id = ot.visit_observation_type_id

	-- Now add in the hospital locations
	FULL JOIN star.location_visit loc
		ON ob.hospital_visit_id = loc.hospital_visit_id

	-- Get the actual location names
	INNER JOIN star.location lo ON loc.location_id = lo.location_id

	-- Get the patient ages so we can bin children - need to match the MRN first
	INNER JOIN star.hospital_visit visit ON visit.hospital_visit_id = loc.hospital_visit_id

	-- Now we can pull birthday
	INNER JOIN star.core_demographic demog ON visit.mrn_id = demog.mrn_id

    -- Now add MRN for EPIC observation crosscheck
    INNER JOIN star.mrn mrn ON demog.mrn_id = mrn.mrn_id

-- Only recent obs at this stage
WHERE ob.observation_datetime > NOW() - '30 MINUTES'::INTERVAL

-- Only use patients over 16
AND ob.observation_datetime - demog.date_of_birth > '16'::INTERVAL

-- Only include named obs
AND ot.id_in_application in

  (
  '10'            --'SpO2'                  -- 602063230
  ,'5'            --'BP'                    -- 602063234
  ,'3040109304'   --'Room Air or Oxygen'    -- 602063268
  ,'6'            --'Temp'                  -- 602063248
  ,'8'            --'Pulse'                 -- 602063237
  ,'9'            --'Resp'                  -- 602063257
  ,'6466'         -- Level of consciousness
  ,'28315'			-- NEWS Score
  ,'401001'			-- GCS total
  ,'3040109305'	-- Oxygen delivery device
  ,'250026'			-- Oxygen therapy flow rate
  ,'301550'			-- FiO2
  ,'28316'			-- NEWS2 score
)


-- Now ensure that we are only looking at obs from ward patients using previously built view
AND lo.location_string IN (SELECT location_string FROM ward_location)


-- Now bin all rows where the observation isn't in the location admission window - could be using between here?
AND
ob.observation_datetime >= loc.admission_time

AND
(ob.observation_datetime <= loc.discharge_time OR loc.discharge_time IS NULL)

ORDER BY ob.observation_datetime DESC
;
