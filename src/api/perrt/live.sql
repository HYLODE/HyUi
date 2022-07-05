-- 2022-06-24 
-- return recent vitals
-- V simple view that finds recent observations 
-- for current inpatients in the last few minutes
-- runs within a few seconds

-- return recent vitals
WITH 
-- FIRST RETURN JUST THE MOST RECENT (TAIL) OBS WITHIN a TIME WINDOW
obs_tail AS 
    (SELECT visit_observation_id, ob_tail_i FROM (
        SELECT
            ob.visit_observation_id
            ,ob.hospital_visit_id
            ,ob.visit_observation_type_id
            ,row_number() over 
                (partition BY 
                    ob.hospital_visit_id, ob.visit_observation_type_id
                    ORDER BY ob.observation_datetime DESC) ob_tail_i
        FROM star.visit_observation ob
        WHERE ob.observation_datetime > NOW() - '12 HOURS'::INTERVAL 
    ) ob WHERE ob_tail_i <= 1
    ORDER BY hospital_visit_id, visit_observation_id 
),
-- NOW RETURN DETAILS FROM THOSE OBS
obs AS
    (SELECT
        ob.visit_observation_id
      ,obs_tail.ob_tail_i
      ,ob.hospital_visit_id
      ,ob.observation_datetime
      ,ot.id_in_application
      ,ob.value_as_real
      ,ob.value_as_text
      ,ob.unit 
    FROM star.visit_observation ob
    INNER JOIN obs_tail ON ob.visit_observation_id = obs_tail.visit_observation_id
    LEFT JOIN star.visit_observation_type ot ON ob.visit_observation_type_id = ot.visit_observation_type_id
    WHERE
    ot.id_in_application in 
      (
       '10'            --'SpO2'                  -- 602063230
      ,'5'            --'BP'                    -- 602063234
      ,'3040109304'   --'Room Air or Oxygen'    -- 602063268
      ,'6'            --'Temp'                  -- 602063248
      ,'8'            --'Pulse'                 -- 602063237
      ,'9'            --'Resp'                  -- 602063257
      ,'6466'         -- Level of consciousness
      ,'28315'        -- NEWS score Scale 1     -- 47175382
      ,'28316'        -- NEWS score Scale 2     -- 47175920
        )
    ),
-- NOW PREPARE THE DEMOGRAPHIC AND BED INFO
loc AS
    (SELECT * FROM (SELECT
         vd.hospital_visit_id
        ,live_mrn.mrn
        ,cd.lastname
        ,cd.firstname
        ,cd.sex
        ,cd.date_of_birth
        -- ,vd.location_id
        -- ugly HL7 location string 
        ,lo.location_string
        ,dept.name dept_name
        ,room.name room_name  
        ,bed.hl7string bed_hl7
        -- time admitted to that bed/theatre/scan etc.
        ,vo.admission_time hosp_admit_dt
        ,vd.admission_time bed_admit_dt
        ,row_number() over (partition BY vd.hospital_visit_id ORDER BY vd.admission_time DESC) bed_tail_i
        
    FROM star.location_visit vd
        INNER JOIN star.location lo ON vd.location_id = lo.location_id
        INNER JOIN star.department dept ON lo.department_id = dept.department_id
        INNER JOIN star.room ON lo.room_id = room.room_id
        INNER JOIN star.bed ON lo.bed_id = bed.bed_id
        INNER JOIN star.hospital_visit vo ON vd.hospital_visit_id = vo.hospital_visit_id 
        INNER JOIN star.core_demographic cd ON vo.mrn_id = cd.mrn_id
        -- get current hospital number
        INNER JOIN star.mrn original_mrn ON vo.mrn_id = original_mrn.mrn_id
        -- get mrn to live mapping 
        INNER JOIN star.mrn_to_live mtl ON vo.mrn_id = mtl.mrn_id 
        -- get live mrn 
        INNER JOIN star.mrn live_mrn ON mtl.live_mrn_id = live_mrn.mrn_id 
    WHERE 
        vo.admission_time IS NOT NULL
        AND
        vo.discharge_time IS NULL
        AND
        cd.date_of_death IS NULL
        AND 
        vo.patient_class = ANY('{INPATIENT,DAY_CASE,EMERGENCY}')
        AND
        dept.name LIKE 'UCH%'
) bed_tail WHERE bed_tail_i = 1),
consults AS (
    SELECT
    
     cr.consultation_request_id
    ,cr.valid_from
    ,cr.scheduled_datetime
    ,cr.hospital_visit_id
    ,ct.code
    ,ct.name
    ,con_tail.con_i
    
    FROM star.consultation_request cr
    LEFT JOIN star.consultation_type ct ON cr.consultation_type_id = ct.consultation_type_id
    LEFT JOIN (
        -- so '1' represents most recent consult
        SELECT
         *
        ,row_number() over (partition BY consults.hospital_visit_id ORDER BY consults.valid_from DESC) con_i
        FROM star.consultation_request consults
        LEFT JOIN star.consultation_type ct ON consults.consultation_type_id = ct.consultation_type_id
        WHERE 
            consults.scheduled_datetime > NOW() - INTERVAL '30 DAYS'
            AND
            ct.code IN ('CON134', 'CON6')
        ) con_tail 
     ON cr.consultation_request_id = con_tail.consultation_request_id 
    
    WHERE
        cr.closed_due_to_discharge = false
        AND
        cr.cancelled = false
        AND
        cr.scheduled_datetime > NOW() - INTERVAL '30 DAYS'
        AND
        --   ct.name IN (
        --   'Inpatient consult to PERRT', -- CON134
        --   'Inpatient Consult to Symptom Control and Palliative Care', -- CON27
        --   'Inpatient Consult to Transforming end of life care team', --
        --   'Inpatient consult to Intensivist', -- CON6
        --   'Inpatient consult to Social Work' -- CON65
        --   )
        ct.code IN ('CON134', 'CON6')
        AND 
        con_tail.con_i = 1
)

-- FINALLY MERGE bed/demographic/consults info with obs
SELECT
     obs.visit_observation_id
    ,obs.ob_tail_i
    ,obs.observation_datetime
    ,obs.id_in_application
    ,obs.value_as_real
    ,obs.value_as_text
    ,obs.unit
    ,loc.mrn
    ,loc.lastname
    ,loc.firstname
    ,loc.sex
    ,loc.date_of_birth
    ,loc.bed_admit_dt
    ,loc.dept_name
    ,loc.room_name
    ,loc.bed_hl7
    ,con.scheduled_datetime perrt_consult_datetime
FROM obs
INNER JOIN loc ON obs.hospital_visit_id = loc.hospital_visit_id
LEFT JOIN consults con ON obs.hospital_visit_id = con.hospital_visit_id
ORDER BY obs.observation_datetime DESC

