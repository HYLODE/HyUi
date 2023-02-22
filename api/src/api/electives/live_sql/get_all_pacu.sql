with cbd as (
    SELECT PatientDurableKey,
        booked_destination,
        booking_date
    FROM (
            SELECT scf.PatientDurableKey,
                pof.StringResponse booked_destination,
                poax.OrderedDateKey booking_date,
                ROW_NUMBER() OVER (
                    PARTITION BY scf.PatientDurableKey
                    ORDER BY OrderedDateKey DESC
                ) ranked_order
            FROM [CABOODLE_REPORT].[dbo].[SurgicalCaseFact] scf
                LEFT JOIN [CABOODLE_REPORT].[dbo].[ProcedureOrderAllUclhFactX] poax ON scf.[PatientDurableKey] = poax.[PatientDurableKey]
                LEFT JOIN [CABOODLE_REPORT].[dbo].ProcedureOrderQuestionAnswerUclhFactX pof ON poax.ProcedureOrderAllUclhKey = pof.ProcedureOrderAllUclhKey
            WHERE scf.[PatientDurableKey] > 0
                AND poax.OrderTypeCode = 78
                AND pof.SurveyQuestionKey = 1443
        ) ac
    WHERE ac.ranked_order = 1
),
pre as (
    SELECT cnavd.[StringValue] preassess_destination,
        cnf.PatientDurableKey
    FROM [CABOODLE_REPORT].[dbo].[ClinicalNoteFact] cnf
        LEFT JOIN [CABOODLE_REPORT].[dbo].[ClinicalNoteAttributeValueDim] cnavd ON cnavd.[ClinicalNoteKey] = cnf.[ClinicalNoteKey]
        LEFT JOIN [CABOODLE_REPORT].[dbo].[AttributeDim] ad ON cnavd.[AttributeKey] = ad.[AttributeKey]
    WHERE cnf.[Type] = 'Anaesthesia Preprocedure Evaluation'
        AND ad.[SmartDataElementEpicId] = 'UCLH#1325' -- preassessment case booking
)
SELECT DISTINCT patd.[PrimaryMrn],
    patd.FirstName,
    patd.LastName,
    patd.Sex,
    patd.BirthDate,
    scufx.[PlannedOperationStartInstant],
    scf.[HospitalEncounterKey],
    scf.[Classification],
    scufx.[PostOperativeDestination],
    wlef.[AdmissionService],
    wlef.[ElectiveAdmissionType],
    poax.OrderedDateKey booking_date,
    wlef.[IntendedManagement],
    PostOperativeDestination,
    pof.StringResponse booked_destination,
    pre.preassess_destination,
    pd.Name,
    wlef.[Priority],
    scufx.CaseScheduleStatus
FROM [CABOODLE_REPORT].[dbo].[SurgicalCaseFact] scf
    LEFT JOIN [CABOODLE_REPORT].[dbo].[WaitingListEntryFact] wlef ON scf.[SurgicalCaseKey] = wlef.[SurgicalCaseKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[SurgicalCaseUclhFactX] scufx ON scf.[SurgicalCaseKey] = scufx.[SurgicalCaseKey]
    LEfT JOIN [CABOODLE_REPORT].[dbo].[PatientDim] patd ON scf.[PatientDurableKey] = patd.[DurableKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[DepartmentDim] dd ON scf.[OperatingRoomKey] = dd.[DepartmentKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[ProcedureDim] pd ON scf.[PrimaryProcedureKey] = pd.[ProcedureKey]
    left join pre on pre.PatientDurableKey = scf.PatientDurableKey
    LEFT JOIN [CABOODLE_REPORT].[dbo].[ProcedureOrderAllUclhFactX] poax ON scf.CaseRequestDateKey = poax.OrderedDateKey
    AND poax.PatientDurableKey = scf.PatientDurableKey
    LEFT JOIN [CABOODLE_REPORT].[dbo].ProcedureOrderQuestionAnswerUclhFactX pof ON poax.ProcedureOrderAllUclhKey = pof.ProcedureOrderAllUclhKey
WHERE scf.[PatientDurableKey] > 1
    AND scf.[PatientDurableKey] IS NOT NULL
    AND patd.[AgeInYears] >= 18
    AND scufx.[PlannedOperationStartInstant] >= '2023-01-10'
    AND scufx.[PlannedOperationStartInstant] < '2023-01-11'
    AND scufx.[CaseCancelReasonCode] != '581' -- 'Hospital Cancel - Admin Error'
    AND scufx.CaseScheduleStatus = 'Scheduled' --  AND scf.[Classification] IN (
    --      'Elective',
    --     'Expedited (within 2 weeks on elective list)'
    --) -- AND scf.[Classification] NOT IN ('*Unknown', 'Immediate (Emergency list)','Immediate','Non-elective','*Unspecified','*Deleted','Urgent (Emergency list)','*Not Applicable')
    AND (
        PostOperativeDestination = 'ITU/PACU Bed'
        OR pof.StringResponse = 'ITU/PACU Bed'
        or preassess_destination = 'ITU/PACU Bed'
    )
    AND dd.[DepartmentName] != 'NHNN THEATRE SUITE'
    AND poax.OrderTypeCode = 78
    AND pof.SurveyQuestionKey = 1443
ORDER BY LastName
