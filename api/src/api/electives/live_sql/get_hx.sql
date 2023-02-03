WITH surgical_pts AS (
    SELECT DISTINCT scf.[PatientDurableKey],
        scufx.[PlannedOperationStartInstant],
        scufx.[TouchTimeStartInstant],
        scufx.[SurgicalCaseKey]
    FROM [CABOODLE_REPORT].[dbo].[SurgicalCaseFact] scf
        LEFT JOIN [CABOODLE_REPORT].[dbo].[WaitingListEntryFact] wlef ON scf.[SurgicalCaseKey] = wlef.[SurgicalCaseKey]
        LEFT JOIN [CABOODLE_REPORT].[dbo].[SurgicalCaseUclhFactX] scufx ON wlef.[SurgicalCaseKey] = scufx.[SurgicalCaseKey]
        LEFT JOIN [CABOODLE_REPORT].[dbo].[DepartmentDim] dd ON scf.[OperatingRoomKey] = dd.[DepartmentKey]
        LEFT JOIN [CABOODLE_REPORT].[dbo].[PatientDim] patd ON scf.[PatientDurableKey] = patd.[DurableKey]
    WHERE scf.[PatientDurableKey] > 0
        AND scf.[PatientDurableKey] IS NOT NULL -- AND scf.[PrimaryService] != 'Obstetrics'
        -- AND scf.[PrimaryService] != 'Neurosurgery'
        -- AND scf.[PrimaryService] != 'Paediatric Dental'
        -- AND dd.[DepartmentName] != 'NHNN THEATRE SUITE'
        -- AND dd.[DepartmentName] != 'RNTNE THEATRE SUITE'
        AND patd.[AgeInYears] >= 18
        AND (
            wlef.[IntendedManagement] IN (
                '*Unspecified',
                'Inpatient',
                'Inpatient Series',
                'Night Admit Series'
            )
            OR wlef.[IntendedManagement] IS NULL
        )
        AND scufx.[PlannedOperationStartInstant] >= :start_date
        AND scufx.[PlannedOperationStartInstant] < :end_date
)
SELECT DISTINCT def.[PatientDurableKey],
    surgical_pts.[SurgicalCaseKey],
    def.[DiagnosisKey],
    dd.[Name] as DiagnosisDimName,
    ddim.[DateValue] AS DateEntered,
    ddim2.[DateValue] AS DateRemoved,
    surgical_pts.[PlannedOperationStartInstant] --   ,def.[ExternalDiagnosisConceptKey] this is not entered for any, -2 for all
    --   ,dtd.[Type] AS dtdCode
    --   ,dtd.[DisplayString] AS DiagnosisTerminologyDimName
    --   ,dtd.[TerminologyConceptKey]
    --   ,dtd.[Value] AS Code
    --   ,tcd.[StandardName]
    --   ,tcd.[Concept] AS StandardCode
    --   ,tcd.[Name] AS StandardName
FROM [CABOODLE_REPORT].[dbo].[DiagnosisEventFact] def
    LEFT JOIN [CABOODLE_REPORT].[dbo].[DiagnosisDim] dd ON dd.[DiagnosisKey] = def.[DiagnosisKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[DiagnosisTerminologyDim] dtd ON dtd.[DiagnosisKey] = dd.[DiagnosisKey]
    LEFT JOIN surgical_pts ON surgical_pts.[PatientDurableKey] = def.[PatientDurableKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] ddim ON UserEnteredDateKey = ddim.DateKey
    LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] ddim2 ON UserRemovedDateKey = ddim2.DateKey
    LEFT JOIN [CABOODLE_REPORT].[dbo].[TerminologyConceptDim] tcd ON dtd.[TerminologyConceptKey] = tcd.[TerminologyConceptKey]
WHERE def.[DiagnosisKey] > 0
    AND (
        ddim.[DateValue] < CONVERT(
            date,
            surgical_pts.[PlannedOperationStartInstant]
        )
        OR ddim.[DateValue] < CONVERT(date, surgical_pts.[TouchTimeStartInstant])
    )
    AND (
        ddim2.[DateValue] > CONVERT(
            date,
            surgical_pts.[PlannedOperationStartInstant]
        )
        OR ddim2.[DateValue] > CONVERT(date, surgical_pts.[TouchTimeStartInstant])
        OR ddim2.[DateValue] IS NULL
    )
