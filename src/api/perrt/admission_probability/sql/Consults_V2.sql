--Pull most common consults - D Stein 2022

SELECT ct.name,
cr.hospital_visit_id,
cr.valid_from

FROM star.consultation_type ct
RIGHT JOIN star.consultation_request cr ON ct.consultation_type_id = cr.consultation_type_id

--WHERE cr.valid_from BETWEEN NOW() - '10 DAYS'::INTERVAL AND NOW()
WHERE ct.name IN ('Inpatient consult to Acute Medicine',
 'Inpatient consult to Dietetics (N&D) - Not TPN',
 'ED consult to Ambulatory Medicine',
 'Inpatient Consult to Integrated Discharge Service',
 'Inpatient consult to Paediatrics',
 'Inpatient consult to PERRT',
 'Inpatient Referral to Tissue Viability',
 'Inpatient consult to General Surgery',
 'Inpatient Consult to Symptom Control and Palliative Care',
 'Inpatient consult to Mental Health Liaison Team',
 'Inpatient consult to Orthopedic Surgery',
 'Inpatient consult to ENT',
 'Inpatient consult to Obstetrics',
 'Inpatient consult to Haematology',
 'Inpatient consult to Infant Feeding Team',
 'Inpatient Consult to Pain Team (Acute, Complex and Cancer pain services)',
 'Inpatient consult to Infectious Diseases',
 'Inpatient consult to Adult Diabetes CNS',
 'Inpatient consult to Oral & Maxillofacial Surgery',
 'Inpatient consult to Urology',
 'Inpatient consult to Gynaecology',
 'Inpatient consult to Oncology',
 'Inpatient consult to Podiatry',
 'Inpatient consult to Adult Endocrine & Diabetes',
 'Inpatient Consult to Drug/Alcohol Team',
 'Inpatient consult to Neurology',
 'Inpatient consult to Neuro Ophthalmology',
 'IP Consult to MCC Complementary Therapy Team',
 'Inpatient Consult to Acute Frailty Team',
 'Inpatient consult to Cardiology',
 'Inpatient Consult to Homeless Team',
 'Inpatient consult to Neuropsychology',
 'Inpatient consult to Respiratory Medicine',
 'Inpatient Consult to Transforming end of life care team',
 'Inpatient consult to Neuro-psychiatry',
 'Inpatient consult to Psychology',
 'Inpatient consult to Nutrition Team (TPN)',
 'Inpatient Consult to UCLH@Home',
 'Inpatient consult Respiratory Physiotherapy',
 'Inpatient consult to Intensivist',
 'Inpatient consult to Rheumatology',
 'Inpatient consult to Stoma Care Nursing',
 'Inpatient consult to Gastroenterology',
 'Inpatient Consult to MSIS Psychology - Haematology',
 'Inpatient consult to Stroke Medicine and Neuro-Rehabilitation',
 'Inpatient consult to Care of the Elderly',
 'Inpatient consult to Psychiatry',
 'Inpatient consult to Neonatology',
 'Inpatient consult to Social Work',
 'Inpatient consult to Pastoral Care',
 'Inpatient consult to Dermatology')

AND cr.cancelled = 'false'
AND cr.closed_due_to_discharge = 'false'

AND cr.valid_from BETWEEN {end_time} - '{horizon}'::INTERVAL AND {end_time}

AND cr.hospital_visit_id IN ({hv_ids})
ORDER BY cr.hospital_visit_id DESC
