BEGIN;

-- Drop auth-related sequences
DROP SEQUENCE IF EXISTS auth_group_id_seq CASCADE;
DROP SEQUENCE IF EXISTS auth_group_permissions_id_seq CASCADE;
DROP SEQUENCE IF EXISTS auth_permission_id_seq CASCADE;
DROP SEQUENCE IF EXISTS auth_user_id_seq CASCADE;
DROP SEQUENCE IF EXISTS auth_user_groups_id_seq CASCADE;
DROP SEQUENCE IF EXISTS auth_user_user_permissions_id_seq CASCADE;

-- Drop auth-related tables
DROP TABLE IF EXISTS auth_user_user_permissions CASCADE;
DROP TABLE IF EXISTS auth_user_groups CASCADE;
DROP TABLE IF EXISTS auth_user CASCADE;
DROP TABLE IF EXISTS auth_group_permissions CASCADE;
DROP TABLE IF EXISTS auth_group CASCADE;
DROP TABLE IF EXISTS auth_permission CASCADE;

-- Drop session table
DROP TABLE IF EXISTS django_session CASCADE;

COMMIT;
