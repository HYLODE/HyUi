SELECT --scufx.TouchTimeEndInstant,
    --  icu.CrossIcuStayStartInstant,
    icu.IcuLengthOfStay,
    icu.PatientDurableKey,
    scf.SurgicalCaseKey
FROM CABOODLE_REPORT.dbo.SurgicalCaseFact scf
    INNER JOIN CABOODLE_REPORT.dbo.IcuStayRegistryDataMart icu on icu.EncounterKey = scf.HospitalEncounterKey
    LEFT JOIN CABOODLE_REPORT.dbo.SurgicalCaseUclhFactX scufx on scufx.SurgicalCaseKey = scf.SurgicalCaseKey
WHERE icu.EncounterKey > 1 -- AND icu.IcuLengthOfStay > 0.3
    AND scufx.TouchTimeEndInstant IS NOT NULL
    AND DATEDIFF(
        MINUTE,
        scufx.TouchTimeEndInstant,
        icu.CrossIcuStayStartInstant
    ) < 1440
    AND DATEDIFF(
        MINUTE,
        scufx.TouchTimeEndInstant,
        icu.CrossICUStayStartInstant
    ) > -1440
    AND scufx.[PlannedOperationStartInstant] >= ?
    AND scufx.[PlannedOperationStartInstant] < ?
