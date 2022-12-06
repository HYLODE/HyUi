-- noinspection SqlNoDataSourceInspectionForFile

-- 2022-06-21
-- Query by J Hunter
-- see https://github.com/HYLODE/HyUi/issues/47#issuecomment-1160706270

   SELECT
        cnf.[PatientDurableKey]
        ,cnf.[CreationInstant]
      --  ,cnf.[Type]
      --  ,cnf.[AuthorType]
        ,cnavd.[StringValue]
        ,cnavd.[NumericValue]
      --  ,ad.[SmartDataElementEpicId]
        ,ad.[Name]
      --  ,ad.[Abbreviation]
        ,ad.[DataType]
     FROM [CABOODLE_REPORT].[dbo].[ClinicalNoteFact] cnf
     LEFT JOIN [CABOODLE_REPORT].[dbo].[ClinicalNoteAttributeValueDim] cnavd ON cnavd.[ClinicalNoteKey] = cnf.[ClinicalNoteKey]
     LEFT JOIN [CABOODLE_REPORT].[dbo].[AttributeDim] ad ON cnavd.[AttributeKey] = ad.[AttributeKey]
     WHERE cnf.[Type] = 'Anaesthesia Preprocedure Evaluation'
     AND ad.[SmartDataElementEpicId] IN ('EPIC#10040', 'UCLH#1325', 'EPIC#10008')
     AND cnf.[PatientDurableKey] IN (SELECT DISTINCT
          scf.[PatientDurableKey]
     FROM [CABOODLE_REPORT].[dbo].[SurgicalCaseFact] scf
         LEFT JOIN [CABOODLE_REPORT].[dbo].[WaitingListEntryFact] wlef ON scf.[SurgicalCaseKey] = wlef.[SurgicalCaseKey]
         LEFT JOIN [CABOODLE_REPORT].[dbo].[SurgicalCaseUclhFactX] scufx ON scf.[SurgicalCaseKey] = scufx.[SurgicalCaseKey]
         LEFT JOIN [CABOODLE_REPORT].[dbo].[ProcedureDim] pd ON scf.[PrimaryProcedureKey] = pd.[ProcedureKey]
         LEFT JOIN [CABOODLE_REPORT].[dbo].[DepartmentDim] dd ON scf.[OperatingRoomKey] = dd.[DepartmentKey]
         LEFT JOIN [CABOODLE_REPORT].[dbo].[PatientDim] patd ON scf.[PatientDurableKey] = patd.[DurableKey]
         LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datewl ON wlef.[PlacedOnWaitingListDateKey] = datewl.[DateKey]
         LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datedta ON wlef.[DecidedToAdmitDateKey] = datedta.[DateKey]
         LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datesurg ON scf.[SurgeryDateKey] = datesurg.[DateKey]
         LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datecasereq ON scf.[CaseRequestDateKey] = datecasereq.[DateKey]
         LEFT JOIN [CABOODLE_REPORT].[dbo].[TimeOfDayDim] todcase ON scf.[CaseRequestTimeOfDayKey] = todcase.[TimeOfDayKey]
         LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datecancel ON scufx.[CancelDateKey] = datecancel.[DateKey]
         WHERE scf.[PatientDurableKey] > 1
         AND scf.[PatientDurableKey] IS NOT NULL
         -- AND cnf.[CreationInstant] > CONVERT(DATE,DATEADD(YEAR, -1 ,CURRENT_TIMESTAMP))
         AND scf.[PrimaryService] != 'Obstetrics' AND scf.[PrimaryService] != 'Neurosurgery' AND scf.[PrimaryService] != 'Paediatric Dental'
         AND dd.[DepartmentName] != 'NHNN THEATRE SUITE' AND dd.[DepartmentName] != 'RNTNE THEATRE SUITE' AND dd.[DepartmentName] != 'EGA E02 LABOUR WARD'
         AND dd.[DepartmentName] != 'MCC H-1 THEATRE SUITE' AND dd.[DepartmentName] != 'UCH P02 ENDOSCOPY' AND dd.[DepartmentName] != 'UCH ANAESTHESIA DEPT'
         AND patd.[AgeInYears] >= 18
          AND  scufx.[PlannedOperationStartInstant] >= CONVERT(DATE,DATEADD(DAY, 0 ,CURRENT_TIMESTAMP)) AND [PlannedOperationStartInstant] <= CONVERT(DATE,DATEADD(DAY, :days_ahead ,CURRENT_TIMESTAMP))
         AND (wlef.[IntendedManagement] IN ('*Unspecified', 'Inpatient', 'Inpatient Series', 'Night Admit Series') OR wlef.[IntendedManagement] IS NULL))
