SELECT DISTINCT ifact.PatientDurableKey,
    scufx.SurgicalCaseKey,
    scufx.PlannedOperationStartInstant,
    scufx.TouchTimeStartInstant,
    ifact.ImagingKey,
    itf.Narrative,
    eff.FinalizingDateKey,
    dd.DateValue,
    ifact.IsAbnormal
FROM CABOODLE_REPORT.dbo.SurgicalCaseFact scf
    LEFT JOIN CABOODLE_REPORT.dbo.SurgicalCaseUclhFactX scufx ON scf.[SurgicalCaseKey] = scufx.[SurgicalCaseKey]
    LEFT JOIN CABOODLE_REPORT.dbo.ImagingFact ifact ON ifact.PatientDurableKey = scf.PatientDurableKey
    LEFT JOIN CABOODLE_REPORT.dbo.ImagingTextFact itf ON itf.ImagingKey = ifact.ImagingKey
    LEFT JOIN CABOODLE_REPORT.dbo.EchoFindingFact eff ON ifact.ImagingKey = eff.ImagingKey
    LEFT JOIN CABOODLE_REPORT.dbo.DateDim dd ON eff.FinalizingDateKey = dd.DateKey
WHERE scufx.PlannedOperationStartInstant >= :start_date
    AND scufx.PlannedOperationStartInstant < :end_date
    and (
        dd.[DateValue] < CONVERT(date, scufx.PlannedOperationStartInstant)
        OR dd.[DateValue] < CONVERT(date, scufx.TouchTimeStartInstant)
    )
order by SurgicalCaseKey
