BEGIN IMMEDIATE;
ALTER TABLE relations ADD COLUMN effective INTEGER NOT NULL DEFAULT 1
    CHECK (effective IN (0, 1) AND (type = 'supersedes' OR effective = 1));
PRAGMA user_version = 2;
COMMIT;
