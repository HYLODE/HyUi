WITH pa AS (
    SELECT distinct cnf.[PatientDurableKey],
        cnf.[CreationInstant],
        cnavd.[StringValue],
        ad.[Name],
        ad.[SmartDataElementEpicId],
        cnavd.AttributeValueLineNumber_X line_num,
        ROW_NUMBER() OVER (
            PARTITION BY cnf.[PatientDurableKey]
            ORDER BY cnf.[CreationInstant] DESC
        ) AS RowNumber
    FROM [CABOODLE_REPORT].[dbo].[ClinicalNoteFact] cnf
        LEFT JOIN [CABOODLE_REPORT].[dbo].[ClinicalNoteAttributeValueDim] cnavd ON cnavd.[ClinicalNoteKey] = cnf.[ClinicalNoteKey]
        LEFT JOIN [CABOODLE_REPORT].[dbo].[AttributeDim] ad ON cnavd.[AttributeKey] = ad.[AttributeKey]
        LEFT JOIN [CABOODLE_REPORT].[dbo].[SurgicalCaseFact] scf on cnf.PatientDurableKey = scf.PatientDurableKey
        LEFT JOIN [CABOODLE_REPORT].[dbo].[WaitingListEntryFact] wlef ON scf.[SurgicalCaseKey] = wlef.[SurgicalCaseKey]
        LEFT JOIN [CABOODLE_REPORT].[dbo].[SurgicalCaseUclhFactX] scufx ON scf.[SurgicalCaseKey] = scufx.[SurgicalCaseKey]
        LEFT JOIN [CABOODLE_REPORT].[dbo].[PatientDim] patd ON scf.[PatientDurableKey] = patd.[DurableKey]
    WHERE cnf.[Type] = 'Anaesthesia Preprocedure Evaluation'
        AND ad.[SmartDataElementEpicId] IN ('UK#071', 'UCLH#3616', 'UCLH#548')
        AND scf.[PatientDurableKey] > 1
        AND scf.[PatientDurableKey] IS NOT NULL
        AND patd.[AgeInYears] >= 18
        AND scufx.PlannedOperationStartInstant >= :start_date
        AND scufx.PlannedOperationStartInstant < :end_date
        AND (
            wlef.[IntendedManagement] IN (
                '*Unspecified',
                'Inpatient',
                'Inpatient Series',
                'Night Admit Series'
            )
            OR wlef.[IntendedManagement] IS NULL
        )
)
SELECT pa.[PatientDurableKey],
    pa.CreationInstant as pac_date,
    MAX(
        CASE
            WHEN pa.[SmartDataElementEpicId] = 'UK#071' THEN pa.[StringValue]
        END
    ) AS pac_anaesthetic_review,
    MAX(
        CASE
            WHEN pa.[SmartDataElementEpicId] = 'UCLH#3616' THEN pa.[StringValue]
        END
    ) AS pac_nursing_outcome,
    MAX(
        CASE
            WHEN pa.[SmartDataElementEpicId] = 'UCLH#548' THEN pa.[StringValue]
        END
    ) AS pac_nursing_issues
FROM pa
WHERE pa.RowNumber = 1
GROUP BY pa.[PatientDurableKey],
    pa.CreationInstant
