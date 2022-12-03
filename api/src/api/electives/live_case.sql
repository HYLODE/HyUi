-- noinspection SqlNoDataSourceInspectionForFile

-- 2022-08-02
-- Query by J Hunter
-- see https://github.com/HYLODE/HyUi/issues/47#issuecomment-1160706270
-- updated to fix join

    SELECT DISTINCT
        --    wlef.[PatientDurableKey]
            patd.[PrimaryMrn]
            ,scf.[SurgicalCaseEpicId]
            ,patd.[AgeInYears]
            ,patd.[FirstName]
            ,patd.[LastName]
            ,patd.[Sex]
            ,patd.[BirthDate]
        --   ,wlef.[SurgicalCaseKey]
        --   ,wlef.[ProcedureOrderKey]
        --   ,wlef.[PlacedOnWaitingListDateKey]
           ,datewl.[DateValue] PlacedOnWaitingListDate
        --   ,wlef.[DecidedToAdmitDateKey]
           ,datedta.[DateValue] DecidedToAdmitDate
        --   ,wlef.[DiagnosisComboKey]
        --   ,wlef.[ProcedureComboKey]
        --   ,wlef.[SurgicalProcedureComboKey]
           ,wlef.[AdmissionService]
           ,wlef.[ElectiveAdmissionType]
           ,wlef.[IntendedManagement]
           ,wlef.[Priority]
           ,wlef.[RemovalReason]
        --   ,wlef.[ShortNoticeDays]
           ,wlef.[Status]
           ,wlef.[Subgroup]
           ,wlef.[SurgicalService]
           ,wlef.[Type]
       --    ,wlef.[Count]
        --   ,wlef.[_CreationInstant]
           ,wlef.[_LastUpdatedInstant] LastUpdatedInstant
        --   ,wlef.[OfferedDateComboIdTypeId]
        --   ,wlef.[OfferedDateNumericId]
         --  ,wlef.[OfferedDateComboId]
        --   ,wlef.[DiagnosisComboIdTypeId]
        --   ,wlef.[DiagnosisNumericId]
        --   ,wlef.[DiagnosisComboId]
        --   ,wlef.[SurgicalProcedureComboIdTypeId]
        --   ,wlef.[SurgicalProcedureNumericId]
        --   ,wlef.[SurgicalProcedureComboId]
        --   ,wlef.[ProcedureComboIdTypeId]
        --   ,wlef.[ProcedureNumericId]
        --   ,wlef.[ProcedureComboId]
        --   ,scf.[SurgicalCaseEpicId]
           ,scf.[PatientKey]
           ,scf.[PatientDurableKey]
        --  ,scf.[PatientSourceDataDurableKey]
        --   ,scf.[AgeKey]
        --   ,scf.[PrimaryProcedureKey]
        --   ,scf.[PrimaryProcedureCodeKey]
        --   ,scf.[SurgeryDateKey]
           ,datesurg.[DateValue] SurgeryDate
        --   ,scf.[OperatingRoomKey]
        --   ,scf.[HospitalEncounterKey]
        --   ,scf.[SurgeryEncounterKey]
        --   ,scf.[CaseRequestDateKey]
        --   ,datesurg.[DateValue] CaseRequestDate
        --  ,scf.[CaseRequestTimeOfDayKey]
        --   ,todcase.[TimeValue] CaseRequestTimeOfDay
           ,scf.[PrimaryService]
           ,scf.[Classification]
           ,scf.[SurgeryPatientClass]
           ,scf.[AdmissionPatientClass]
           ,scf.[PrimaryAnesthesiaType]
           ,scf.[ReasonNotPerformed]
           ,scf.[Canceled]
        --   ,scf.[CaseDiagnosisComboIdTypeId]
        --   ,scf.[CaseDiagnosisNumericId]
        --   ,scf.[CaseDiagnosisComboId]
        --   ,scf.[PreprocedureDiagnosisComboKey]
        --   ,scf.[PreprocedureDiagnosisNumericId]
        --   ,scf.[PreprocedureDiagnosisComboId]
           ,scufx.[SurgicalCaseUclhKey]
           ,scufx.[SurgicalCaseKey]
           ,scufx.[CaseScheduleStatus]
           ,scufx.[CaseCancelReason]
           ,scufx.[CaseCancelReasonCode]
        --   ,scufx.[CancelDateKey]
           ,datecancel.[DateValue] CancelDate
           ,scufx.[PlannedOperationStartInstant]
           ,scufx.[PlannedOperationEndInstant]
           ,scufx.[PostOperativeDestination]
           ,pd.[Name]
           ,pd.[PatientFriendlyName]
           ,dd.[RoomName]
           ,dd.[DepartmentName]
      FROM [CABOODLE_REPORT].[dbo].[SurgicalCaseFact] scf
      LEFT JOIN [CABOODLE_REPORT].[dbo].[WaitingListEntryFact] wlef ON wlef.[SurgicalCaseKey] = scf.[SurgicalCaseKey]
      LEFT JOIN [CABOODLE_REPORT].[dbo].[SurgicalCaseUclhFactX] scufx ON scf.[SurgicalCaseKey] = scufx.[SurgicalCaseKey]
      LEFT JOIN [CABOODLE_REPORT].[dbo].[PatientDim] patd ON scf.[PatientDurableKey] = patd.[DurableKey]
      LEFT JOIN [CABOODLE_REPORT].[dbo].[ProcedureDim] pd ON scf.[PrimaryProcedureKey] = pd.[ProcedureKey]
      LEFT JOIN [CABOODLE_REPORT].[dbo].[DepartmentDim] dd ON scf.[OperatingRoomKey] = dd.[DepartmentKey]
      LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datewl ON wlef.[PlacedOnWaitingListDateKey] = datewl.[DateKey]
      LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datedta ON wlef.[DecidedToAdmitDateKey] = datedta.[DateKey]
      LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datesurg ON scf.[SurgeryDateKey] = datesurg.[DateKey]
      LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datecasereq ON scf.[CaseRequestDateKey] = datecasereq.[DateKey]
      LEFT JOIN [CABOODLE_REPORT].[dbo].[TimeOfDayDim] todcase ON scf.[CaseRequestTimeOfDayKey] = todcase.[TimeOfDayKey]
      LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datecancel ON scufx.[CancelDateKey] = datecancel.[DateKey]
      WHERE scf.[PatientDurableKey] > 1 AND scf.[PatientDurableKey] IS NOT NULL
    --  AND wlef.[SurgicalService] != '*Unspecified'
      AND scf.[PrimaryService] != 'Obstetrics' AND scf.[PrimaryService] != 'Neurosurgery' AND scf.[PrimaryService] != 'Paediatric Dental'
      AND scf.[PatientInFacilityDateKey] < 0
      AND dd.[DepartmentName] != 'NHNN THEATRE SUITE' AND dd.[DepartmentName] != 'RNTNE THEATRE SUITE' AND dd.[DepartmentName] != 'EGA E02 LABOUR WARD'
      AND dd.[DepartmentName] != 'MCC H-1 THEATRE SUITE' AND dd.[DepartmentName] != 'UCH ANAESTHESIA DEPT'
      --AND dd.[DepartmentName] != 'UCH P02 ENDOSCOPY'
      AND patd.[AgeInYears] >= 18
      AND (wlef.[IntendedManagement] IN ('*Unspecified', 'Inpatient', 'Inpatient Series', 'Night Admit Series') OR wlef.[IntendedManagement] IS NULL)
      AND  scufx.[PlannedOperationStartInstant] >= CONVERT(DATE,DATEADD(DAY, 0 ,CURRENT_TIMESTAMP)) AND [PlannedOperationStartInstant] <= CONVERT(DATE,DATEADD(DAY, :days_ahead ,CURRENT_TIMESTAMP))
      ORDER BY  datesurg.[DateValue],dd.[DepartmentName],dd.[RoomName] ASC
