-- D Stein March 2022

-- Query to pull labs from adult inpatients currently on the wards
-- This query is to pull labs for each patient

SELECT DISTINCT res.lab_order_id,
def.test_lab_code,
res.valid_from,
res.value_as_bytes,
res.value_as_real,
res.value_as_text,
lo.request_datetime,
lo.hospital_visit_id

FROM star.lab_test_definition def

JOIN star.lab_result res ON res.lab_test_definition_id = def.lab_test_definition_id
JOIN star.lab_order lo ON res.lab_order_id = lo.lab_order_id

--Look at last 72h
WHERE res.result_last_modified_datetime >= {end_time} - '{horizon}'::INTERVAL
AND res.result_last_modified_datetime <= {end_time}

-- Now choose which labs we want
AND def.test_lab_code IN ('HBGL', 'RCC', 'HCT', 'HCTU', 'MCVU', 'PLT', 'NE', 'WCC', 'LY', -- FBC
									'NA', 'K', 'CREA', 'GFR', 'UREA' -- U+Es
									'BILI', 'ALP', 'ALT', 'ALB', --LFTs
									'CRP', 'MG', 'CA', 'CCA', 'PHOS', 'LDH', 'HTRT', --Other
									'INR', 'PT', 'APTT' --clotting
									'GLU', 'Glu', 'pH', 'pCO2', 'K+', 'Na+', 'Lac', 'Urea', 'Crea', 'tHb', 'COHb', 'Ferr', 'pO2', 'Urea')

--Only patients in the previous data pull
AND lo.hospital_visit_id IN ({hv_ids})

ORDER BY res.lab_order_id, lo.request_datetime ASC;
