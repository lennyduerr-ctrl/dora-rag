-- DORA RAG: Supabase Setup
-- Run this in the Supabase SQL Editor (https://supabase.com/dashboard)

-- 1. Enable pgvector extension
create extension if not exists vector;

-- 2. Create chunks table
create table dora_chunks (
  id bigserial primary key,
  content text not null,
  metadata jsonb not null default '{}',
  embedding vector(1536)
);

-- 3. Create similarity search index
create index on dora_chunks
  using hnsw (embedding vector_cosine_ops);

-- 4. Create match function for LangChain
create or replace function match_dora_chunks(
  query_embedding vector(1536),
  match_threshold float default 0.5,
  match_count int default 5
)
returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
language sql stable
as $$
  select
    id,
    content,
    metadata,
    1 - (embedding <=> query_embedding) as similarity
  from dora_chunks
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by embedding <=> query_embedding
  limit match_count;
$$;

-- 5. Filtered match function for specialized search tools
create or replace function match_dora_chunks_filtered(
  query_embedding vector(1536),
  match_threshold float default 0.3,
  match_count int default 8,
  filter_doc_types text[] default null,
  filter_authority text default null,
  filter_category text default null
)
returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
language sql stable
as $$
  select
    id,
    content,
    metadata,
    1 - (embedding <=> query_embedding) as similarity
  from dora_chunks
  where 1 - (embedding <=> query_embedding) > match_threshold
    and (filter_doc_types is null or metadata->>'document_type' = any(filter_doc_types))
    and (filter_authority is null or metadata->>'authority' = filter_authority)
    and (filter_category is null or metadata->>'category' = filter_category)
  order by embedding <=> query_embedding
  limit match_count;
$$;
