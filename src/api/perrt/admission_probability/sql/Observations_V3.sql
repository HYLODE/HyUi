-- Updated observations view
-- D Stein Mar 2022

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
            WHEN SPLIT_PART(location_string,'^',1) ~ '^MFAW'  THEN 'EGA' -- MFAW is maternal and fetal admission unit?
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
    ((SPLIT_PART(location_string,'^',1) NOT IN ('ED')

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

    -- Bin all queen's square locations
    AND SUBSTR(location_string, 4, 1) NOT IN ('Q')

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
    AND location_string NOT LIKE '%%GWB L01W%%') -- removes GWB CCU


    -- Updating to include SDEC
    OR (location_string LIKE '%%SDEC%%'))

    --- Also only include places which have ever had a patient or visit:
    AND location_id IN (SELECT location_id FROM star.location_visit)


    ORDER BY loc
    ),

    rough_census AS
       (
        SELECT 	hv.encounter AS csn,
   		hv.hospital_visit_id AS hv_id,
         lv.admission_datetime    AS admission_dt,
         lv.discharge_datetime AS discharge_dt,
         loc.location_string  AS hl7_location,
			m.mrn AS mrn

         FROM star.hospital_visit hv
                LEFT JOIN star.mrn m
                          ON hv.mrn_id = m.mrn_id
                LEFT JOIN star.core_demographic pt
                          ON m.mrn_id = pt.mrn_id
                LEFT JOIN star.location_visit lv
                          ON hv.hospital_visit_id = lv.hospital_visit_id
                LEFT JOIN star.location loc
                          ON lv.location_id = loc.location_id


         WHERE (loc.location_string IN ({location}))--(loc.location_string LIKE 'T03%%' OR loc.location_string LIKE '%%T06PACU%%' OR loc.location_string LIKE '%%GWB L01 CC%%')
           AND hv.patient_class IN ('INPATIENT', 'EMERGENCY')
           AND hv.admission_datetime IS NOT NULL -- check a valid hospital visit
           AND lv.admission_datetime <= {end_time} -- check location admission happened at or before horizon
			  AND lv.admission_datetime >= {end_time} - '6 MONTHS'::INTERVAL -- Bin patients who have been in a given bed an unfeasibly long time
           AND (hv.discharge_datetime IS NULL OR hv.discharge_datetime > {end_time})       -- check patient is still in hospital at horizon
           AND (lv.discharge_datetime IS NULL OR lv.discharge_datetime > {end_time})       -- check patient is still at location at horizon
           AND (pt.date_of_death IS NULL OR pt.date_of_death > {end_time}) -- check patient is alive at horizon

       ),
     census AS
       (
         SELECT csn,
                hv_id,
                admission_dt,
                discharge_dt,
                hl7_location,
                mrn
         FROM (
                SELECT csn,
                       hv_id,
                       admission_dt,
                       discharge_dt,
                       hl7_location,
                       ROW_NUMBER() OVER (PARTITION BY hl7_location ORDER BY admission_dt DESC) AS POSITION,
                       mrn
                FROM rough_census
              ) occupant_ordered
         WHERE occupant_ordered.position = 1 -- filters ghosts who may be lingering in a bed
       )

