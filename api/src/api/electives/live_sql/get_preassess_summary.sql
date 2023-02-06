SELECT distinct cnf.[PatientDurableKey],
    cnf.[CreationInstant],
    cnavd.[StringValue],
    ad.[Name],
	cnavd.AttributeValueLineNumber_X
FROM [CABOODLE_REPORT].[dbo].[ClinicalNoteFact] cnf
    LEFT JOIN [CABOODLE_REPORT].[dbo].[ClinicalNoteAttributeValueDim] cnavd ON cnavd.[ClinicalNoteKey] = cnf.[ClinicalNoteKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[AttributeDim] ad ON cnavd.[AttributeKey] = ad.[AttributeKey]
	LEFT JOIN [CABOODLE_REPORT].[dbo].[SurgicalCaseFact] scf on cnf.PatientDurableKey = scf.PatientDurableKey
	LEFT JOIN [CABOODLE_REPORT].[dbo].[WaitingListEntryFact] wlef ON scf.[SurgicalCaseKey] = wlef.[SurgicalCaseKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[SurgicalCaseUclhFactX] scufx ON scf.[SurgicalCaseKey] = scufx.[SurgicalCaseKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[PatientDim] patd ON scf.[PatientDurableKey] = patd.[DurableKey]
WHERE cnf.[Type] = 'Anaesthesia Preprocedure Evaluation'
    AND ad.[SmartDataElementEpicId]= 'UK#071'
    AND scf.[PatientDurableKey] > 1
            AND scf.[PatientDurableKey] IS NOT NULL
            AND patd.[AgeInYears] >= 18
            AND scufx.PlannedOperationStartInstant >= '2023-02-06'
    AND scufx.PlannedOperationStartInstant < '2023-02-08'
            AND (
                wlef.[IntendedManagement] IN (
                    '*Unspecified',
                    'Inpatient',
                    'Inpatient Series',
                    'Night Admit Series'
                )
                OR wlef.[IntendedManagement] IS NULL
            )
