SELECT cnf.[PatientDurableKey],
    cnf.[CreationInstant],
    cnf.[Type],
    cnf.[AuthorType],
    cnavd.[StringValue],
    cnavd.[NumericValue],
    cnavd.[DateValue],
    ad.[SmartDataElementEpicId],
    ad.[Name],
    ad.[Abbreviation],
    ad.[DataType],
    ad.[ConceptType],
    ad.[ConceptValue]
FROM [CABOODLE_REPORT].[dbo].[ClinicalNoteFact] cnf
    LEFT JOIN [CABOODLE_REPORT].[dbo].[ClinicalNoteAttributeValueDim] cnavd ON cnavd.[ClinicalNoteKey] = cnf.[ClinicalNoteKey]
    LEFT JOIN [CABOODLE_REPORT].[dbo].[AttributeDim] ad ON cnavd.[AttributeKey] = ad.[AttributeKey]
WHERE cnf.[Type] = 'Anaesthesia Preprocedure Evaluation'
    AND ad.[SmartDataElementEpicId] IN (
        'EPIC#10040',
        'EPIC#34590',
        --'UCLH#1047', UCLH#1700',
        'EPIC#10008',
        'UCLH#3616',
        'UCLH#1325',
        'UCLH#3069',
        'EPIC#20239',
        'UCLH#015',
        'EPIC#10077',
        'EPIC#10060',
        'EPIC#10081',
        'UCLH#1254',
        'UCLH#016',
        'EPIC#38214',
        'EPIC#31000061200',
        'UCLH#020',
        'UCLH#1728',
        'UCLH#1253',
        'UCLH#5454',
        'EPIC#4479',
        'EPIC#4474',
        'EPIC#4476',
        'EPIC#4478',
        'UCLH#451',
        'UCLH#5254',
        'EPIC#10004',
        'EPIC#HPI0095',
        'EPIC#HPI0264',
        'UCLH#549',
        'EPIC#HPI0090',
        'EPIC#HPI0212',
        'EPIC#18618',
        'UCLH#005',
        'EPIC#14273',
        'UCLH#3952',
        'EPIC#20199',
        'EPIC#HPI0142',
        'EPIC#4312',
        'EPIC#10013',
        'EPIC#HPI0143',
        'UCLH#049',
        'EPIC#RSHE0024',
        'EPIC#RSCV0009',
        'EPIC#3306',
        'UCLH#884',
        'EPIC#22644',
        'EPIC#4372',
        'UCLH#2148',
        'EPIC#14571',
        'EPIC#2082',
        'EPIC#4275',
        'UCLH#1185',
        'EPIC#RSHE0012',
        'EPIC#35729',
        'EPIC#38132',
        'EPIC#14368',
        'EPIC#29363',
        'EPIC#4395',
        'EPIC#4398',
        'EPIC#62917',
        'EPIC#PENK0201',
        'EPIC#HPI0324',
        'EPIC#62913',
        'UCLH#011',
        'EPIC#4333',
        'EPIC#18123',
        'EPIC#37056',
        'EPIC#4339',
        'EPIC#21776',
        'EPIC#35789',
        'UCLH#040',
        'UCLH#1239',
        'EPIC#4397',
        'EPIC#2948',
        'EPIC#19354',
        'EPIC#4650',
        'UCLH#1240',
        'EPIC#31000017368',
        'EPIC#36145',
        'UCLH#007'
    )
    AND cnf.[PatientDurableKey] IN (
        SELECT DISTINCT scf.[PatientDurableKey]
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
            AND scf.[PatientDurableKey] IS NOT NULL -- AND scf.[PrimaryService] != 'Obstetrics'
            -- AND scf.[PrimaryService] != 'Neurosurgery'
            -- AND scf.[PrimaryService] != 'Paediatric Dental'
            -- AND dd.[DepartmentName] != 'NHNN THEATRE SUITE'
            -- AND dd.[DepartmentName] != 'RNTNE THEATRE SUITE'
            -- AND dd.[DepartmentName] != 'EGA E02 LABOUR WARD'
            -- AND dd.[DepartmentName] != 'MCC H-1 THEATRE SUITE'
            -- AND dd.[DepartmentName] != 'UCH P02 ENDOSCOPY'
            -- AND dd.[DepartmentName] != 'UCH ANAESTHESIA DEPT'
            AND patd.[AgeInYears] >= 18
            AND scufx.[PlannedOperationStartInstant] >= :start_date
            AND scufx.[PlannedOperationStartInstant] < :end_date
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
