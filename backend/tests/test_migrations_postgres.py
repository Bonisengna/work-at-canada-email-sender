import os

import psycopg
import pytest

DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL is required for PostgreSQL migration tests")
def test_schema_and_critical_constraints() -> None:
    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute("select version_num from alembic_version")
            assert cursor.fetchone() == ("20260824_0001",)

            cursor.execute(
                "select count(*) from pg_tables where schemaname = 'public' and rowsecurity"
            )
            assert cursor.fetchone() == (21,)

            cursor.execute("select count(*) from job_sources")
            assert cursor.fetchone() == (6,)

            cursor.execute(
                """
                select column_name from information_schema.columns
                where table_schema = 'public' and table_name = 'user_settings'
                  and column_name in (
                    'ai_api_key_encrypted',
                    'google_access_token_encrypted',
                    'google_refresh_token_encrypted'
                  )
                """
            )
            assert {row[0] for row in cursor.fetchall()} == {
                "ai_api_key_encrypted",
                "google_access_token_encrypted",
                "google_refresh_token_encrypted",
            }

            cursor.execute(
                """
                insert into users(id, email, password_hash)
                values (gen_random_uuid(), 'schema-test@example.com', 'not-a-real-hash')
                returning id
                """
            )
            user_id = cursor.fetchone()[0]

            cursor.execute("savepoint before_invalid_target")
            with pytest.raises(psycopg.errors.CheckViolation):
                cursor.execute(
                    "insert into user_settings(user_id, daily_email_target) values (%s, 7)",
                    (user_id,),
                )
            cursor.execute("rollback to savepoint before_invalid_target")

            cursor.execute("savepoint before_invalid_contact")
            with pytest.raises(psycopg.errors.CheckViolation):
                cursor.execute(
                    """
                    with company as (
                      insert into companies(normalized_name, display_name)
                      values ('migration-test-company', 'Migration Test Company')
                      returning id
                    )
                    insert into company_contacts(
                      company_id, email, normalized_email, contact_type,
                      is_personal, approval_status
                    )
                    select id, 'person@example.com', 'person@example.com',
                           'personal', true, 'approved'
                    from company
                    """
                )
            cursor.execute("rollback to savepoint before_invalid_contact")

        connection.rollback()
