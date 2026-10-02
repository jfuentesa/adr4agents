BEGIN IMMEDIATE;

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    context TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    author TEXT NOT NULL,
    title TEXT NOT NULL,
    context TEXT NOT NULL,
    alternatives TEXT NOT NULL,
    decision TEXT NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('draft', 'proposed', 'accepted', 'rejected', 'superseded')
    ),
    superseded_by INTEGER REFERENCES decisions(id),
    CHECK (superseded_by IS NULL OR superseded_by != id),
    CHECK ((status = 'superseded') = (superseded_by IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS decision_tags (
    decision_id INTEGER NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    PRIMARY KEY (decision_id, tag)
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY,
    decision_id INTEGER NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    author TEXT NOT NULL,
    text TEXT NOT NULL,
    date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    target_id INTEGER NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('complements', 'contradicts', 'supersedes')),
    CHECK (source_id != target_id),
    UNIQUE (source_id, target_id, type)
);

CREATE INDEX IF NOT EXISTS decisions_project_status
    ON decisions(project_id, status, id);
CREATE INDEX IF NOT EXISTS decision_tags_tag ON decision_tags(tag, decision_id);
CREATE INDEX IF NOT EXISTS comments_decision ON comments(decision_id, id);
CREATE INDEX IF NOT EXISTS relations_target ON relations(target_id, id);

PRAGMA user_version = 1;
COMMIT;
