WITH surgical_pts AS (
    SELECT DISTINCT scf.[PatientDurableKey],
        scufx.[SurgicalCaseKey],
        scufx.[PlannedOperationStartInstant],
        scufx.[TouchTimeStartInstant]
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
SELECT surgical_pts.[SurgicalCaseKey],
    surgical_pts.[PlannedOperationStartInstant] --,lcrf.[ResultStatus]
,
    lcd.[Name],
    lcrf.[Value] --,lcrf.[NumericValue]
,
    lcrf.[ResultInstant],
    surgical_pts.[PatientDurableKey]
FROM [CABOODLE_REPORT].[dbo].[LabComponentResultFact] lcrf
    LEFT JOIN [CABOODLE_REPORT].[dbo].[LabComponentDim] lcd ON lcrf.[LabComponentKey] = lcd.[LabComponentKey]
    LEFT JOIN surgical_pts ON surgical_pts.[PatientDurableKey] = lcrf.[PatientDurableKey]
WHERE lcrf.[PatientDurableKey] > 1
    AND surgical_pts.[SurgicalCaseKey] IS NOT NULL
    AND surgical_pts.[PlannedOperationStartInstant] IS NOT NULL
    AND lcrf.[ResultInstant] < CONVERT(
        date,
        surgical_pts.[PlannedOperationStartInstant]
    )
    AND lcrf.[ResultInstant] > DATEADD(
        month,
        -4,
        CONVERT(
            date,
            surgical_pts.[PlannedOperationStartInstant]
        )
    )
    AND lcd.[Name] IN (
        'Creatinine',
        'Haemoglobin (g/L)',
        'White cell count',
        'Platelet count',
        'Sodium',
        'Albumin',
        'Bilirubin (total)',
        'INR',
        'C-reactive protein'
    )
