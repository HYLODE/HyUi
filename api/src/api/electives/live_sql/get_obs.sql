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
        AND scf.[Classification] IN (
            'Elective',
            'Expedited (within 2 weeks on elective list)'
        )
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
    surgical_pts.[PlannedOperationStartInstant],
    surgical_pts.[PatientDurableKey],
    fvf.[Value],
    fvf.[NumericValue],
    fvf.[FirstDocumentedInstant],
    fvf.[TakenInstant],
    frd.[DisplayName]
FROM [CABOODLE_REPORT].[dbo].[FlowsheetValueFact] fvf
    LEFT JOIN surgical_pts ON surgical_pts.[PatientDurableKey] = fvf.[PatientDurableKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[FlowsheetRowDim] frd ON fvf.[FlowsheetRowKey] = frd.[FlowsheetRowKey]
WHERE fvf.[PatientDurableKey] > 1
    AND surgical_pts.[SurgicalCaseKey] IS NOT NULL
    AND surgical_pts.[PlannedOperationStartInstant] IS NOT NULL
    AND fvf.[FirstDocumentedInstant] < CONVERT(
        date,
        surgical_pts.[PlannedOperationStartInstant]
    )
    AND fvf.[FirstDocumentedInstant] > DATEADD(
        month,
        -4,
        CONVERT(
            date,
            surgical_pts.[PlannedOperationStartInstant]
        )
    )
    AND fvf.[TakenInstant] < CONVERT(
        date,
        surgical_pts.[PlannedOperationStartInstant]
    )
    AND fvf.[TakenInstant] > DATEADD(
        month,
        -4,
        CONVERT(
            date,
            surgical_pts.[PlannedOperationStartInstant]
        )
    )
    AND frd.[Name] IN (
        'PULSE',
        'PULSE OXIMETRY',
        'BLOOD PRESSURE',
        'RESPIRATIONS',
        'TEMPERATURE',
        'R BAR BMI (CALCULATED)',
        'R BMI',
        'R AIR OR OXYGEN'
    )
