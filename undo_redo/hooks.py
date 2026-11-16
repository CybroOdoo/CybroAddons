# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Post initialization hook to create PostgreSQL triggers and functions
    for tracking record updates and deletions across database tables."""
    env.cr.execute("""
        CREATE OR REPLACE FUNCTION log_update_data()
        RETURNS TRIGGER AS $$
        DECLARE
            changed_fields JSONB = '{}'::JSONB;
            old_row JSONB;
            new_row JSONB;
            column_name TEXT;
        BEGIN
            old_row = to_jsonb(OLD);
            new_row = to_jsonb(NEW);

            FOR column_name IN SELECT jsonb_object_keys(old_row)
            LOOP
                IF old_row ->> column_name IS DISTINCT FROM new_row ->> column_name THEN
                    changed_fields = jsonb_set(
                        changed_fields,
                        array[column_name],
                        old_row -> column_name
                    );
                END IF;
            END LOOP;

            IF jsonb_typeof(changed_fields) != 'null' AND changed_fields != '{}'::JSONB THEN
                BEGIN
                    INSERT INTO undo_redo (
                        user_id,
                        table_name,
                        record_id,
                        updated_data,
                        mode
                    )
                    VALUES (
                        (old_row ->> 'write_uid')::integer,
                        TG_TABLE_NAME,
                        OLD.id,
                        changed_fields,
                        'undo'
                    );
                    EXCEPTION WHEN OTHERS THEN
                        RETURN NEW;
                END;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    env.cr.execute("""
        CREATE OR REPLACE FUNCTION log_delete_data()
        RETURNS TRIGGER AS $$
        BEGIN
            DELETE FROM undo_redo
            WHERE record_id = OLD.id
            AND table_name = TG_TABLE_NAME;
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)
    env.cr.execute("""
        DO $$
        DECLARE
            rec RECORD;
        BEGIN
            FOR rec IN
                SELECT n.nspname, c.relname
                FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE c.relkind = 'r'
                AND n.nspname NOT IN ('pg_catalog', 'information_schema')
                AND c.relname NOT LIKE 'orm_signaling_%'
                AND c.relname NOT LIKE 'ir_%'
                AND c.relname NOT LIKE 'bus_%'
                AND c.relname NOT IN (
                    'undo_redo', 'base_module_uninstall', 'base_module_upgrade', 'base_module_update'
                )
                AND EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = n.nspname
                    AND table_name = c.relname
                    AND column_name = 'id'
                )
            LOOP
                EXECUTE format('
                    CREATE TRIGGER capture_delete_dynamic
                    AFTER UPDATE ON %I.%I
                    FOR EACH ROW
                    EXECUTE FUNCTION log_update_data();', rec.nspname, rec.relname);
                EXECUTE format('
                    CREATE TRIGGER log_delete_trigger
                    AFTER DELETE ON %I.%I
                    FOR EACH ROW
                    EXECUTE FUNCTION log_delete_data();',
                    rec.nspname, rec.relname);
            END LOOP;
        END $$;
    """)
    env.cr.execute("""
        CREATE OR REPLACE FUNCTION add_update_trigger_to_new_tables()
        RETURNS VOID AS $$
        DECLARE
            rec RECORD;
        BEGIN
            FOR rec IN
                SELECT n.nspname, c.relname
                FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE c.relkind = 'r'
                AND n.nspname NOT IN ('pg_catalog', 'information_schema')
                AND c.relname NOT LIKE 'orm_signaling_%'
                AND c.relname NOT LIKE 'ir_%'
                AND c.relname NOT LIKE 'bus_%'
                AND c.relname NOT IN (
                    'undo_redo', 'base_module_uninstall', 'base_module_upgrade', 'base_module_update'
                )
                AND EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = n.nspname
                    AND table_name = c.relname
                    AND column_name = 'id'
                )
            LOOP
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_trigger
                    WHERE tgrelid = (
                        SELECT oid FROM pg_class
                        WHERE relname = rec.relname
                        AND relnamespace = (
                            SELECT oid FROM pg_namespace WHERE nspname = rec.nspname
                        )
                    )
                    AND tgname = 'capture_delete_dynamic'
                ) THEN
                    IF rec.relname NOT LIKE 'orm_signaling_%'
                        AND rec.relname NOT LIKE 'ir_%'
                        AND rec.relname NOT LIKE 'bus_%'
                        AND rec.relname NOT IN (
                            'undo_redo', 'base_module_uninstall', 'base_module_upgrade', 'base_module_update'
                        ) THEN
                        EXECUTE format('
                            CREATE TRIGGER capture_delete_dynamic
                            AFTER UPDATE ON %I.%I
                            FOR EACH ROW
                            EXECUTE FUNCTION log_update_data();', rec.nspname, rec.relname);
                        EXECUTE format('
                            CREATE TRIGGER log_delete_trigger
                            AFTER DELETE ON %I.%I
                            FOR EACH ROW
                            EXECUTE FUNCTION log_delete_data();',
                            rec.nspname, rec.relname);
                    END IF;
                END IF;
            END LOOP;
        END;
        $$ LANGUAGE plpgsql;
    """)
    try:
        with env.cr.savepoint():
            env.cr.execute("""
                CREATE OR REPLACE FUNCTION trigger_on_table_creation()
                RETURNS EVENT_TRIGGER AS $$
                BEGIN
                    PERFORM add_update_trigger_to_new_tables();
                END;
                $$ LANGUAGE plpgsql;
            """)
            env.cr.execute("""
                CREATE EVENT TRIGGER auto_add_delete_triggers
                ON ddl_command_end
                WHEN TAG IN ('CREATE TABLE')
                EXECUTE FUNCTION trigger_on_table_creation();
            """)
    except Exception as e:
        _logger.info(
            "Database user lacks superuser privileges; event trigger skipped (%s). "
            "Table triggers will be maintained via registry hook.",
            e,
        )
    env.cr.execute("""
        CREATE OR REPLACE FUNCTION handle_log_reinsert()
        RETURNS TRIGGER AS $$
        DECLARE
            target_table TEXT;
            column_list TEXT;
            value_list TEXT;
            column_count INT;
            new_mode TEXT;
            latest_id INT;
        BEGIN
            IF TG_TABLE_NAME = 'undo_redo' THEN
                target_table := OLD.table_name;

                column_list := array_to_string(
                    array(SELECT jsonb_object_keys(OLD.updated_data)),
                    ', '
                );
                value_list := array_to_string(
                    array(
                        SELECT format('%L', OLD.updated_data->>key)
                        FROM jsonb_object_keys(OLD.updated_data) AS key
                    ),
                    ', '
                );

                new_mode := CASE OLD.mode
                    WHEN 'undo' THEN 'redo'
                    ELSE 'undo'
                END;
                column_count := array_length(string_to_array(column_list, ','), 1);
                IF column_count > 1 THEN
                    EXECUTE format(
                        'UPDATE %I SET (%s) = (%s) WHERE id = %L',
                        target_table,
                        column_list,
                        value_list,
                        OLD.record_id
                    );
                ELSIF column_count = 1 THEN
                    EXECUTE format(
                        'UPDATE %I SET %s = %s WHERE id = %L',
                        target_table,
                        column_list,
                        value_list,
                        OLD.record_id
                    );
                END IF;
                SELECT id INTO latest_id
                FROM undo_redo
                WHERE table_name = OLD.table_name
                AND record_id = OLD.record_id
                ORDER BY id DESC
                LIMIT 1;

                UPDATE undo_redo
                SET mode = new_mode
                WHERE id = latest_id;

                RETURN OLD;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)
    env.cr.execute("""
        CREATE TRIGGER after_delete_trigger
        AFTER DELETE ON undo_redo
        FOR EACH ROW
        EXECUTE FUNCTION handle_log_reinsert();
    """)


