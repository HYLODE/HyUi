-- src/api/beds/mock.sql
-- name the table after the module to avoid name collisions
-- in the mock database
SELECT
*
FROM censusmock
WHERE
    department IN :departments
    OR
    location_string IN :locations
;
