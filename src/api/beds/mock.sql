-- src/api/beds/mock.sql
-- name the table after the module to avoid name collisions
-- in the mock database
SELECT
*
FROM bedsmock
WHERE (
    department IN (?)
    -- OR
    -- location_string = ANY ( %(locations)s )
)
;
