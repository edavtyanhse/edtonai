# SQL migration order

These files are the historical baseline for databases created before Alembic
was introduced. Apply files in numeric order, then stamp the Alembic baseline
revision from `backend/alembic/versions/20260429_0001_baseline_existing_sql.py`.

The numeric prefixes are unique and dependency-aware:

1. `001_add_parsed_data.sql`
2. `002_split_parsed_data.sql`
3. `003_add_updated_at_remove_safety_notes.sql`
4. `004_add_source_url.sql`
5. `005_add_feedback_table.sql`
6. `006_add_analysis_id_to_user_version.sql`
7. `007_increase_metadata_lengths.sql`
8. `008_extend_feedback_for_nps_csat.sql`

`clear_database.sql` is a destructive maintenance script and is not part of
the normal migration sequence.

New schema changes should be implemented as Alembic revisions under
`backend/alembic/versions`.
