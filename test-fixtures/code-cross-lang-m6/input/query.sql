-- Cross-language IPC mechanism M6 (SQL tables) sample.
-- The 'jobs_queue' table is shared between the rust-worker and python-api.

SELECT id, payload, status FROM jobs_queue WHERE status = 'pending';

UPDATE jobs_queue SET status = 'processing' WHERE id = $1;
