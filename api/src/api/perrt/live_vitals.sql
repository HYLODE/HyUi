-- noinspection SqlNoDataSourceInspectionForFile
-- read just vitals
-- two parameters:

SELECT ob.visit_observation_id
     , ob.hospital_visit_id
     , ob.observation_datetime
     , ot.id_in_application
     , ob.value_as_real
     , ob.value_as_text
     , ob.unit
     -- include encounter so you can test the query from the front end
     , hv.encounter
FROM star.visit_observation ob
         LEFT JOIN star.visit_observation_type ot ON ob.visit_observation_type_id = ot.visit_observation_type_id
         LEFT JOIN star.hospital_visit hv ON ob.hospital_visit_id = hv.hospital_visit_id
-- see param in next line
WHERE ob.observation_datetime > :horizon_dt
  AND ot.id_in_application in
      (
       '10' --'SpO2'                  -- 602063230
          , '5' --'BP'                    -- 602063234
          , '3040109304' --'Room Air or Oxygen'    -- 602063268
          , '6' --'Temp'                  -- 602063248
          , '8' --'Pulse'                 -- 602063237
          , '9' --'Resp'                  -- 602063257
          , '6466' -- Level of consciousness
          , '28315' -- NEWS score Scale 1     -- 47175382
          , '28316' -- NEWS score Scale 2     -- 47175920
          )
  -- see param in next line
  AND hv.encounter = ANY( :encounter_ids )
