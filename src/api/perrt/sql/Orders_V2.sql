-- Pull some interesting orders, D Stein 2022

SELECT
lb.lab_battery_id,
lo.valid_from,
lb.battery_code,
lo.stored_from,
lo.hospital_visit_id

FROM star.lab_battery lb
RIGHT JOIN star.lab_order lo ON lb.lab_battery_id = lo.lab_battery_id
WHERE lb.battery_code IN ('FBC', 'CRP', 'ECC', 'ECL', 'MG', 'CSNF', 'VBG', 'BC', 'LFT', 'ABG', 'U', 'AKI', 'BON')
AND lo.valid_from BETWEEN {end_time} - '{horizon}'::INTERVAL AND {end_time} 
AND lo.hospital_visit_id IN ({hv_ids})
ORDER BY lo.hospital_visit_id, lo.valid_from