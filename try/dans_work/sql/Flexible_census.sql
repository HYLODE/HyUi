--- Query to determine if a patient is going to be admitted to ICU in a given time window
--- D Stein 2021, adapted from HyFLOW query

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
    AND location_string NOT LIKE '%%GWB L01W%%' -- GWB CCU


    --- Also only include places which have ever had a patient or visit:
    AND location_id IN (SELECT location_id FROM star.location_visit)


    ORDER BY loc
    ),

    rough_census AS
       (
        SELECT 	hv.encounter AS csn,
   		hv.hospital_visit_id AS hv_id,
         lv.admission_time    AS admission_dt,
         lv.discharge_time AS discharge_dt,
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


         WHERE (loc.location_string {location})--(loc.location_string LIKE 'T03%%' OR loc.location_string LIKE '%%T06PACU%%' OR loc.location_string LIKE '%%GWB L01 CC%%')
           AND hv.patient_class = 'INPATIENT'
           AND hv.admission_time IS NOT NULL -- check a valid hospital visit
           AND lv.admission_time <= {end_time} - '{horizon}'::INTERVAL                                     -- check location admission happened at or before horizon
           AND (hv.discharge_time IS NULL OR hv.discharge_time > {end_time} - '{horizon}'::INTERVAL)       -- check patient is still in hospital at horizon
           AND (lv.discharge_time IS NULL OR lv.discharge_time > {end_time})       -- check patient is still at location at horizon
           AND (pt.date_of_death IS NULL OR pt.date_of_death > {end_time}) -- check patient is alive at horizon

       ),
     census AS
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
                FROM rough_census
              ) occupant_ordered
         WHERE occupant_ordered.position = 1 -- filters ghosts who may be lingering in a bed
       )
SELECT csn,
       lv.admission_time   AS admission_dt,
       lv.discharge_time   AS discharge_dt,
       loc.location_string AS hl7_location,
       mrn
FROM census
       LEFT JOIN star.location_visit lv
                 ON census.hv_id = lv.hospital_visit_id
       LEFT JOIN star.location loc
                 ON lv.location_id = loc.location_id
WHERE loc.location_string {location} -- LIKE 'T03%%' OR loc.location_string LIKE '%%T06PACU%%' OR loc.location_string LIKE '%%GWB L01 CC%%'
ORDER BY csn, admission_dt