-- Now repeat the census query but this time for ICU
-- First do the census query
, rough_ICU_census AS
       (
        SELECT 	hv.encounter AS csn,
   		hv.hospital_visit_id AS hv_id,
         lv.admission_datetime    AS admission_dt,
         lv.discharge_datetime AS discharge_dt,
         loc.location_string  AS hl7_location,
			m.mrn AS mrn

         FROM star.hospital_visit hv
                LEFT JOIN star.mrn m
                          ON hv.mrn_id = m.mrn_id
                LEFT JOIN star.core_demographic pt
                          ON m.mrn_id = pt.mrn_id
                LEFT JOIN star.location_visit lv
                          ON hv.hospital_visit_id = lv.hospital_visit_id
                LEFT JOIN star.location loc
                          ON lv.location_id = loc.location_id


         WHERE ({icu_location})
           AND hv.patient_class IN ('INPATIENT', 'EMERGENCY')
           AND hv.admission_datetime IS NOT NULL -- check a valid hospital visit
           AND lv.admission_datetime >= {end_time} -- check admission happened in the future
           AND lv.admission_datetime <= {end_time} + '24 HOURS'::INTERVAL -- check admission happened in about 24h time
           AND (hv.discharge_datetime IS NULL OR hv.discharge_datetime > {end_time} + '24 HOURS'::INTERVAL)       -- check patient is still in hospital at horizon
           AND (lv.discharge_datetime IS NULL OR lv.discharge_datetime > {end_time} + '24 HOURS'::INTERVAL)       -- check patient is still at location at horizon
           AND (pt.date_of_death IS NULL OR pt.date_of_death > {end_time}) -- check patient is alive at time of prediction, so long as they are admitted to ICU

       ),

	  ICU_census AS
       (
         SELECT csn,
                hv_id,
                admission_dt,
                hl7_location,
                mrn
         FROM (
                SELECT csn,
                       hv_id,
                       admission_dt,
                       hl7_location,
                       ROW_NUMBER() OVER (PARTITION BY hl7_location ORDER BY admission_dt DESC) AS POSITION,
                       mrn
                FROM rough_ICU_census
              ) occupant_ordered
         WHERE occupant_ordered.position = 1 -- filters ghosts who may be lingering in a bed
       )

-- Now do the actual observations pull based on
SELECT
  	-- observation details
	  ob.visit_observation_id,
  	ob.hospital_visit_id,
  	ob.observation_datetime,

  	--,ob.visit_observation_type_id
  	ot.id_in_application,

  	-- label nicely
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
	 WHEN ot.id_in_application = '3040104280'	THEN 'Pain score, verbal at rest'
  	 WHEN ot.id_in_application = '3040104281' THEN 'Pain score, verbal on movement'
    WHEN ot.id_in_application = '6600' THEN 'All pressure areas observed?'

  	END AS vital,

  	ob.value_as_real,
  	ob.value_as_text,
  	ob.unit,

  	-- Admisssion time, discharge time, location, age can probably be removed when happy with this string
  	--loc.admission_datetime,
  	--loc.discharge_datetime,
  	lo.location_string,
  	demog.date_of_birth,

  	-- Can think about making this a decimal?
  	EXTRACT(YEAR FROM AGE(ob.observation_datetime, demog.date_of_birth)) AS age_at_obs,

    -- Include MRN and CSN
    mrn.mrn
    ,visit.encounter AS csn  -- NOTE changed for convenience - unclear whether encounter or hospital_visit_id are the correct csn
    --,visit.hospital_visit_id

    --Include some other demographics as well
    ,demog.ethnicity
    ,demog.home_postcode -- for index of multiple deprivation
    ,demog.sex

    -- Now include sideroom, unique ward name etc
    ,ward_location.bed
    ,ward_location.ward_raw
    ,ward_location.building
    ,ward_location.bed_type

    -- Generate our ICU admission outcome
    ,CASE
        WHEN visit.encounter IN (SELECT csn FROM ICU_census) THEN CAST(1 AS BIT)
        ELSE CAST(0 AS BIT)
    END AS icu_admission

    -- Hospital discharge date
    ,visit.discharge_datetime hospital_discharge_dt

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

    -- Now add the bed location (bed, sideroom, ward etc)
    INNER JOIN ward_location ON lo.location_string = ward_location.loc

-- Only recent obs at this stage
WHERE (ob.observation_datetime >= {end_time} - '{horizon}'::INTERVAL AND
       ob.observation_datetime <= {end_time})

-- Only use patients over 16
AND ob.observation_datetime - demog.date_of_birth > '{min_age}'::INTERVAL

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
  ,'3040104280'	-- Pain score, verbal at rest
  ,'3040104281'	-- Pain score, verbal on movement
  ,'6600'			-- All pressure areas observed?
)


-- Now ensure that we are only looking at obs from ward patients using previously built view -- should consider whether we actually need this?
AND lo.location_string IN ({location})


-- Now bin all rows where the observation isn't in the location admission window - could be using between here?
AND
ob.observation_datetime >= loc.admission_datetime

AND
(ob.observation_datetime <= loc.discharge_datetime OR loc.discharge_datetime IS NULL)

-- Only include specified CSNs
AND visit.encounter IN (SELECT csn from census)

ORDER BY visit.hospital_visit_id, ob.observation_datetime DESC
;
