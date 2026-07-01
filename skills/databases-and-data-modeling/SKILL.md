---
name: databases-and-data-modeling
description: Design schemas, write queries, manage migrations, and choose the right database for the job: normalization vs denormalization trade-offs, indexing, ACID transactions, avoiding N+1 queries, connection pooling, and vector search basics for AI features. Use when the user wants to model a data domain, choose between SQL and NoSQL, design or review a schema, write or optimize a query, set up migrations, add caching, or integrate a vector store. Trigger on "schema", "database", "PostgreSQL", "SQLite", "migrations", "Alembic", "Prisma", "SQLAlchemy", "indexing", "N+1", "connection pool", "Redis", "normalization", "foreign key", "transactions", "ACID", "pgvector", "vector search", "query optimization". Pairs with backend-api-design (for the API that reads the data) and ai-application-engineering (for vector stores and embedding pipelines). Honest: provides schema and query advice; it is not a DBA and cannot guarantee data integrity or recovery; back up before running any migration.
---

# Databases and data modeling: get the foundation right

Decisions made at the data layer are the hardest to undo. A schema that is poorly normalized, missing
indexes, or ignoring transactions creates problems that compound over time. Take the data model seriously
before writing application code, because the ORM cannot fix a bad schema.

Start with PostgreSQL unless a specific constraint rules it out. It handles relational data, JSON, full-text
search, and vector similarity (via pgvector) in one engine, which keeps the operational surface small.
SQLite is the right choice for local tools, testing, and embedded use; it requires no server.

## Normalization vs denormalization

| Situation | Guidance |
|---|---|
| Default starting point | Normalize to third normal form (3NF): each non-key column depends on the whole key and nothing but the key. This eliminates update anomalies and makes schema evolution safer. |
| Read-heavy reporting path | Controlled denormalization is fine: a materialized view, a summary table updated by a trigger, or a read replica. Make the trade-off explicit and documented. |
| Document-shaped, schema-flexible data | Use PostgreSQL JSONB for the flexible part; keep the stable, queryable columns as normal columns. Avoid a pure document store unless the data is truly document-shaped and you need no relational joins. |

## Indexing: index what you query, not everything

- Every foreign key column needs an index; most ORMs do not add them automatically.
- Add a B-tree index on columns that appear in `WHERE`, `ORDER BY`, or `JOIN` conditions in frequent queries.
- Use a partial index when the query always filters on a condition: `CREATE INDEX ON orders (user_id) WHERE status = 'pending'`.
- Unused indexes cost write performance and storage; run `pg_stat_user_indexes` to find them.
- For full-text search, use a GIN index on a `tsvector` column, not `LIKE '%term%'` scans.

## Transactions and ACID

A transaction is the unit of consistency. Use one whenever an operation touches more than one row or table
and all changes must succeed together or not at all.

```sql
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = :sender;
UPDATE accounts SET balance = balance + 100 WHERE id = :receiver;
INSERT INTO transfers (sender_id, receiver_id, amount) VALUES (:sender, :receiver, 100);
COMMIT;
```

Choose the isolation level deliberately: `READ COMMITTED` is the PostgreSQL default and correct for most
OLTP; use `REPEATABLE READ` or `SERIALIZABLE` only when you have a proven phantom-read or write-skew problem,
because they add contention.

## Migrations: automate them, never hand-edit production

- Use Alembic (Python/SQLAlchemy) or Prisma Migrate (Node/TypeScript) to generate and apply migrations.
- Every migration is a reversible pair: `upgrade()` and `downgrade()`. Write the downgrade.
- Run migrations in CI against a real database before merging.
- Back up production before applying any migration that drops a column or changes a column type.
- Never run `ALTER TABLE` by hand on production and then try to reconstruct the migration after the fact.

```python
# Alembic migration example
def upgrade():
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))

def downgrade():
    op.drop_column("users", "bio")
```

## Avoiding N+1 queries

N+1 is the pattern where loading N parent rows triggers N additional queries for their children. It is a
common ORM-related performance problem and invisible without query logging.

- Enable query logging in development; count the queries for each page load or API response.
- Use `JOIN` or the ORM's eager-loading mechanism (`selectinload`, Prisma `include`) to fetch related rows in one query.
- For list endpoints, load all related data in one batched query rather than in a loop.

## Connection pooling

A database has a hard connection limit. Application servers must share connections through a pool.

| Tool | Use case |
|---|---|
| SQLAlchemy connection pool (built-in) | Python apps; configure `pool_size` and `max_overflow` to match the database's `max_connections`. |
| PgBouncer | When many app instances share one Postgres; runs as a sidecar and multiplexes connections. |
| Prisma's connection pool | Node apps; built into the Prisma client; tune `connection_limit` in the URL. |

## Vector search basics for AI features

For RAG and semantic search, store embeddings alongside relational data in PostgreSQL using pgvector.
This avoids a separate vector-store service until scale demands it.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE documents (
    id         BIGSERIAL PRIMARY KEY,
    content    TEXT NOT NULL,
    embedding  VECTOR(1536),   -- match your embedding model's dimension
    source     TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- HNSW index for approximate nearest-neighbor search
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
```

Query: `SELECT id, content FROM documents ORDER BY embedding <=> $1 LIMIT 10;`

See the ai-application-engineering skill for the full RAG pipeline that sits on top of this layer.

## Caching with Redis

Cache the results of slow queries or expensive computations, not raw database rows. Use cache-aside: read
from the cache first; on a miss, read from the database and populate the cache with a TTL. Invalidate by
key on write, not by time alone for data that must be consistent. Redis (redis.io) is a widely used choice
for shared-memory caches across multiple app instances.

## Honest guardrails

- Back up before any migration that drops or renames a column; a `downgrade()` can only restore schema, not lost data.
- Cambium provides schema and query advice; it is not a DBA and cannot guarantee data integrity, recovery, or operational correctness in production.
- ORM magic hides SQL; inspect generated queries on any path that touches large tables or loops.
- `TRUNCATE` and `DROP TABLE` are destructive DDL statements. Transaction and rollback behavior for DDL varies by database and driver; some databases auto-commit DDL outside any transaction. Always back up before running them, and confirm your database's behavior before assuming a rollback is possible. `DELETE` without a `WHERE` clause is similarly catastrophic without a backup.

## Attribution and sources

PostgreSQL documentation (postgresql.org/docs), pgvector (github.com/pgvector/pgvector),
SQLite (sqlite.org), SQLAlchemy (docs.sqlalchemy.org), Alembic (alembic.sqlalchemy.org),
Prisma (prisma.io/docs), Redis (redis.io/docs), PgBouncer (pgbouncer.org),
normalization and normal forms (Date, C.J., "An Introduction to Database Systems", 8th ed.),
ACID and isolation levels (PostgreSQL docs, postgresql.org/docs/current/transaction-iso.html),
N+1 detection (Bullet gem author's blog post, Brandon Keepers, 2012, popularized the term in ORMs).
