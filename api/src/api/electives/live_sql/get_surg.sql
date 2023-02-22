SELECT DISTINCT patd.[PrimaryMrn],
	patd.[AgeInYears],
	patd.[Sex],
	patd.[FirstName],
	patd.[LastName],
	patd.[BirthDate],
	datewl.[DateValue] PlacedOnWaitingListDate,
	datedta.[DateValue] DecidedToAdmitDate,
	datesurg.[DateValue] SurgeryDate,
	datesurg.[DateValue] CaseRequestDate,
	todcase.[TimeValue] CaseRequestTimeOfDay,
	datecancel.[DateValue] CancelDate,
	scf.[PatientKey],
	scf.[PatientDurableKey],
	scf.[PrimaryService],
	scf.[ProcedureLevel],
	scf.[Classification],
	scf.[SurgeryPatientClass],
	scf.[AdmissionPatientClass],
	scf.[PrimaryAnesthesiaType],
	scf.[ReasonNotPerformed],
	scf.[Canceled],
	scf.[SurgicalCaseEpicId],
	scufx.[PlannedOperationStartInstant],
	scufx.[PlannedOperationEndInstant],
	scufx.[TouchTimeStartInstant],
	scufx.[TouchTimeEndInstant],
	scufx.[TouchTimeMinutes],
	scufx.[PostOperativeDestination],
	wlef.[AdmissionService],
	wlef.[ElectiveAdmissionType],
	wlef.[IntendedManagement],
	wlef.[Priority],
	wlef.[RemovalReason],
	wlef.[Status],
	wlef.[SurgicalService],
	wlef.[Type],
	wlef.[Count],
	scufx.[SurgicalCaseUclhKey],
	scufx.[SurgicalCaseKey],
	scufx.[CaseScheduleStatus],
	scufx.[CaseCancelReason],
	scufx.[CaseCancelReasonCode],
	scufx.[AsaRatingCode],
	pd.[Name],
	pd.[PatientFriendlyName],
	dd.[RoomName],
	dd.[DepartmentName],
	cbd.booked_destination
FROM [CABOODLE_REPORT].[dbo].[SurgicalCaseFact] scf
	LEFT JOIN [CABOODLE_REPORT].[dbo].[WaitingListEntryFact] wlef ON scf.[SurgicalCaseKey] = wlef.[SurgicalCaseKey]
	LEFT JOIN [CABOODLE_REPORT].[dbo].[SurgicalCaseUclhFactX] scufx ON scf.[SurgicalCaseKey] = scufx.[SurgicalCaseKey]
	LEFT JOIN [CABOODLE_REPORT].[dbo].[ProcedureDim] pd ON scf.[PrimaryProcedureKey] = pd.[ProcedureKey]
	LEFT JOIN [CABOODLE_REPORT].[dbo].[DepartmentDim] dd ON scf.[OperatingRoomKey] = dd.[DepartmentKey]
	LEFT JOIN [CABOODLE_REPORT].[dbo].[PatientDim] patd ON scf.[PatientDurableKey] = patd.[DurableKey]
	LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datewl ON wlef.[PlacedOnWaitingListDateKey] = datewl.[DateKey]
	LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datedta ON wlef.[DecidedToAdmitDateKey] = datedta.[DateKey]
	LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datesurg ON scf.[SurgeryDateKey] = datesurg.[DateKey] -- LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datecasereq ON scf.[CaseRequestDateKey] = datecasereq.[DateKey]
	LEFT JOIN [CABOODLE_REPORT].[dbo].[TimeOfDayDim] todcase ON scf.[CaseRequestTimeOfDayKey] = todcase.[TimeOfDayKey]
	LEFT JOIN [CABOODLE_REPORT].[dbo].[DateDim] datecancel ON scufx.[CancelDateKey] = datecancel.[DateKey]
	LEFT JOIN (
		SELECT PatientDurableKey,
			booked_destination,
			booking_date
		FROM (
				SELECT scf.PatientDurableKey,
					pof.StringResponse booked_destination,
					poax.OrderedDateKey booking_date,
					ROW_NUMBER() OVER (
						PARTITION BY scf.PatientDurableKey
						ORDER BY OrderedDateKey DESC
					) ranked_order
				FROM [CABOODLE_REPORT].[dbo].[SurgicalCaseFact] scf
					LEFT JOIN [CABOODLE_REPORT].[dbo].[ProcedureOrderAllUclhFactX] poax ON scf.[PatientDurableKey] = poax.[PatientDurableKey]
					LEFT JOIN [CABOODLE_REPORT].[dbo].ProcedureOrderQuestionAnswerUclhFactX pof ON poax.ProcedureOrderAllUclhKey = pof.ProcedureOrderAllUclhKey
				WHERE scf.[PatientDurableKey] > 0
					AND poax.OrderTypeCode = 78
					AND pof.SurveyQuestionKey = 1443
			) ac
		WHERE ac.ranked_order = 1
	) cbd on cbd.[PatientDurableKey] = scf.PatientDurableKey
WHERE scf.[PatientDurableKey] > 1
	AND scf.[PatientDurableKey] IS NOT NULL -- AND scf.[PrimaryService] != 'Obstetrics'
	-- AND scf.[PrimaryService] != 'Neurosurgery'
	-- AND scf.[PrimaryService] != 'Paediatric Dental'
	-- AND dd.[DepartmentName] != 'NHNN THEATRE SUITE'
	-- AND dd.[DepartmentName] != 'RNTNE THEATRE SUITE'
	-- AND dd.[DepartmentName] != 'EGA E02 LABOUR WARD'
	-- AND dd.[DepartmentName] != 'MCC H-1 THEATRE SUITE' -- AND dd.[DepartmentName] != 'UCH P02 ENDOSCOPY'
	-- AND dd.[DepartmentName] != 'UCH ANAESTHESIA DEPT'
	-- AND (
	-- 	wlef.[IntendedManagement] IN (
	-- 		'*Unspecified',
	-- 		'Inpatient',
	-- 		'Inpatient Series',
	-- 		'Night Admit Series'
	-- 	)
	-- 	OR wlef.[IntendedManagement] IS NULL
	-- )
	AND patd.[AgeInYears] >= 18
	AND scufx.CaseScheduleStatusCode = 1 -- 'Scheduled'
	AND scufx.[PlannedOperationStartInstant] >= :start_date
	AND scufx.[PlannedOperationStartInstant] < :end_date
