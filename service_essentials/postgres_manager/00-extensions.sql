-- Create required PostgreSQL extensions
-- This file is executed first (00-) to ensure extensions are available before seed data

-- pgcrypto: cryptographic functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- pg_trgm: text similarity measurement and index searching based on trigrams
-- Required for similarity() function used in quality-checker
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE EXTENSION IF NOT EXISTS unaccent;