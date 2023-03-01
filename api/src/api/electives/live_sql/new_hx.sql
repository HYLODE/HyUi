WITH surg AS (
    SELECT DISTINCT patd.[PrimaryMrn],
        scf.[PatientDurableKey],
        scf.[SurgicalCaseEpicId],
        scufx.[PlannedOperationStartInstant],
        scufx.[SurgicalCaseUclhKey],
        scufx.[SurgicalCaseKey]
    FROM [CABOODLE_REPORT].[dbo].[SurgicalCaseFact] scf
        LEFT JOIN [CABOODLE_REPORT].[dbo].[SurgicalCaseUclhFactX] scufx ON scf.[SurgicalCaseKey] = scufx.[SurgicalCaseKey]
        LEFT JOIN [CABOODLE_REPORT].[dbo].[PatientDim] patd ON scf.[PatientDurableKey] = patd.[DurableKey]
    WHERE scf.[PatientDurableKey] > 1
        AND scf.[PatientDurableKey] IS NOT NULL
        AND patd.[AgeInYears] >= 18
        AND scufx.[PlannedOperationStartInstant] >= :start_date
        AND scufx.[PlannedOperationStartInstant] < :end_date
        AND scufx.[CaseCancelReasonCode] != '581'
)
SELECT DISTINCT surg.PatientDurableKey,
    surg.SurgicalCaseKey,
    -- dtd.Type,
    dtd.Value,
    dtd.DisplayString
FROM surg
    LEFT JOIN CABOODLE_REPORT.dbo.DiagnosisEventFact def ON def.PatientDurableKey = surg.PatientDurableKey -- LEFT JOIN CABOODLE_REPORT.dbo.DiagnosisDim dd on dd.DiagnosisKey = def.DiagnosisKey
    LEFT JOIN CABOODLE_REPORT.dbo.DiagnosisTerminologyDim dtd on def.DiagnosisKey = dtd.DiagnosisKey
WHERE dtd.Type = 'ICD-10-UK'