def uninstall_hook(env):
    """Uninstall hook to drop all created triggers and functions."""
    try:
        with env.cr.savepoint():
            env.cr.execute("""
                DROP EVENT TRIGGER IF EXISTS auto_add_delete_triggers;
            """)
    except Exception as e:
        _logger.warning("Could not drop event trigger auto_add_delete_triggers: %s", e)
    env.cr.execute("""
        DROP TRIGGER IF EXISTS after_delete_trigger ON undo_redo;
    """)
    env.cr.execute("""
        DO $$
        DECLARE
            rec RECORD;
        BEGIN
            SET LOCAL lock_timeout = '200ms';
            FOR rec IN
                SELECT n.nspname, c.relname, t.tgname
                FROM pg_trigger t
                JOIN pg_class c ON t.tgrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE t.tgname IN ('capture_delete_dynamic', 'log_delete_trigger')
                  AND NOT t.tgisinternal
            LOOP
                BEGIN
                    EXECUTE format('DROP TRIGGER IF EXISTS %I ON %I.%I;',
                        rec.tgname, rec.nspname, rec.relname);
                EXCEPTION WHEN OTHERS THEN
                    NULL;
                END;
            END LOOP;
        END $$;
    """)
    functions_to_drop = [
        "log_update_data()",
        "log_delete_data()",
        "add_update_trigger_to_new_tables()",
        "trigger_on_table_creation()",
        "handle_log_reinsert()",
    ]
    for func in functions_to_drop:
        try:
            with env.cr.savepoint():
                env.cr.execute(f"DROP FUNCTION IF EXISTS {func} CASCADE;")
        except Exception as e:
            _logger.warning("Could not drop function %s: %s", func, e)
