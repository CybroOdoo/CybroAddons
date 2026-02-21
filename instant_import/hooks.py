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
            field_name TEXT;
            field_config jsonb;
            field_value_jsonb jsonb;
            column_list TEXT;
        BEGIN
            -- TG_ARGV[0] is the config passed from the trigger creation
            FOR field_name, field_config IN SELECT * FROM jsonb_each(TG_ARGV[0]::jsonb) LOOP
                
                -- Pull the O2M data from the parent column
                EXECUTE format('SELECT ($1).%I::jsonb', field_name) INTO field_value_jsonb USING NEW;

                IF field_value_jsonb IS NOT NULL AND jsonb_array_length(field_value_jsonb) > 0 THEN
                    
                    -- Extract only the keys present in the JSON
                    SELECT string_agg(quote_ident(key), ', ') 
                    INTO column_list 
                    FROM jsonb_object_keys(field_value_jsonb->0) AS t(key);

                    -- THE FIX: We list columns in both the INSERT and the SELECT.
                    -- This prevents the '*' mismatch error.
                    EXECUTE format(
                        'INSERT INTO %I (%I, %s) 
                         SELECT $1, %s FROM jsonb_populate_recordset(NULL::%I, $2)',
                        field_config->>'data_table',
                        field_config->>'inverse_name',
                        column_list,
                        column_list,
                        field_config->>'data_table'
                    ) USING NEW.id, field_value_jsonb;

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
