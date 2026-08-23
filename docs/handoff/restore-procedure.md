# Postgres Backup & Restore Procedure (TD-36 / gap G12)

All site content lives in Railway Postgres 16 and nowhere else. An untested backup is a belief, not a backup. No secret values here — substitute real connection strings from the Railway dashboard at run time.

## 1. Backup policy check (TD-M4 decision, re-verified at TD-36)

1. Railway dashboard → Postgres service → Settings/Backups: is automatic backup enabled on your plan? Record the answer in `docs/conventions.md`.
2. If automatic: note retention window and restore entry point.
3. If **not** automatic: the weekly `pg_dump` cron to R2 below is mandatory **before any content is authored**.

## 2. Weekly pg_dump cron to R2 (only if Railway backups are not automatic)

Railway cron service (same pattern as the publishing scheduler), weekly:

```bash
pg_dump "$DATABASE_URL" --format=custom --compress=9 --file=/tmp/portfolio.dump
```

- `--format=custom` (`.dump`): compressed, supports selective restore via `pg_restore`.
- Upload to R2 bucket `portfolio-media` under `backups/` with a date-stamped key, e.g. `backups/postgres/portfolio-$(date +%F).dump`, via the existing StorageAdapter/S3 credentials.
- Keep ≥ 8 weekly dumps; prune older objects in the same job.
- Log loudly on failure (Sentry alert once TD-36 wires it) — a silently failing backup job is the exact failure this procedure exists to prevent.

## 3. Restore drill — into scratch Docker Postgres

Never drill against production. Use a throwaway container:

```bash
docker run -d --name restore-drill -e POSTGRES_PASSWORD=drill -p 5433:5432 postgres:16-alpine
```

1. Fetch the latest backup (R2):
   ```bash
   aws s3 cp s3://portfolio-media/backups/postgres/portfolio-<DATE>.dump ./portfolio.dump --endpoint-url "$R2_ENDPOINT"
   ```
   (or download from Railway's backup UI if automatic).
2. Create the target database:
   ```bash
   docker exec restore-drill psql -U postgres -c "CREATE DATABASE portfolio_restore;"
   ```
3. Restore the custom-format dump:
   ```bash
   docker exec -i restore-drill pg_restore -U postgres -d portfolio_restore --no-owner --clean --if-exists < portfolio.dump
   ```
   `--no-owner` avoids role mismatches; `--clean --if-exists` makes the drill re-runnable.
4. Verify row counts on key tables (expect non-zero where content exists; compare against production counts taken at the same time):
   ```sql
   SELECT
     (SELECT count(*) FROM timeline_entries)      AS timeline,
     (SELECT count(*) FROM projects)              AS projects,
     (SELECT count(*) FROM skills)                AS skills,
     (SELECT count(*) FROM certifications)        AS certifications,
     (SELECT count(*) FROM posts)                 AS posts,
     (SELECT count(*) FROM prose_pages)           AS prose,
     (SELECT count(*) FROM collection_items)      AS collections,
     (SELECT count(*) FROM overview_intros)       AS overview,  -- must be 6
     (SELECT count(*) FROM topic_tags)            AS tags,
     (SELECT count(*) FROM audience_tag_map)      AS tag_map,
     (SELECT count(*) FROM form_submissions)      AS submissions;
   ```
   (Table names follow the models; adjust to the actual schema if renamed.)
5. Verify Alembic state matches:
   ```bash
   docker exec restore-drill psql -U postgres -d portfolio_restore -c "SELECT version_num FROM alembic_version;"
   ```
   Must equal `uv run alembic heads` output (exactly one head).
6. Spot-check one content row renders logically (e.g. latest published timeline entry's title/dates).
7. Tear down: `docker rm -f restore-drill`.

## 4. Failure modes to expect

- `pg_restore` errors on missing roles → `--no-owner` fixes.
- Empty table that should have content → dump predates the content; check cron job logs.
- `alembic_version` mismatch → dump taken mid-migration; re-run after the deploy settles.

## 5. Schedule

| When | What |
|---|---|
| TD-M4 | Confirm backup policy; if not automatic, stand up the weekly dump cron before authoring content |
| TD-36 | First full restore drill (section 3); record result in `docs/conventions.md` |
| Quarterly thereafter | Repeat the drill; re-verify cron job still running and pruning |
