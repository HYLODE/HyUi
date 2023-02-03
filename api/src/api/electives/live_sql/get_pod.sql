-- noinspection SqlNoDataSourceInspectionForFile
-- 2022-07-21
-- Query by J Hunter
-- see https://github.com/HYLODE/HyUi/issues/47#issuecomment-1160706270
SELECT pod.NAME AS PodOrc,
    c.OR_CASE_ID AS OrCaseId,
    c.SURGERY_DATE AS SurgeryDateClarity
FROM OR_CASE c
    INNER JOIN ZC_OR_POSTOP_DEST pod ON pod.POSTOP_DEST = c.POSTOP_DEST_C
WHERE c.SURGERY_DATE >= :start_date
    AND c.SURGERY_DATE < :end_date
