# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
def setup_db_level_functions(env):
    env.cr.execute(
        """
        CREATE OR REPLACE FUNCTION process_o2m_mapping()
        RETURNS TRIGGER AS $$
        DECLARE
            values json;
            field_name TEXT;
            field_config json;
            record_data json;
            field_value text;
            column_info record;
            column_list text;
            value_list text;
            debug_msg text;
        BEGIN
            values := TG_ARGV[0]::json;

            FOR field_name, field_config IN SELECT * FROM json_each(values::json) LOOP
                EXECUTE format('SELECT ($1).%I::text', field_name)
                INTO field_value
                USING NEW;

                IF field_value IS NOT NULL THEN
                    FOR record_data IN SELECT * FROM json_array_elements(field_value::json) LOOP
                        -- Log the record data for debugging
                        RAISE NOTICE 'Record data: %', record_data;

                        SELECT 
                            string_agg(quote_ident(c.column_name), ', '),
                            string_agg(
                                CASE 
                                    WHEN c.data_type IN ('integer', 'bigint') THEN format('CAST(($2->>%L) AS INTEGER)', c.column_name)
                                    WHEN c.data_type = 'numeric' THEN format('CAST(($2->>%L) AS NUMERIC)', c.column_name)
                                    WHEN c.data_type = 'double precision' THEN format('CAST(($2->>%L) AS DOUBLE PRECISION)', c.column_name)
                                    WHEN c.data_type = 'boolean' THEN format('CAST(($2->>%L) AS BOOLEAN)', c.column_name)
                                    WHEN c.data_type = 'date' THEN format('CAST(($2->>%L) AS DATE)', c.column_name)
                                    -- FIXED: Handle all timestamp variations
                                    WHEN c.data_type IN ('timestamp without time zone', 'timestamp with time zone') 
                                        THEN format('CAST(($2->>%L) AS TIMESTAMP)', c.column_name)
                                    WHEN c.data_type = 'datetime' THEN format('CAST(($2->>%L) AS TIMESTAMP)', c.column_name)
                                    ELSE format('$2->>%L', c.column_name)
                                END, 
                                ', '
                            )
                        INTO 
                            column_list,
                            value_list
                        FROM information_schema.columns c
                        WHERE c.table_name = field_config->>'data_table'
                        AND c.column_name = ANY (
                            ARRAY(SELECT key::text FROM json_object_keys(record_data) AS t(key))
                        );

                        -- Add the inverse_name column and value
                        column_list := quote_ident(field_config->>'inverse_name') || ', ' || COALESCE(column_list, '');
                        value_list := '$1, ' || COALESCE(value_list, '');

                        -- Build the complete SQL statement
                        debug_msg := format(
                            'INSERT INTO %I (%s) VALUES (%s)',
                            field_config->>'data_table',
                            column_list,
                            value_list
                        );

                        EXECUTE debug_msg
                        USING NEW.id, record_data;
                    END LOOP;
                END IF;
            END LOOP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    env.cr.execute(
        """
        CREATE OR REPLACE FUNCTION process_m2m_mapping()
        RETURNS TRIGGER AS $$
        DECLARE
            col record;
            value_array text[];
            single_value text;
            id1 integer;
            id2 integer;
            dynamic_sql text;
            mapping_config jsonb;
            column_type text;
            field_config jsonb;
        BEGIN
            -- Get the mapping configuration from TG_ARGV[0]
            -- Expected format:
            -- {
            --   "m2m__field1": {"data_table": "table1", "mapping_table": "map1", "column1": "col1", "column2": "col2"},
            --   "m2m__field2": {"data_table": "table2", "mapping_table": "map2", "column1": "col3", "column2": "col4"}
            -- }
            mapping_config := TG_ARGV[0]::jsonb;

            -- Loop through all columns of the table
            FOR col IN (
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = TG_TABLE_NAME::text
                AND column_name LIKE 'm2m__%'
            ) LOOP
                -- Get configuration for this m2m field
                field_config := mapping_config->col.column_name;

                IF field_config IS NOT NULL THEN
                    -- Only process if the column has a value
                    EXECUTE format('SELECT $1.%I', col.column_name) USING NEW INTO dynamic_sql;
                    IF dynamic_sql IS NOT NULL THEN
                        -- Get the ID from the currently triggered table
                        id1 := NEW.id;

                        -- Get the data type of the name column
                        EXECUTE format(
                            'SELECT data_type
                             FROM information_schema.columns
                             WHERE table_name = %L
                             AND column_name = ''name''',
                            field_config->>'data_table'
                        ) INTO column_type;

                        -- Split the m2m values
                        value_array := string_to_array(dynamic_sql, ',');

                        -- Process each value in the array
                        FOREACH single_value IN ARRAY value_array LOOP
                            -- Get the ID from the related table based on column type
                            IF column_type = 'jsonb' THEN
                                EXECUTE format(
                                    'SELECT id FROM %I WHERE (name->>''en_US'' = %L OR name->>''fr_FR'' = %L)',
                                    field_config->>'data_table',
                                    TRIM(single_value),
                                    TRIM(single_value)
                                ) INTO id2;

                                -- If not found, try searching without language code
                                IF id2 IS NULL THEN
                                    EXECUTE format(
                                        'SELECT id FROM %I WHERE (name->''en_US'' ? %L OR name->''fr_FR'' ? %L)',
                                        field_config->>'data_table',
                                        TRIM(single_value),
                                        TRIM(single_value)
                                    ) INTO id2;
                                END IF;
                            ELSE
                                -- For text type
                                EXECUTE format(
                                    'SELECT id FROM %I WHERE name = %L',
                                    field_config->>'data_table',
                                    TRIM(single_value)
                                ) INTO id2;
                            END IF;

                            -- Insert into mapping table if both IDs are found
                            IF id1 IS NOT NULL AND id2 IS NOT NULL THEN
                                EXECUTE format(
                                    'INSERT INTO %I (%I, %I)
                                     VALUES (%L, %L)
                                     ON CONFLICT (%I, %I) DO NOTHING',
                                    field_config->>'mapping_table',
                                    field_config->>'column1',
                                    field_config->>'column2',
                                    id1, id2,
                                    field_config->>'column1',
                                    field_config->>'column2'
                                );
                            END IF;
                        END LOOP;
                    END IF;
                END IF;
            END LOOP;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

def delete_contact(env):
    env.cr.execute(
        """
        DROP FUNCTION IF EXISTS process_m2m_mapping();
        DROP FUNCTION IF EXISTS process_o2m_mapping();
        """
    )
