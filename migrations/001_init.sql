-- Full v1 schema (SPEC.md §4). Forward-only; never edit after it has been applied anywhere.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE repos (
  id              BIGSERIAL PRIMARY KEY,
  slug            TEXT NOT NULL UNIQUE,
  source_url      TEXT,
  local_path      TEXT,
  default_branch  TEXT,
  head_commit     TEXT,
  embedding_model TEXT NOT NULL,
  embedding_dim   INT  NOT NULL,
  chunker_version INT  NOT NULL,
  indexed_at      TIMESTAMPTZ,
  stats           JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE files (
  id           BIGSERIAL PRIMARY KEY,
  repo_id      BIGINT NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
  path         TEXT   NOT NULL,
  lang         TEXT   NOT NULL,
  content_sha  TEXT   NOT NULL,
  size_bytes   INT    NOT NULL,
  loc          INT    NOT NULL,
  parse_status TEXT   NOT NULL,
  is_test      BOOLEAN NOT NULL DEFAULT FALSE,
  indexed_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (repo_id, path)
);

CREATE TABLE chunks (
  id           BIGSERIAL PRIMARY KEY,
  repo_id      BIGINT NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
  file_id      BIGINT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
  kind         TEXT   NOT NULL,
  symbol_path  TEXT,
  symbol_name  TEXT,
  start_line   INT NOT NULL,
  end_line     INT NOT NULL,
  start_byte   INT NOT NULL,
  end_byte     INT NOT NULL,
  part_index   INT NOT NULL DEFAULT 0,
  part_total   INT NOT NULL DEFAULT 1,
  token_count  INT NOT NULL,
  text         TEXT NOT NULL,
  keywords     TEXT NOT NULL,
  text_sha     TEXT NOT NULL,
  tsv          tsvector GENERATED ALWAYS AS (
                 setweight(to_tsvector('simple', coalesce(symbol_path, '')), 'A') ||
                 setweight(to_tsvector('simple', keywords), 'B') ||
                 setweight(to_tsvector('simple', text), 'C')
               ) STORED,
  UNIQUE (file_id, start_byte, end_byte, part_index)
);

CREATE TABLE chunk_embeddings (
  chunk_id  BIGINT NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  model     TEXT   NOT NULL,
  embedding vector(1024) NOT NULL,
  PRIMARY KEY (chunk_id, model)
);

CREATE TABLE embedding_cache (
  model      TEXT NOT NULL,
  text_sha   TEXT NOT NULL,
  embedding  vector(1024) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (model, text_sha)
);

CREATE INDEX ON chunk_embeddings USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
CREATE INDEX ON chunks USING gin (tsv);
CREATE INDEX ON chunks USING gin (symbol_name gin_trgm_ops);
CREATE INDEX ON chunks (repo_id, kind);
CREATE INDEX ON chunks (file_id);
CREATE INDEX ON files (repo_id, path);
