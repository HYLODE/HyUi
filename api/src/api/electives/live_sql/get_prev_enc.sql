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
        AND scf.[PatientDurableKey] IS NOT NULL
        AND scf.[PrimaryService] != 'Obstetrics'
        AND scf.[PrimaryService] != 'Neurosurgery'
        AND scf.[PrimaryService] != 'Paediatric Dental'
        AND dd.[DepartmentName] != 'NHNN THEATRE SUITE'
        AND dd.[DepartmentName] != 'RNTNE THEATRE SUITE'
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
        AND scufx.[PlannedOperationStartInstant] >= ?
        AND scufx.[PlannedOperationStartInstant] < ?
)
SELECT DISTINCT ef.[EncounterKey],
    ef.[PatientKey],
    ef.[PatientDurableKey] --      ,ef.[DateKey]
,
    ddim.[DateValue] AS StartDate --      ,ef.[EndDateKey]
,
    ddim2.[DateValue] AS EndDate,
    ef.[DepartmentKey],
    depdim.[DepartmentSpecialty],
    ef.[Type],
    ef.[EncounterEpicCsn] --      ,ef.[Date]
,
    ef.[EndInstant] --     ,ef.[DerivedEncounterStatus]
,
    ef.[PatientClass],
    ef.[IsHospitalAdmission],
    ef.[IsEdVisit],
    ef.[IsOutpatientFaceToFaceVisit],
    surgical_pts.[SurgicalCaseKey],
    surgical_pts.[PlannedOperationStartInstant]
FROM [CABOODLE_REPORT].[dbo].[EncounterFact] ef
    LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] ddim ON ddim.[DateKey] = ef.[DateKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] ddim2 ON ddim2.[DateKey] = ef.[EndDateKey]
    LEFT JOIN surgical_pts ON surgical_pts.[PatientDurableKey] = ef.[PatientDurableKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[DepartmentDim] depdim ON ef.[DepartmentKey] = depdim.[DepartmentKey]
WHERE surgical_pts.[PlannedOperationStartInstant] IS NOT NULL
    AND (
        ef.[EndInstant] < surgical_pts.[PlannedOperationStartInstant]
    )
    AND (
        (ef.[IsEdVisit] = '1')
        OR (ef.[IsOutpatientFaceToFaceVisit] = '1')
        OR (ef.[IsHospitalAdmission] = '1')
    )
