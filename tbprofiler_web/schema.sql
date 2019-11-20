DROP TABLE IF EXISTS results;

CREATE TABLE results (
  id TEXT PRIMARY KEY,
	sample_name TEXT NOT NULL,
	status TEXT DEFAULT "processing",
	result TEXT,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	user_id TEXT,
	lineage TEXT,
	drtype TEXT
);
