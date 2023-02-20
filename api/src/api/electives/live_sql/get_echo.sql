WITH surgical_pts AS (
    SELECT DISTINCT scf.[PatientDurableKey],
        scf.[SurgicalCaseKey],
        scufx.[PlannedOperationStartInstant],
        scufx.[TouchTimeStartInstant],
        scf.[Classification]
    FROM [CABOODLE_REPORT].[dbo].[SurgicalCaseFact] scf
        LEFT JOIN [CABOODLE_REPORT].[dbo].[WaitingListEntryFact] wlef ON scf.[SurgicalCaseKey] = wlef.[SurgicalCaseKey]
        LEFT JOIN [CABOODLE_REPORT].[dbo].[SurgicalCaseUclhFactX] scufx ON wlef.[SurgicalCaseKey] = scufx.[SurgicalCaseKey]
        LEFT JOIN [CABOODLE_REPORT].[dbo].[DepartmentDim] dd ON scf.[OperatingRoomKey] = dd.[DepartmentKey]
        LEFT JOIN [CABOODLE_REPORT].[dbo].[PatientDim] patd ON scf.[PatientDurableKey] = patd.[DurableKey]
    WHERE scf.[PatientDurableKey] > 0
        AND scf.[PatientDurableKey] IS NOT NULL
        AND scf.[PrimaryService] != 'Obstetrics'
        AND scf.[PrimaryService] != 'Neurosurgery'
        AND scf.[PrimaryService] != 'Paediatric Dental'
        AND dd.[DepartmentName] != 'NHNN THEATRE SUITE'
        AND dd.[DepartmentName] != 'RNTNE THEATRE SUITE'
        AND patd.[AgeInYears] >= 18 --   AND ( scufx.[PlannedOperationStartInstant] < CONVERT(DATE,DATEADD(DAY,1,CURRENT_TIMESTAMP))
        AND (
            wlef.[IntendedManagement] IN (
                '*Unspecified',
                'Inpatient',
                'Inpatient Series',
                'Night Admit Series'
            )
            OR wlef.[IntendedManagement] IS NULL
        ) --     )
        AND scufx.[PlannedOperationStartInstant] >= ?
        AND scufx.[PlannedOperationStartInstant] < ?
)
SELECT DISTINCT ifact.[PatientDurableKey],
    surgical_pts.[SurgicalCaseKey],
    eff.[ImagingKey],
    eff.[FindingType],
    eff.[FindingName],
    eff.[StringValue],
    eff.[NumericValue],
    eff.[Unit],
    ddim.[DateValue] AS EchoStartDate,
    ddim2.[DateValue] AS EchoFinalisedDate,
    surgical_pts.[PlannedOperationStartInstant] --    ,eff.[EchoFindingKey]
    --    ,eff.[FindingAttributeKey]
    --    ,eff.[FinalizingDateKey]
    --    ,eff.[DateValue]
    --   ,ifact.[PatientDurableKey]
    --   ,ifact.[ExamStartDateKey]
FROM [CABOODLE_REPORT].[dbo].[EchoFindingFact] eff
    LEFT JOIN [CABOODLE_REPORT].[dbo].[ImagingFact] ifact ON ifact.[ImagingKey] = eff.[ImagingKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[AttributeDim] ad ON eff.[FindingAttributeKey] = ad.[AttributeKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] ddim ON ddim.[DateKey] = ifact.[ExamStartDateKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] ddim2 ON ddim2.[DateKey] = eff.[FinalizingDateKey]
    LEFT JOIN surgical_pts ON surgical_pts.[PatientDurableKey] = ifact.[PatientDurableKey]
WHERE eff.[ImagingKey] > 1
    AND ifact.[PatientDurableKey] > 1
    AND (
        ddim2.[DateValue] < CONVERT(
            date,
            surgical_pts.[PlannedOperationStartInstant]
        )
        OR ddim2.[DateValue] < CONVERT(date, surgical_pts.[TouchTimeStartInstant])
    )
    AND surgical_pts.[PlannedOperationStartInstant] IS NOT NULL
    AND (
        (surgical_pts.[Classification] = 'Elective')
        OR (
            surgical_pts.[Classification] = 'Expedited (within 2 weeks on elective list)'
        )
    )
