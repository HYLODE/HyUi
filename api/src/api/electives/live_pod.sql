-- 2022-07-21
-- Query by J Hunter
-- see https://github.com/HYLODE/HyUi/issues/47#issuecomment-1160706270

-- TODO: parameterise where clause for greater number of days
SELECT
     pod.NAME AS pod_orc
    ,c.OR_CASE_ID AS or_case_id
    ,c.SURGERY_DATE AS SurgeryDateClarity
FROM OR_CASE c
INNER JOIN ZC_OR_POSTOP_DEST pod ON pod.POSTOP_DEST = c.POSTOP_DEST_C
WHERE c.SURGERY_DATE >= GETDATE()
AND c.SURGERY_DATE <= CONVERT(DATE,DATEADD(DAY, :days_ahead ,CURRENT_TIMESTAMP))
