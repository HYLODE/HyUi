  SELECT

     cr.consultation_request_id
    --,cr.valid_from
    ,cr.scheduled_datetime
    ,cr.status_change_datetime
    ,cr.hospital_visit_id
    ,hv.encounter
    ,ct.code
    ,ct.name


    FROM star.consultation_request cr
    LEFT JOIN star.consultation_type ct ON cr.consultation_type_id = ct.consultation_type_id
    LEFT JOIN star.hospital_visit hv ON cr.hospital_visit_id = hv.hospital_visit_id

    WHERE
        cr.closed_due_to_discharge = false
        AND
        cr.cancelled = false
        AND
        cr.scheduled_datetime > :horizon_dt
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
		hv.encounter = ANY( :encounter_ids )
