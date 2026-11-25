CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
CREATE TABLE analysis_runs (
	id INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	dataset_hash VARCHAR(64) NOT NULL, 
	n_participants_included INTEGER NOT NULL, 
	n_participants_total INTEGER NOT NULL, 
	experiment_versions JSON, 
	software_versions JSON, 
	results_json JSON, 
	output_dir TEXT, 
	error TEXT, 
	PRIMARY KEY (id)
);
CREATE TABLE app_settings (
	"key" VARCHAR(80) NOT NULL, 
	value TEXT, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY ("key")
);
CREATE TABLE audit_logs (
	id INTEGER NOT NULL, 
	timestamp DATETIME NOT NULL, 
	actor VARCHAR(40) NOT NULL, 
	action VARCHAR(80) NOT NULL, 
	entity_type VARCHAR(40), 
	entity_id VARCHAR(80), 
	details JSON, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_audit_logs_action ON audit_logs (action);
CREATE INDEX ix_audit_logs_timestamp ON audit_logs (timestamp);
CREATE TABLE experiment_configs (
	id INTEGER NOT NULL, 
	version_number INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	config_json JSON NOT NULL, 
	config_hash VARCHAR(64) NOT NULL, 
	experiment_version VARCHAR(64) NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	is_active_main BOOLEAN NOT NULL, 
	parent_id INTEGER, 
	notes TEXT, 
	lock_justification TEXT, 
	created_at DATETIME NOT NULL, 
	locked_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_config_status CHECK (status IN ('draft','locked','retired')), 
	FOREIGN KEY(parent_id) REFERENCES experiment_configs (id), 
	UNIQUE (experiment_version), 
	UNIQUE (version_number)
);
CREATE TABLE import_batches (
	id INTEGER NOT NULL, 
	file_names TEXT NOT NULL, 
	file_sha256 VARCHAR(64) NOT NULL, 
	file_format VARCHAR(20) NOT NULL, 
	import_kind VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	validation_report JSON, 
	staged_payload JSON, 
	n_participants INTEGER NOT NULL, 
	n_sessions INTEGER NOT NULL, 
	n_trials INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	committed_at DATETIME, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_import_batches_file_sha256 ON import_batches (file_sha256);
CREATE TABLE generated_reports (
	id INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	kind VARCHAR(20) NOT NULL, 
	analysis_run_id INTEGER, 
	output_dir TEXT NOT NULL, 
	files JSON NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(analysis_run_id) REFERENCES analysis_runs (id)
);
CREATE TABLE participants (
	id INTEGER NOT NULL, 
	participant_id VARCHAR(40) NOT NULL, 
	age INTEGER, 
	gender VARCHAR(40), 
	academic_course VARCHAR(120), 
	consent_status BOOLEAN NOT NULL, 
	consent_timestamp DATETIME, 
	participant_type VARCHAR(10) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	status_reason TEXT, 
	data_source VARCHAR(20) NOT NULL, 
	import_batch_id INTEGER, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_participant_type CHECK (participant_type IN ('main','pilot')), 
	CONSTRAINT ck_participant_status CHECK (status IN ('active','withdrawn','excluded')), 
	CONSTRAINT ck_participant_age CHECK (age IS NULL OR (age >= 18 AND age <= 120)), 
	FOREIGN KEY(import_batch_id) REFERENCES import_batches (id)
);
CREATE UNIQUE INDEX ix_participants_participant_id ON participants (participant_id);
CREATE TABLE experiment_sessions (
	session_id VARCHAR(64) NOT NULL, 
	participant_id VARCHAR(40) NOT NULL, 
	config_id INTEGER, 
	experiment_version VARCHAR(64) NOT NULL, 
	session_type VARCHAR(10) NOT NULL, 
	condition_order VARCHAR(3) NOT NULL, 
	random_seed INTEGER, 
	trial_plan JSON, 
	device_information TEXT, 
	browser_information TEXT, 
	screen_information TEXT, 
	estimated_refresh_rate FLOAT, 
	start_time DATETIME, 
	completion_time DATETIME, 
	completion_status VARCHAR(20) NOT NULL, 
	token_hash VARCHAR(64), 
	practice_attempts INTEGER NOT NULL, 
	interruptions INTEGER NOT NULL, 
	fullscreen_exits INTEGER NOT NULL, 
	notes TEXT, 
	data_source VARCHAR(20) NOT NULL, 
	import_batch_id INTEGER, 
	created_at DATETIME NOT NULL, 
	last_activity DATETIME NOT NULL, 
	PRIMARY KEY (session_id), 
	CONSTRAINT ck_completion_status CHECK (completion_status IN ('registered','in_progress','completed','incomplete','withdrawn','abandoned')), 
	CONSTRAINT ck_condition_order CHECK (condition_order IN ('ABC','ACB','BAC','BCA','CAB','CBA')), 
	CONSTRAINT ck_session_type CHECK (session_type IN ('main','pilot')), 
	FOREIGN KEY(config_id) REFERENCES experiment_configs (id), 
	FOREIGN KEY(import_batch_id) REFERENCES import_batches (id), 
	FOREIGN KEY(participant_id) REFERENCES participants (participant_id) ON DELETE CASCADE
);
CREATE INDEX ix_experiment_sessions_participant_id ON experiment_sessions (participant_id);
CREATE TABLE imported_participant_summaries (
	id INTEGER NOT NULL, 
	participant_id VARCHAR(40) NOT NULL, 
	experiment_version VARCHAR(64), 
	condition_order VARCHAR(3), 
	accuracy_a FLOAT NOT NULL, 
	accuracy_b FLOAT NOT NULL, 
	accuracy_c FLOAT NOT NULL, 
	rt_a FLOAT, 
	rt_b FLOAT, 
	rt_c FLOAT, 
	timeout_rate FLOAT, 
	secondary_accuracy_b FLOAT, 
	secondary_accuracy_c FLOAT, 
	import_batch_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(import_batch_id) REFERENCES import_batches (id), 
	FOREIGN KEY(participant_id) REFERENCES participants (participant_id) ON DELETE CASCADE, 
	UNIQUE (participant_id)
);
CREATE TABLE participant_contacts (
	id INTEGER NOT NULL, 
	participant_id VARCHAR(40) NOT NULL, 
	email VARCHAR(254), 
	email_hash VARCHAR(64), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(participant_id) REFERENCES participants (participant_id) ON DELETE CASCADE, 
	UNIQUE (participant_id)
);
CREATE INDEX ix_participant_contacts_email_hash ON participant_contacts (email_hash);
CREATE TABLE trials (
	trial_id INTEGER NOT NULL, 
	session_id VARCHAR(64) NOT NULL, 
	participant_id VARCHAR(40) NOT NULL, 
	trial_number INTEGER NOT NULL, 
	block_number INTEGER NOT NULL, 
	condition VARCHAR(1) NOT NULL, 
	practice_trial BOOLEAN NOT NULL, 
	practice_attempt INTEGER NOT NULL, 
	original_pattern VARCHAR(64) NOT NULL, 
	recognition_pattern VARCHAR(64) NOT NULL, 
	correct_answer VARCHAR(10) NOT NULL, 
	participant_response VARCHAR(10), 
	is_correct BOOLEAN, 
	reaction_time_ms FLOAT, 
	response_timeout BOOLEAN NOT NULL, 
	premature_keypresses INTEGER NOT NULL, 
	interference_type VARCHAR(20) NOT NULL, 
	interference_stimulus VARCHAR(120), 
	interference_correct_answer VARCHAR(10), 
	interference_response VARCHAR(10), 
	interference_accuracy BOOLEAN, 
	interference_reaction_time_ms FLOAT, 
	planned_fixation_duration_ms FLOAT, 
	actual_fixation_duration_ms FLOAT, 
	planned_stimulus_duration_ms FLOAT, 
	measured_stimulus_duration_ms FLOAT, 
	planned_interference_duration_ms FLOAT, 
	measured_interference_duration_ms FLOAT, 
	planned_retention_duration_ms FLOAT, 
	measured_retention_duration_ms FLOAT, 
	planned_iti_ms FLOAT, 
	inter_trial_interval_ms FLOAT, 
	refresh_rate_hz FLOAT, 
	dropped_frames INTEGER, 
	focus_loss BOOLEAN NOT NULL, 
	timing_quality_flag VARCHAR(10) NOT NULL, 
	timing_notes TEXT, 
	exclusion_status VARCHAR(10) NOT NULL, 
	exclusion_reason TEXT, 
	event_timestamps JSON, 
	timestamp DATETIME NOT NULL, 
	PRIMARY KEY (trial_id), 
	CONSTRAINT ck_trial_condition CHECK (condition IN ('A','B','C')), 
	CONSTRAINT ck_trial_correct_answer CHECK (correct_answer IN ('same','different')), 
	CONSTRAINT ck_exclusion_status CHECK (exclusion_status IN ('included','excluded')), 
	CONSTRAINT ck_trial_response CHECK (participant_response IS NULL OR participant_response IN ('same','different')), 
	CONSTRAINT ck_timing_flag CHECK (timing_quality_flag IN ('ok','warning','invalid')), 
	CONSTRAINT ck_trial_rt CHECK (reaction_time_ms IS NULL OR reaction_time_ms >= 0), 
	FOREIGN KEY(session_id) REFERENCES experiment_sessions (session_id) ON DELETE CASCADE, 
	CONSTRAINT uq_trial_key UNIQUE (session_id, practice_trial, practice_attempt, trial_number)
);
CREATE INDEX ix_trials_participant_id ON trials (participant_id);
CREATE INDEX ix_trials_session_id ON trials (session_id);
