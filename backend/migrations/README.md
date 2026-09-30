# Database migrations

Alembic is the only schema-management mechanism for PostgreSQL and deployed environments.

From `backend/`:

```bash
python -m alembic -c migrations/alembic.ini upgrade head
python -m alembic -c migrations/alembic.ini current
python -m alembic -c migrations/alembic.ini check
```

Create a reviewed migration after changing ORM models:

```bash
python -m alembic -c migrations/alembic.ini revision --autogenerate -m "describe change"
```

## Existing unversioned local databases

The initial migration is intended for new databases. Back up and validate an existing
unversioned database before adopting Alembic. If its schema exactly matches the initial
revision, mark it without replaying table creation:

```bash
python -m alembic -c migrations/alembic.ini stamp head
```

Never stamp an unknown production schema. Generate and review a data/schema migration instead.
