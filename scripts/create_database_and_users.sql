/* -----------------------------------------------------------------------------
History:
  2026-02-16 Brandon Worthington - Added.
 
Purpose:
  - Create the application database
  - Create users for daily human admin use, the app, and migrations
  - Apply grants

How to use (TablePlus or other local MySQL client):
  1) Connect as root (or Cloud SQL admin user) via Cloud SQL Auth Proxy.
  2) Replace the password placeholders below.
  3) Run the script.

Notes:
  - Database and user names do not have dev or prod indicators because the Cloud
    SQL instance name/ID already specifies the environment.
  - Explicit charset/collation for consistency across dev/prod.
  - Do NOT commit real passwords to git.
----------------------------------------------------------------------------- */

-- 1) App database
CREATE DATABASE IF NOT EXISTS bustracker
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

-- 2) Admin user for TablePlus (day-to-day human access)
CREATE USER IF NOT EXISTS 'bustracker_admin'@'%' IDENTIFIED BY 'REPLACE_ME_ADMIN_PW';
GRANT ALL PRIVILEGES ON bustracker.* TO 'bustracker_admin'@'%';

-- 3) App user for Flask (application runtime user)
CREATE USER IF NOT EXISTS 'bustracker_app'@'%' IDENTIFIED BY 'REPLACE_ME_APP_PW';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON bustracker.* TO 'bustracker_app'@'%';

-- 4) Migrate user for database migrations (creating/altering tables, etc.)
CREATE USER IF NOT EXISTS 'bustracker_migrate'@'%' IDENTIFIED BY 'REPLACE_ME_MIGRATE_PW';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES
  ON bustracker.* TO 'bustracker_migrate'@'%';

-- 5) Apply
FLUSH PRIVILEGES;

-- 6) Verification helpers
SHOW DATABASES;
SHOW GRANTS FOR 'bustracker_admin'@'%';
SHOW GRANTS FOR 'bustracker_app'@'%';
SHOW GRANTS FOR 'bustracker_migrate'@'%';

SELECT
  default_character_set_name AS db_charset,
  default_collation_name AS db_collation
FROM information_schema.SCHEMATA
WHERE schema_name = 'bustracker';
