-- YugKrit Database Schema (reference DDL, auto-generated from SQLAlchemy models)
-- This file is for documentation / manual inspection.
-- The application creates tables automatically via SQLAlchemy (db.create_all()).

CREATE TABLE achievements (
	id INTEGER NOT NULL, 
	code VARCHAR(50), 
	title VARCHAR(150), 
	description VARCHAR(300), 
	icon VARCHAR(50), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (code)
);

CREATE TABLE challenge_categories (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	icon VARCHAR(50), 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE organizations (
	id INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	org_type VARCHAR(30) NOT NULL, 
	official_email VARCHAR(150), 
	website VARCHAR(200), 
	phone VARCHAR(20), 
	address VARCHAR(300), 
	district VARCHAR(100), 
	state VARCHAR(100), 
	status VARCHAR(20), 
	verified_by_id INTEGER, 
	verified_at DATETIME, 
	rejection_reason VARCHAR(500), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(verified_by_id) REFERENCES users (id)
);

CREATE TABLE otp_codes (
	id INTEGER NOT NULL, 
	phone VARCHAR(20) NOT NULL, 
	purpose VARCHAR(20), 
	code_hash VARCHAR(128) NOT NULL, 
	attempts INTEGER, 
	max_attempts INTEGER, 
	is_verified BOOLEAN, 
	created_at DATETIME, 
	expires_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE permissions (
	id INTEGER NOT NULL, 
	code VARCHAR(100) NOT NULL, 
	description VARCHAR(255), 
	PRIMARY KEY (id), 
	UNIQUE (code)
);

CREATE TABLE roles (
	id INTEGER NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	description VARCHAR(255), 
	dashboard_route VARCHAR(100), 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE users (
	id INTEGER NOT NULL, 
	full_name VARCHAR(150) NOT NULL, 
	email VARCHAR(150) NOT NULL, 
	phone VARCHAR(20), 
	password_hash VARCHAR(255) NOT NULL, 
	role_id INTEGER NOT NULL, 
	organization_id INTEGER, 
	is_active BOOLEAN, 
	is_email_verified BOOLEAN, 
	is_phone_verified BOOLEAN, 
	last_login_at DATETIME, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(role_id) REFERENCES roles (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
);

CREATE TABLE audit_logs (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	role_name VARCHAR(50), 
	action VARCHAR(100), 
	entity VARCHAR(100), 
	entity_id INTEGER, 
	previous_value VARCHAR(500), 
	new_value VARCHAR(500), 
	reason VARCHAR(300), 
	timestamp DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE citizen_profiles (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	aadhaar_hash VARCHAR(128) NOT NULL, 
	aadhaar_last4 VARCHAR(4) NOT NULL, 
	address VARCHAR(300), 
	city VARCHAR(100), 
	district VARCHAR(100), 
	state VARCHAR(100), 
	verification_status VARCHAR(20), 
	verified_by_id INTEGER, 
	verified_at DATETIME, 
	rejection_reason VARCHAR(500), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (aadhaar_hash), 
	FOREIGN KEY(verified_by_id) REFERENCES users (id)
);

CREATE TABLE government_departments (
	id INTEGER NOT NULL, 
	organization_id INTEGER NOT NULL, 
	department_name VARCHAR(200), 
	jurisdiction_level VARCHAR(50), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
);

CREATE TABLE ngos (
	id INTEGER NOT NULL, 
	organization_id INTEGER NOT NULL, 
	registration_number VARCHAR(100), 
	registration_authority VARCHAR(150), 
	registration_date DATE, 
	authorized_rep VARCHAR(150), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
);

CREATE TABLE notifications (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	title VARCHAR(200), 
	message VARCHAR(500), 
	link VARCHAR(300), 
	is_read BOOLEAN, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE organization_documents (
	id INTEGER NOT NULL, 
	organization_id INTEGER NOT NULL, 
	document_type VARCHAR(100), 
	file_name VARCHAR(255), 
	file_path VARCHAR(500), 
	file_size INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
);

CREATE TABLE role_permissions (
	role_id INTEGER NOT NULL, 
	permission_id INTEGER NOT NULL, 
	PRIMARY KEY (role_id, permission_id), 
	FOREIGN KEY(role_id) REFERENCES roles (id), 
	FOREIGN KEY(permission_id) REFERENCES permissions (id)
);

CREATE TABLE ulbs (
	id INTEGER NOT NULL, 
	organization_id INTEGER NOT NULL, 
	ulb_type VARCHAR(100), 
	category VARCHAR(20), 
	authorized_officer VARCHAR(150), 
	designation VARCHAR(100), 
	registration_number VARCHAR(100), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
);

CREATE TABLE universities (
	id INTEGER NOT NULL, 
	organization_id INTEGER NOT NULL, 
	institution_type VARCHAR(100), 
	aishe_code VARCHAR(50), 
	affiliating_university VARCHAR(200), 
	rep_name VARCHAR(150), 
	rep_designation VARCHAR(100), 
	rep_email VARCHAR(150), 
	rep_phone VARCHAR(20), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
);

CREATE TABLE challenges (
	id INTEGER NOT NULL, 
	challenge_code VARCHAR(30), 
	title VARCHAR(200) NOT NULL, 
	description TEXT, 
	category_id INTEGER, 
	subcategory VARCHAR(100), 
	submitted_by_org_id INTEGER, 
	submitted_by_citizen_id INTEGER, 
	problem_owner_org_id INTEGER, 
	assigned_university_id INTEGER, 
	affected_population INTEGER, 
	urgency VARCHAR(20), 
	current_situation TEXT, 
	supporting_info TEXT, 
	priority_score INTEGER, 
	status VARCHAR(30), 
	difficulty VARCHAR(20), 
	required_skills VARCHAR(300), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (challenge_code), 
	FOREIGN KEY(category_id) REFERENCES challenge_categories (id), 
	FOREIGN KEY(submitted_by_org_id) REFERENCES organizations (id), 
	FOREIGN KEY(submitted_by_citizen_id) REFERENCES citizen_profiles (id), 
	FOREIGN KEY(problem_owner_org_id) REFERENCES organizations (id), 
	FOREIGN KEY(assigned_university_id) REFERENCES universities (id)
);

CREATE TABLE faculty (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	university_id INTEGER NOT NULL, 
	department VARCHAR(150), 
	designation VARCHAR(100), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(university_id) REFERENCES universities (id)
);

CREATE TABLE student_profiles (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	institution_id INTEGER NOT NULL, 
	registration_number VARCHAR(50) NOT NULL, 
	full_name VARCHAR(150) NOT NULL, 
	college_email VARCHAR(150) NOT NULL, 
	department VARCHAR(150), 
	course VARCHAR(100), 
	year VARCHAR(20), 
	phone VARCHAR(20), 
	status VARCHAR(20), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_student_institution_regno UNIQUE (institution_id, registration_number), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(institution_id) REFERENCES universities (id)
);

CREATE TABLE university_departments (
	id INTEGER NOT NULL, 
	university_id INTEGER NOT NULL, 
	name VARCHAR(150), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(university_id) REFERENCES universities (id)
);

CREATE TABLE ai_analyses (
	id INTEGER NOT NULL, 
	challenge_id INTEGER NOT NULL, 
	suggested_category VARCHAR(100), 
	priority_score INTEGER, 
	suggested_skills VARCHAR(300), 
	university_matches TEXT, 
	similar_challenge_ids VARCHAR(200), 
	human_review_required BOOLEAN, 
	overridden_by_id INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(challenge_id) REFERENCES challenges (id), 
	FOREIGN KEY(overridden_by_id) REFERENCES users (id)
);

CREATE TABLE challenge_assignments (
	id INTEGER NOT NULL, 
	challenge_id INTEGER NOT NULL, 
	assigned_to_type VARCHAR(30), 
	assigned_to_org_id INTEGER, 
	assigned_by_id INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(challenge_id) REFERENCES challenges (id), 
	FOREIGN KEY(assigned_to_org_id) REFERENCES organizations (id), 
	FOREIGN KEY(assigned_by_id) REFERENCES users (id)
);

CREATE TABLE challenge_evidence (
	id INTEGER NOT NULL, 
	challenge_id INTEGER NOT NULL, 
	evidence_type VARCHAR(20), 
	file_name VARCHAR(255), 
	file_path VARCHAR(500), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(challenge_id) REFERENCES challenges (id)
);

CREATE TABLE challenge_locations (
	id INTEGER NOT NULL, 
	challenge_id INTEGER NOT NULL, 
	address VARCHAR(300), 
	district VARCHAR(100), 
	state VARCHAR(100), 
	latitude FLOAT, 
	longitude FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(challenge_id) REFERENCES challenges (id)
);

CREATE TABLE projects (
	id INTEGER NOT NULL, 
	project_code VARCHAR(30), 
	name VARCHAR(200) NOT NULL, 
	objective TEXT, 
	description TEXT, 
	expected_outcome TEXT, 
	challenge_id INTEGER NOT NULL, 
	university_id INTEGER NOT NULL, 
	faculty_mentor_id INTEGER, 
	start_date DATE, 
	expected_completion DATE, 
	status VARCHAR(30), 
	research_progress INTEGER, 
	design_progress INTEGER, 
	prototype_progress INTEGER, 
	testing_progress INTEGER, 
	validation_progress INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (project_code), 
	FOREIGN KEY(challenge_id) REFERENCES challenges (id), 
	FOREIGN KEY(university_id) REFERENCES universities (id), 
	FOREIGN KEY(faculty_mentor_id) REFERENCES faculty (id)
);

CREATE TABLE student_interests (
	id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	interest_name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES student_profiles (id)
);

CREATE TABLE student_skills (
	id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	skill_name VARCHAR(100) NOT NULL, 
	proficiency VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES student_profiles (id)
);

CREATE TABLE university_applications (
	id INTEGER NOT NULL, 
	challenge_id INTEGER NOT NULL, 
	university_id INTEGER NOT NULL, 
	applied_by_id INTEGER, 
	pitch TEXT, 
	status VARCHAR(20), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(challenge_id) REFERENCES challenges (id), 
	FOREIGN KEY(university_id) REFERENCES universities (id), 
	FOREIGN KEY(applied_by_id) REFERENCES users (id)
);

CREATE TABLE certificates (
	id INTEGER NOT NULL, 
	certificate_id VARCHAR(50) NOT NULL, 
	student_id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	role_in_project VARCHAR(50), 
	issued_date DATE, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (certificate_id), 
	FOREIGN KEY(student_id) REFERENCES student_profiles (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE TABLE community_validations (
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	validated_by_org_id INTEGER, 
	feedback TEXT, 
	rating INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(validated_by_org_id) REFERENCES organizations (id)
);

CREATE TABLE messages (
	id INTEGER NOT NULL, 
	sender_id INTEGER NOT NULL, 
	recipient_id INTEGER NOT NULL, 
	project_id INTEGER, 
	body TEXT, 
	is_read BOOLEAN, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(sender_id) REFERENCES users (id), 
	FOREIGN KEY(recipient_id) REFERENCES users (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE TABLE milestones (
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	title VARCHAR(150) NOT NULL, 
	description TEXT, 
	owner_id INTEGER, 
	due_date DATE, 
	sequence INTEGER, 
	status VARCHAR(30), 
	reviewer_comment TEXT, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(owner_id) REFERENCES student_profiles (id)
);

CREATE TABLE project_evaluations (
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	evaluated_by_id INTEGER, 
	score INTEGER, 
	comments TEXT, 
	verified BOOLEAN, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(evaluated_by_id) REFERENCES users (id)
);

CREATE TABLE project_impacts (
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	people_impacted INTEGER, 
	summary TEXT, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE TABLE project_teams (
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	team_name VARCHAR(150), 
	team_leader_id INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(team_leader_id) REFERENCES student_profiles (id)
);

CREATE TABLE student_achievements (
	id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	achievement_id INTEGER NOT NULL, 
	project_id INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES student_profiles (id), 
	FOREIGN KEY(achievement_id) REFERENCES achievements (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE TABLE deliverables (
	id INTEGER NOT NULL, 
	milestone_id INTEGER NOT NULL, 
	file_name VARCHAR(255), 
	file_path VARCHAR(500), 
	description VARCHAR(300), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(milestone_id) REFERENCES milestones (id)
);

CREATE TABLE project_team_members (
	id INTEGER NOT NULL, 
	team_id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	role_in_team VARCHAR(50), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_team_student UNIQUE (team_id, student_id), 
	FOREIGN KEY(team_id) REFERENCES project_teams (id), 
	FOREIGN KEY(student_id) REFERENCES student_profiles (id)
);

CREATE TABLE tasks (
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	milestone_id INTEGER, 
	title VARCHAR(200) NOT NULL, 
	description TEXT, 
	assigned_to_id INTEGER, 
	due_date DATE, 
	status VARCHAR(20), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(milestone_id) REFERENCES milestones (id), 
	FOREIGN KEY(assigned_to_id) REFERENCES student_profiles (id)
);
