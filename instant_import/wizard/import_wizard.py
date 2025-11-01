# -*- coding: utf-8 -*-
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
import json
import csv
from datetime import datetime
from io import BytesIO

import pandas as pd
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.base_import.models.base_import import FIELDS_RECURSION_LIMIT


class ImportWizard(models.TransientModel):
    _name = 'custom.import.wizard'
    _description = 'Custom Import Wizard'

    model_id = fields.Many2one(
        'ir.model', 'Model',
        required=True,
        domain=[('transient', '=', False)]
    )

    def remove_m2m_temp_columns(self, table, m2m_columns):
        for column in m2m_columns:
            self.env.cr.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column};")
        self.env.cr.execute(f"DROP TRIGGER IF EXISTS trg_process_m2m_mapping ON {table};")

    def get_m2m_details(self, model_name, field_name):
        model = self.env[model_name]
        field = model._fields[field_name]
        return {
            'relation_table': field.relation,
            'column1': field.column1,
            'column2': field.column2
        }

    @api.model
    def validate_columns(self, res_id, model, columns):
        try:
            uploaded_columns = [item['fieldInfo']['id'] for item in columns if 'fieldInfo' in item]
            if len(uploaded_columns) < len(columns):
                invalid_columns = [col.get('name', 'Unknown') for col in columns if 'fieldInfo' not in col]
                return {
                    'is_valid': False,
                    'invalid_columns': invalid_columns,
                    'error_type': 'invalid_columns'
                }

            missing_required = self._check_missing_required_fields_for_validation(model, columns)
            if missing_required:
                return {
                    'is_valid': False,
                    'missing_required_fields': missing_required,
                    'error_type': 'missing_required_fields',
                    'error_message': _("Required fields missing: %s. Please add these columns to your Excel file.") % ', '.join(missing_required)
                }

            return {'is_valid': True}
        except Exception as e:
            return {
                'is_valid': False,
                'error_type': 'validation_error',
                'error_message': _("Validation failed: %s") % str(e)
            }

    def _check_missing_required_fields_for_validation(self, model_name, columns):
        try:
            imported_fields = set()
            for item in columns:
                if 'fieldInfo' in item:
                    field_name = item['fieldInfo']['id'].split('/')[0] if '/' in item['fieldInfo']['id'] else item['fieldInfo']['id']
                    imported_fields.add(field_name)

            Model = self.env[model_name]
            model_fields = Model.fields_get()
            required_fields = [
                fname for fname, field in model_fields.items()
                if field.get('required') and field.get('store') and not field.get('deprecated', False)
            ]

            defaults = Model.default_get(list(model_fields.keys()))
            odoo_defaults = {k: v for k, v in defaults.items() if v is not None}
            auto_generated_fields = self._get_auto_generated_fields(model_name, required_fields)

            missing = []
            for field in set(required_fields) - imported_fields:
                if field not in odoo_defaults and field not in auto_generated_fields:
                    missing.append(field)

            return missing
        except Exception:
            return []

    def _get_auto_generated_fields(self, model_name, required_fields):
        auto_generated_fields = set()
        try:
            model_obj = self.env[model_name]
            try:
                all_field_names = list(model_obj.fields_get().keys())
                defaults = model_obj.default_get(all_field_names)
                fields_with_defaults = {k for k, v in defaults.items() if v is not None}
            except Exception:
                fields_with_defaults = set()

            for field_name in required_fields:
                if field_name in model_obj._fields:
                    field_obj = model_obj._fields[field_name]
                    if (
                        getattr(field_obj, 'compute', False)
                        or getattr(field_obj, 'related', False)
                        or getattr(field_obj, 'default', False)
                        or field_name in fields_with_defaults
                        or field_name in ['create_date', 'write_date', 'create_uid', 'write_uid']
                    ):
                        auto_generated_fields.add(field_name)
                    if field_obj.type == 'many2one':
                        # Generic company/currency lookup if attribute exists
                        attr_name = field_name.replace('_id', '')
                        if hasattr(self.env, 'company') and hasattr(self.env.company, attr_name):
                            auto_generated_fields.add(field_name)
        except Exception:
            pass
        return auto_generated_fields

    def _handle_special_required_fields(self, data, model_name, model_fields, missing_required):
        try:
            Model = self.env[model_name]
            defaults = Model.default_get(list(model_fields.keys()))

            for field in missing_required:
                if field in model_fields and model_fields[field]['type'] == 'many2one' and field not in data.columns:
                    rel_model = model_fields[field]['relation']
                    rec = self.env[rel_model].search([], limit=1)
                    if rec:
                        data[field] = [rec.id] * len(data)
                elif field not in data.columns and field in defaults:
                    data[field] = [defaults[field]] * len(data)
                elif field == 'user_id' and hasattr(self.env, 'uid') and field not in data.columns:
                    data[field] = [self.env.uid] * len(data)

            for field in missing_required:
                if (field in model_fields and
                    model_fields[field]['type'] in ['date', 'datetime']
                    and (field not in data.columns or data[field].isna().all())
                ):
                    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    data[field] = [now_str] * len(data)
        except Exception:
            pass

    def _build_reference_cache(self, model, values, reference_cache):
        cache_key = model
        if cache_key not in reference_cache:
            reference_cache[cache_key] = {}

        Model = self.env[model]
        unique_values = list(set(str(v).strip() for v in values if pd.notna(v) and v not in ['', 0, '0']))
        if not unique_values:
            return

        id_values = []
        for val in unique_values:
            try:
                id_val = int(float(val))
                id_values.append(id_val)
            except Exception:
                pass

        if id_values:
            records = Model.browse(id_values).exists()
            for record in records:
                reference_cache[cache_key][str(record.id)] = record.id

        search_fields = ['name', 'complete_name', 'code']
        for field_name in search_fields:
            if field_name in Model._fields and Model._fields[field_name].store:
                try:
                    records = Model.search([(field_name, 'in', unique_values)])
                    for record in records:
                        field_value = getattr(record, field_name, None)
                        if field_value:
                            reference_cache[cache_key][str(field_value)] = record.id
                except Exception:
                    continue

    def _resolve_reference(self, model, value, reference_cache):
        if pd.isna(value) or value in ['', 0, '0']:
            return None

        cache_key = model
        str_val = str(value).strip()

        if cache_key in reference_cache:
            cached_id = reference_cache[cache_key].get(str_val)
            if cached_id is not None:
                return cached_id

        Model = self.env[model]
        try:
            record_id = int(float(str_val))
            record = Model.browse(record_id).exists()
            if record:
                return record.id
        except Exception:
            pass

        try:
            return self.env.ref(str_val).id
        except Exception:
            pass

        if model == 'res.users':
            user = Model.search([
                '|', '|',
                ('name', '=ilike', str_val),
                ('login', '=ilike', str_val),
                ('email', '=ilike', str_val)
            ], limit=1)
            if user:
                if cache_key not in reference_cache:
                    reference_cache[cache_key] = {}
                reference_cache[cache_key][str_val] = user.id
                return user.id

        search_fields = ['name', 'complete_name', 'code']
        for field_name in search_fields:
            if field_name in Model._fields and Model._fields[field_name].store:
                try:
                    record = Model.search([(field_name, '=ilike', str_val)], limit=1)
                    if record:
                        if cache_key not in reference_cache:
                            reference_cache[cache_key] = {}
                        reference_cache[cache_key][str_val] = record.id
                        return record.id
                except Exception:
                    continue

        return None

    def get_required_fields(self, model_name):
        Model = self.env[model_name]
        model_fields = Model.fields_get()
        required_fields = []
        for field_name, field in model_fields.items():
            if field.get('required') and field.get('store') and not field.get('deprecated', False):
                required_fields.append({'name': field_name, 'type': field['type']})
        return required_fields

    def _get_sequence_for_model(self, model_name):
        seq = self.env['ir.sequence'].search([('code', '=', model_name)], limit=1)
        return seq or False

    def _generate_bulk_sequences(self, sequence, count):
        if not sequence or count <= 0:
            return []
        if hasattr(sequence, '_next_do'):
            return [sequence._next_do() for _ in range(count)]
        else:
            return [sequence._next() for _ in range(count)]

    def _get_model_defaults(self, model_name):
        try:
            Model = self.env[model_name]
            field_names = list(Model.fields_get().keys())
            defaults = Model.default_get(field_names)
            return {k: v for k, v in defaults.items() if v is not None}
        except Exception:
            return {}

    def _prepare_generic_defaults(self, model_name):
        return self._get_model_defaults(model_name)

    def _check_missing_required_fields(self, model_name, imported_fields, defaults):
        Model = self.env[model_name]
        model_fields = Model.fields_get()
        required_fields = []
        for field_name, field_info in model_fields.items():
            if field_info.get('required') and field_info.get('store') and not field_info.get('deprecated', False):
                required_fields.append(field_name)
        missing_required = set(required_fields) - imported_fields
        auto_generated_fields = self._get_auto_generated_fields(model_name, list(missing_required))
        missing_without_fallback = []
        for field in missing_required:
            if field not in defaults and field not in auto_generated_fields:
                missing_without_fallback.append(field)
        return missing_without_fallback

    def _get_next_sequence_values(self, table_name, count):
        try:
            self.env.cr.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
            max_id = self.env.cr.fetchone()[0]
            ids_to_use = list(range(max_id + 1, max_id + count + 1))
            sequence_name = f"{table_name}_id_seq"
            new_seq_val = max_id + count + 100
            self.env.cr.execute(f"SELECT setval('{sequence_name}', %s, false)", (new_seq_val,))
            return ids_to_use
        except Exception as e:
            try:
                self.env.cr.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
                max_id = self.env.cr.fetchone()[0]
                return list(range(max_id + 1, max_id + count + 1))
            except Exception:
                raise UserError(f"Unable to generate unique IDs: {str(e)}")

    def _sync_sequence_after_import(self, table_name):
        try:
            self.env.cr.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
            max_id = self.env.cr.fetchone()[0]
            sequence_name = f"{table_name}_id_seq"
            new_seq_val = max_id + 1000
            self.env.cr.execute(f"SELECT setval('{sequence_name}', %s)", (new_seq_val,))
        except Exception:
            try:
                self.env.cr.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
                max_id = self.env.cr.fetchone()[0]
                sequence_name = f"{table_name}_id_seq"
                self.env.cr.execute(f"SELECT setval('{sequence_name}', %s)", (max_id + 1,))
            except Exception:
                pass

    def _prepare_audit_fields(self):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return {
            'create_uid': self.env.uid,
            'write_uid': self.env.uid,
            'create_date': current_time,
            'write_date': current_time
        }

    @api.model
    def copy_import(self, res_id, model, columns):
        try:
            reference_cache = {}
            validation_result = self.validate_columns(res_id, model, columns)
            if not validation_result.get('is_valid', False):
                error_message = validation_result.get('error_message', 'Validation failed')
                raise UserError(error_message)

            required_fields = [f['name'] for f in self.get_required_fields(model)]
            model_fields = self.env[model].fields_get()

            column_mapping = {}
            imported_fields = set()
            for item in columns:
                if 'fieldInfo' in item:
                    field_name = item['fieldInfo']['id'].split('/')[0] if '/' in item['fieldInfo']['id'] else item['fieldInfo']['id']
                    column_mapping[item.get('name', field_name)] = field_name
                    imported_fields.add(field_name)

            defaults = self._prepare_generic_defaults(model)
            missing_without_fallback = self._check_missing_required_fields(model, imported_fields, defaults)
            if missing_without_fallback:
                missing_fields_str = ', '.join(missing_without_fallback)
                error_message = _(
                    "The following required fields are missing from your Excel file and cannot be auto-generated: %s. Please add these columns to your Excel file or ensure they have values."
                ) % missing_fields_str
                raise UserError(error_message)

            missing_required = set(required_fields) - imported_fields
            table_name = self.env[model]._table

            m2m_columns = []
            m2m_trigger_val = {}
            has_complex_fields = False

            for item in columns:
                if 'fieldInfo' not in item:
                    continue
                if item["fieldInfo"].get("type") == "many2many":
                    has_complex_fields = True
                    val = self.get_m2m_details(item['fieldInfo']['model_name'], item['fieldInfo']['id'])
                    m2m = f"m2m__{item['fieldInfo']['id']}"
                    m2m_trigger_val[m2m] = {
                        "data_table": self.env[item['fieldInfo']['comodel_name']]._table,
                        "mapping_table": val['relation_table'],
                        "column1": val['column1'],
                        "column2": val['column2'],
                    }
                    m2m_columns.append(m2m)
                    self.env.cr.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {m2m} TEXT;")

            model_record = self.env['ir.model'].search([('model', '=', model)], limit=1)
            if not model_record:
                raise UserError(_("Model '%s' does not exist.") % model)

            initial_count = self.env[model].search_count([])

            import_record = self.env['base_import.import'].browse(res_id).file
            file_stream = BytesIO(import_record)

            data = pd.read_excel(file_stream, dtype=str)
            data = data.replace({pd.NA: None, '': None})
            data = data.drop_duplicates()
            data = data.rename(columns=column_mapping)

            for field in missing_required:
                if field not in data.columns and field in defaults:
                    data[field] = [defaults[field]] * len(data)

            self._handle_special_required_fields(data, model, model_fields, missing_required)

            if 'state' in model_fields and model_fields['state']['type'] == 'selection':
                if 'state' not in data.columns:
                    state_default = defaults.get('state', 'draft')
                    data['state'] = [state_default] * len(data)
                else:
                    state_default = defaults.get('state', 'draft')
                    state_values = []
                    for val in data['state']:
                        if pd.isna(val) or (isinstance(val, str) and val.strip() == ''):
                            state_values.append(state_default)
                        else:
                            state_values.append(val)
                    data['state'] = state_values

            many2one_fields = {}
            for column in data.columns:
                if column in model_fields and model_fields[column]['type'] == 'many2one':
                    comodel = model_fields[column]['relation']
                    many2one_fields[column] = comodel
                    self._build_reference_cache(comodel, data[column], reference_cache)

            for column, comodel in many2one_fields.items():
                resolved_values = []
                for value in data[column]:
                    resolved_id = self._resolve_reference(comodel, value, reference_cache) if pd.notna(value) else None
                    resolved_values.append(resolved_id)
                data[column] = resolved_values

            for column in data.columns:
                if column in model_fields and model_fields[column]['type'] == 'selection':
                    selection_values = model_fields[column]['selection']
                    if isinstance(selection_values, list):
                        selection_map = {v.lower(): k for k, v in selection_values}
                        selection_map.update({k.lower(): k for k, v in selection_values})
                        mapped_values = []
                        for value in data[column]:
                            if pd.isna(value):
                                mapped_values.append(None)
                            else:
                                str_val = str(value).strip().lower()
                                mapped_values.append(selection_map.get(str_val, value))
                        data[column] = mapped_values

            fields_to_import = list(imported_fields.union(missing_required))

            if 'state' in model_fields and 'state' in data.columns and 'state' not in fields_to_import:
                fields_to_import.append('state')

            available_fields = [f for f in fields_to_import if f in data.columns]

            for field in fields_to_import:
                if field not in available_fields and (field in defaults or field in data.columns):
                    if field in data.columns:
                        available_fields.append(field)
                    elif field in defaults:
                        data[field] = defaults[field]
                        available_fields.append(field)

            final_fields = [f for f in available_fields if f in model_fields or f == 'id']

            if not final_fields:
                raise UserError(_("No valid fields found for import"))

            try:
                self.env.cr.execute(f"DROP TRIGGER IF EXISTS trg_process_m2m_mapping ON {table_name};")
            except Exception:
                pass

            return self._postgres_bulk_import(data, model, final_fields, m2m_trigger_val, m2m_columns,
                                              table_name, model_fields, initial_count, model_record,
                                              has_complex_fields, reference_cache)
        except UserError:
            raise
        except Exception as e:
            raise UserError(_("Import failed: %s") % str(e))

    def _postgres_bulk_import(self, data, model, final_fields, m2m_trigger_val, m2m_columns,
                              table_name, model_fields, initial_count, model_record,
                              has_complex_fields, reference_cache):
        try:
            if 'name' in model_fields:
                sequence = self._get_sequence_for_model(model)
                needs_sequence = False
                name_in_data = 'name' in data.columns

                if not name_in_data:
                    needs_sequence = True
                else:
                    non_null_names = data['name'].dropna()
                    if len(non_null_names) == 0:
                        needs_sequence = True
                    else:
                        name_check_results = [
                            str(val).strip().lower() in ['new', '', 'false'] for val in non_null_names
                        ]
                        needs_sequence = all(name_check_results)

                if sequence and needs_sequence:
                    record_count = len(data)
                    if record_count > 0:
                        try:
                            sequence_values = self._generate_bulk_sequences(sequence, record_count)
                            data['name'] = sequence_values
                            if 'name' not in final_fields:
                                final_fields.append('name')
                        except Exception:
                            pass
                elif not sequence and needs_sequence:
                    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                    data['name'] = [f"New-{timestamp}-{i + 1}" for i in range(len(data))]
                    if 'name' not in final_fields:
                        final_fields.append('name')

            audit_fields = self._prepare_audit_fields()
            audit_field_names = ['create_uid', 'write_uid', 'create_date', 'write_date']

            for audit_field in audit_field_names:
                if audit_field in model_fields and audit_field not in final_fields:
                    data[audit_field] = [audit_fields[audit_field]] * len(data)
                    final_fields.append(audit_field)

            if 'id' not in final_fields:
                record_count = len(data)
                if record_count > 0:
                    try:
                        next_ids = self._get_next_sequence_values(table_name, record_count)
                        data['id'] = next_ids
                        final_fields.insert(0, 'id')
                    except Exception:
                        if 'id' in final_fields:
                            final_fields.remove('id')
                        if 'id' in data.columns:
                            data = data.drop(columns=['id'])

            if has_complex_fields and m2m_trigger_val:
                vals = json.dumps(m2m_trigger_val)
                self.env.cr.execute(
                    f"CREATE OR REPLACE TRIGGER trg_process_m2m_mapping AFTER INSERT ON {table_name} "
                    f"FOR EACH ROW EXECUTE FUNCTION process_m2m_mapping('{vals}');"
                )

            data = data[final_fields]
            default_lang = self.env.context.get('lang') or getattr(self.env, 'lang', None) or 'en_US'
            translatable_columns = set()

            for column in data.columns:
                if column in model_fields:
                    field_info = model_fields[column]
                    if field_info.get('translate') and field_info.get('store'):
                        translatable_columns.add(column)

                        def _to_jsonb_value(val):
                            if pd.isna(val) or val is None:
                                return None
                            if isinstance(val, dict):
                                try:
                                    return json.dumps(val, ensure_ascii=False)
                                except Exception:
                                    return json.dumps({default_lang: str(val)}, ensure_ascii=False)
                            s = str(val).strip()
                            if s == '':
                                return None
                            if s.startswith('{') or s.startswith('['):
                                try:
                                    parsed = json.loads(s)
                                    return json.dumps(parsed, ensure_ascii=False)
                                except Exception:
                                    return json.dumps({default_lang: s}, ensure_ascii=False)
                            return json.dumps({default_lang: s}, ensure_ascii=False)

                        try:
                            jsonb_values = [_to_jsonb_value(val) for val in data[column]]
                            data[column] = jsonb_values
                        except Exception:
                            pass

            for column in data.columns:
                if column in model_fields and column not in translatable_columns:
                    field_info = model_fields[column]
                    field_type = field_info['type']

                    if field_type in ['char', 'text']:
                        data[column] = (data[column].astype(str)
                                        .str.replace(r'[\n\r]+', ' ', regex=True)
                                        .str.strip())
                        data[column] = data[column].replace(['nan', 'None'], None)
                    elif field_type in ['integer', 'float']:
                        if model_fields[column].get('required', False):
                            data[column] = pd.to_numeric(data[column], errors='coerce').fillna(0)
                        else:
                            data[column] = pd.to_numeric(data[column], errors='coerce')
                    elif field_type == 'boolean':
                        data[column] = data[column].fillna(False)
                        data[column] = ['t' if bool(val) else 'f' for val in data[column]]
                    elif field_type in ['date', 'datetime']:
                        formatted_dates = []
                        current_datetime = datetime.now()

                        for val in data[column]:
                            if pd.isna(val) or val in ['', None, 'nan', 'None']:
                                formatted_dates.append(current_datetime.strftime('%Y-%m-%d %H:%M:%S'))
                            else:
                                try:
                                    if isinstance(val, str):
                                        parsed_date = pd.to_datetime(val, errors='coerce')
                                        if pd.isna(parsed_date):
                                            parsed_date = datetime.strptime(val, '%Y-%m-%d')
                                        formatted_dates.append(parsed_date.strftime('%Y-%m-%d %H:%M:%S'))
                                    elif hasattr(val, 'strftime'):
                                        formatted_dates.append(val.strftime('%Y-%m-%d %H:%M:%S'))
                                    else:
                                        formatted_dates.append(str(val))
                                except Exception:
                                    formatted_dates.append(current_datetime.strftime('%Y-%m-%d %H:%M:%S'))
                        data[column] = formatted_dates
                    elif field_type == 'many2one':
                        data[column] = pd.to_numeric(data[column], errors='coerce').astype('Int64')

            csv_buffer = BytesIO()
            data_for_copy = data.copy()

            for column in data_for_copy.columns:
                if column in model_fields:
                    field_info = model_fields[column]
                    field_type = field_info['type']

                    if field_info.get('translate') and field_info.get('store'):
                        translate_values = [str(val) if val is not None and not pd.isna(val) else '' for val in data_for_copy[column]]
                        data_for_copy[column] = translate_values
                    elif field_type in ['integer', 'float', 'many2one']:
                        numeric_values = []
                        for val in data_for_copy[column]:
                            if val is None or pd.isna(val):
                                numeric_values.append('')
                            else:
                                try:
                                    if field_type in ['integer', 'many2one']:
                                        numeric_values.append(str(int(float(val))))
                                    else:
                                        numeric_values.append(str(val))
                                except Exception:
                                    numeric_values.append('')
                        data_for_copy[column] = numeric_values
                    else:
                        other_values = [str(val) if val is not None and not pd.isna(val) else '' for val in data_for_copy[column]]
                        data_for_copy[column] = other_values

            data_for_copy.to_csv(
                csv_buffer, index=False, header=False, sep='|',
                na_rep='', quoting=csv.QUOTE_MINIMAL, doublequote=True
            )
            csv_buffer.seek(0)

            self.env.cr.execute(f"ALTER TABLE {table_name} DISABLE TRIGGER ALL;")
            if has_complex_fields and m2m_trigger_val:
                self.env.cr.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER trg_process_m2m_mapping;")

            fields_str = ",".join(final_fields)
            copy_sql = f"""
                COPY {table_name} ({fields_str}) 
                FROM STDIN WITH (
                    FORMAT CSV,
                    HEADER FALSE,
                    DELIMITER '|',
                    NULL '',
                    QUOTE '"'
                )
            """

            start_time = datetime.now()
            self.env.cr.copy_expert(copy_sql, csv_buffer)
            record_count = len(data)

            if record_count > 500:
                self.env.cr.commit()

            end_time = datetime.now()
            import_duration = (end_time - start_time).total_seconds()

            self._sync_sequence_after_import(table_name)
            self.env.cr.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER ALL;")

            if has_complex_fields and m2m_trigger_val:
                self.remove_m2m_temp_columns(table_name, m2m_columns)

            self.env.invalidate_all()
            self.env.cr.execute(f"ANALYZE {table_name};")

            final_count = self.env[model].search_count([])
            imported_count = final_count - initial_count

            return {
                'name': model_record.name,
                'record_count': imported_count,
                'duration': import_duration
            }

        except Exception as e:
            try:
                self.env.cr.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER ALL;")
            except Exception:
                pass

            if has_complex_fields and m2m_trigger_val:
                try:
                    self.remove_m2m_temp_columns(table_name, m2m_columns)
                except Exception:
                    pass

            raise UserError(_("Failed to import data: %s") % str(e))


class Import(models.TransientModel):
    _inherit = 'base_import.import'

    @api.model
    def get_fields_tree(self, model, depth=FIELDS_RECURSION_LIMIT):
        Model = self.env[model]
        importable_fields = [{
            'id': 'id',
            'name': 'id',
            'string': _("External ID"),
            'required': False,
            'fields': [],
            'type': 'id',
        }]

        if not depth:
            return importable_fields

        model_fields = Model.fields_get()
        for name, field in model_fields.items():
            if field.get('deprecated', False) is not False:
                continue
            if not field.get('store'):
                continue
            if field['type'] == 'one2many':
                continue

            field_value = {
                'id': name,
                'name': name,
                'string': field['string'],
                'required': bool(field.get('required')),
                'fields': [],
                'type': field['type'],
                'model_name': model
            }

            if field['type'] in ('many2many', 'many2one'):
                field_value['fields'] = [
                    dict(field_value, name='id', string=_("External ID"), type='id'),
                    dict(field_value, name='.id', string=_("Database ID"), type='id'),
                ]
                field_value['comodel_name'] = field['relation']

            importable_fields.append(field_value)

        return importable_fields