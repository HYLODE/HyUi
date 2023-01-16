SELECT DISTINCT patd.[PrimaryMrn],
    scufx.[PlannedOperationStartInstant],
    scf.[HospitalEncounterKey],
    scf.[Classification],
    scufx.[PostOperativeDestination],
    wlef.[AdmissionService],
    wlef.[ElectiveAdmissionType],
    wlef.[IntendedManagement],
    wlef.[Priority] --	,cbd.booked_destination
FROM [CABOODLE_REPORT].[dbo].[SurgicalCaseFact] scf
    LEFT JOIN [CABOODLE_REPORT].[dbo].[WaitingListEntryFact] wlef ON scf.[SurgicalCaseKey] = wlef.[SurgicalCaseKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[SurgicalCaseUclhFactX] scufx ON scf.[SurgicalCaseKey] = scufx.[SurgicalCaseKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[PatientDim] patd ON scf.[PatientDurableKey] = patd.[DurableKey]
WHERE scf.[PatientDurableKey] > 0
    AND scf.[PatientDurableKey] > 1
    AND scf.[PatientDurableKey] IS NOT NULL
    AND patd.[AgeInYears] >= 18
    AND scufx.[PlannedOperationStartInstant] >= :start_date
    AND scufx.[PlannedOperationStartInstant] < :end_date
    AND scufx.[CaseCancelReasonCode] != '581' -- 'Hospital Cancel - Admin Error'
    AND scf.[Classification] IN (
        'Elective',
        'Expedited (within 2 weeks on elective list)'
    ) -- AND scf.[Classification] NOT IN ('*Unknown', 'Immediate (Emergency list)','Immediate','Non-elective','*Unspecified','*Deleted','Urgent (Emergency list)','*Not Applicable')
    AND PostOperativeDestination = 'ITU/PACU Bed'
