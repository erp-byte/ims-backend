-- Add UNIQUE constraint to modules.name column
-- Run this first before executing the main create_auth_tables.sql script

ALTER TABLE modules ADD CONSTRAINT modules_name_unique UNIQUE (name);
