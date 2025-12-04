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
import json
import logging
from datetime import datetime
from io import BytesIO
import re

import pandas as pd
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.base_import.models.base_import import FIELDS_RECURSION_LIMIT

_logger = logging.getLogger(__name__)


class ImportWizard(models.TransientModel):
    _name = 'custom.import.wizard'
    _description = 'Custom Import Wizard'

    model_id = fields.Many2one('ir.model', 'Model', required=True,
                               domain=[('transient', '=', False)])

    def _get_sequence_for_model(self, model_name):
        """
            Returns the most suitable ir.sequence record for the given model name.
            The method tries multiple matching strategies: exact code match, partial
            match using the last part of the model name, prefix/name lookup, and
            fallback token searches. If no matching sequence is found, it returns False.
        """
        try:
            seq = self.env['ir.sequence'].search([('code', '=', model_name)], limit=1)
            if seq:
                return seq
            last_part = model_name.split('.')[-1]
            seq = self.env['ir.sequence'].search([('code', 'ilike', last_part)], limit=1)
            if seq:
                return seq
            seqs = self.env['ir.sequence'].search(['|', ('prefix', 'ilike', model_name), ('name', 'ilike', model_name)],
                                                  limit=5)
            if seqs:
                return seqs[0]
            parts = [p for p in model_name.replace('.', '_').split('_') if len(p) > 2]
            for p in parts:
                seq = self.env['ir.sequence'].search([('code', 'ilike', p)], limit=1)
                if seq:
                    return seq
            return False
        except Exception as e:
            _logger.warning(f"Sequence lookup failed for {model_name}: {e}")
            return False

    def _get_model_defaults(self, model_name):
        """
           Retrieves the default values for all fields of the given model. The method
           loads the model, fetches its field names, and uses default_get to obtain
           their default values. Only fields with non-None defaults are returned.
        """
        try:
            Model = self.env[model_name]
            field_names = list(Model.fields_get().keys())
            defaults = Model.default_get(field_names)
            return {k: v for k, v in defaults.items() if v is not None}
        except Exception as e:
            _logger.warning(f"Could not get defaults for model {model_name}: {e}")
            return {}

    def _get_common_default_context(self, model_name=None):
        """
           Builds a dictionary of common default values used during record creation.
           This includes generic fields such as company, user, dates, and state. If a
           model name is provided, the method also inspects the model's required
           fields and automatically fills required many2one fields with the first
           matching record, including special handling for UoM fields. Returns a
           context dictionary containing default values suitable for most models.
        """
        defaults = {
            'company_id': self.env.company.id,
            'currency_id': getattr(self.env.company, 'currency_id', False) and self.env.company.currency_id.id or None,
            'create_uid': self.env.uid,
            'write_uid': self.env.uid,
            'create_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'write_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'state': 'draft',
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'date_order': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        if model_name:
            try:
                Model = self.env[model_name]
                model_fields = Model.fields_get()
                # Get required fields from the model
                required_fields = []
                for fname, finfo in model_fields.items():
                    if finfo.get('required') and finfo.get('store') and not finfo.get('deprecated', False):
                        required_fields.append(fname)
                # Only auto-populate many2one fields that are REQUIRED
                for fname, finfo in model_fields.items():
                    if finfo.get('type') == 'many2one' and fname in required_fields:
                        rel_model = finfo.get('relation')
                        if not rel_model:
                            continue
                        # Skip if already in defaults
                        if fname in defaults:
                            continue
                        domain = []
                        if 'company_id' in self.env[rel_model]._fields:
                            domain = [('company_id', '=', self.env.company.id)]
                        rec = self.env[rel_model].search(domain, limit=1) if domain else self.env[rel_model].search([],
                                                                                                                    limit=1)
                        if rec:
                            defaults.setdefault(fname, rec.id)
                    # Handle UOM fields - only if required
                    elif finfo.get('type') == 'many2one' and finfo.get('relation') == 'uom.uom':
                        if fname in required_fields and fname not in defaults:
                            try:
                                rec = self.env['uom.uom'].search([], limit=1)
                                if rec:
                                    defaults[fname] = rec.id
                            except Exception:
                                pass
            except Exception as e:
                _logger.warning(f"Could not prepare model-specific defaults for {model_name}: {e}")
        return defaults

    def _get_dynamic_state_default(self, model, state_field_info):
        """
            Determines the default value for a model's state field based on its
            selection options. If the selection is dynamic (callable), it is evaluated.
            The method prioritizes returning a 'draft' state when available; otherwise,
            it returns the first selection value. In case of errors or missing data,
            'draft' is used as a fallback.
        """
        try:
            selection_values = state_field_info['selection']
            if callable(selection_values):
                selection_values = selection_values(self.env[model])
            if selection_values:
                draft_states = [val[0] for val in selection_values if val[0].lower() == 'draft']
                if draft_states:
                    return draft_states[0]
                return selection_values[0][0]
            return 'draft'
        except Exception as e:
            _logger.warning(f"Error getting dynamic state default: {e}")
            return 'draft'

    def _prepare_audit_fields(self):
        """
           Generates a dictionary containing standard audit fields used during record
           creation. It assigns the current user as both creator and last writer, and
           sets the creation and last write timestamps to the current datetime.
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return {
            'create_uid': self.env.uid,
            'write_uid': self.env.uid,
            'create_date': current_time,
            'write_date': current_time
        }

    @api.model
    def copy_import(self, res_id, model, columns):
        """
            Performs an advanced import of Excel data into the specified model, handling
            complex field structures such as many2one, many2many, and one2many
            relationships. The method validates columns, prepares defaults, maps
            relational fields, resolves references, processes O2M grouping, fills
            required fields dynamically, and finally executes an optimized PostgreSQL
            bulk import. It also manages trigger creation/removal and ensures proper
            audit and state values, raising detailed errors when import validation or
            processing fails.
        """
        try:
            reference_cache = {}
            validation_result = self.validate_columns(res_id, model, columns)
            if not validation_result.get('is_valid', False):
                raise UserError(validation_result.get('error_message', 'Validation failed'))
            required_fields_info = self.get_required_fields(model)
            required_field_names = [f['name'] for f in required_fields_info]
            model_fields = self.env[model].fields_get()
            for field_name, field_info in model_fields.items():
                if field_info['type'] == 'one2many':
                    _logger.info(f"O2M Field: {field_name} -> {field_info['relation']}")
            column_mapping, imported_fields, o2m_field_mappings = {}, set(), {}
            for item in columns:
                if 'fieldInfo' not in item:
                    continue
                field_path = item['fieldInfo'].get('fieldPath', item['fieldInfo']['id'])
                field_name = item['fieldInfo']['id']
                excel_column_name = item.get('name', field_name)
                _logger.info(f"Processing field: {field_path} -> {field_name} (Excel: {excel_column_name})")
                if '/' in field_path:
                    path_parts = field_path.split('/')
                    parent_field_raw = path_parts[0]
                    child_field_raw = '/'.join(path_parts[1:])
                    parent_field = parent_field_raw
                    if parent_field not in model_fields:
                        _logger.warning(
                            f"Parent field '{parent_field}' not found, attempting to find a one2many field dynamically...")
                        o2m_fields = [f for f, info in model_fields.items() if info['type'] == 'one2many']
                        if o2m_fields:
                            parent_field = o2m_fields[0]
                            _logger.info(f"Using first O2M field for {model}: {parent_field}")
                        else:
                            continue
                    field_info = model_fields[parent_field]
                    if field_info['type'] != 'one2many':
                        _logger.error(f"Field '{parent_field}' is not a one2many field")
                        continue
                    comodel_name = field_info['relation']
                    _logger.info(f"Found O2M field: {parent_field} -> {comodel_name}")
                    try:
                        comodel_fields = self.env[comodel_name].fields_get()
                        child_field = child_field_raw
                        if child_field not in comodel_fields:
                            simplified = child_field.replace(' ', '_').lower()
                            candidates = [f for f in comodel_fields if
                                          f.lower() == simplified or simplified in f.lower()]
                            if candidates:
                                child_field = candidates[0]
                        o2m_field_mappings.setdefault(parent_field, []).append({
                            'excel_column': excel_column_name,
                            'child_field': child_field,
                            'full_path': field_path,
                            'comodel_name': comodel_name
                        })
                        imported_fields.add(parent_field)
                        _logger.info(f"✅O2M Mapping: {parent_field} -> {child_field}")
                    except Exception as e:
                        _logger.error(f"Error processing child field: {e}")
                        continue
                else:
                    if field_name in model_fields:
                        column_mapping[excel_column_name] = field_name
                        imported_fields.add(field_name)
                        _logger.info(f"Regular field: {excel_column_name} -> {field_name}")
            import_record = self.env['base_import.import'].browse(res_id).file
            file_stream = BytesIO(import_record)
            data = pd.read_excel(file_stream, dtype=str)
            data = data.replace({pd.NA: None, '': None})
            data = data.rename(columns=column_mapping)
            Model = self.env[model]
            defaults = self._get_model_defaults(model)
            missing_without_fallback = self._check_missing_required_fields(model, imported_fields, defaults)
            if missing_without_fallback:
                data = self._handle_missing_required_fields(data, model, missing_without_fallback)
                updated_imported_fields = imported_fields.union(set(missing_without_fallback))
                still_missing = self._check_missing_required_fields(model, updated_imported_fields, defaults)
                if still_missing:
                    raise UserError(f"Missing required fields without defaults: {', '.join(still_missing)}")
            if not o2m_field_mappings:
                filled_rows = []
                for _, row in data.iterrows():
                    parent_dict = row.to_dict()
                    parent_dict = self._apply_parent_defaults(parent_dict, model)
                    filled_rows.append(parent_dict)
                data = pd.DataFrame(filled_rows)
            if o2m_field_mappings:
                processed_data = self._group_o2m_records(data, model, o2m_field_mappings, reference_cache)
                if processed_data is not None and len(processed_data) > 0:
                    data = processed_data
                    _logger.info(f"After O2M grouping: {len(data)} parent records with O2M data for model {model}")
                else:
                    _logger.warning("O2M grouping returned empty data, falling back to original processing")
            else:
                _logger.info("No O2M fields found, using standard processing")
            required_fields = [f['name'] for f in required_fields_info]
            missing_required = set(required_fields) - imported_fields
            table_name = self.env[model]._table
            m2m_columns, o2m_columns, m2m_trigger_val, o2m_trigger_val = [], [], {}, {}
            has_complex_fields = False
            # Process M2M fields
            for item in columns:
                if 'fieldInfo' in item and item["fieldInfo"].get("type") == "many2many":
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
                raise UserError(f"Model '{model}' does not exist.")
            initial_count = self.env[model].search_count([])
            # Process O2M fields
            for parent_field, field_mappings in o2m_field_mappings.items():
                parent_field_info = self.env[model]._fields.get(parent_field)
                if isinstance(parent_field_info, fields.One2many):
                    has_complex_fields = True
                    o2m_field_name = f'o2m__{parent_field}'
                    if o2m_field_name not in o2m_columns:
                        o2m_trigger_val[o2m_field_name] = {
                            "data_table": self.env[parent_field_info.comodel_name]._table,
                            "inverse_name": getattr(parent_field_info, 'inverse_name', None),
                            "comodel_name": parent_field_info.comodel_name
                        }
                        o2m_columns.append(o2m_field_name)
                        _logger.info(f"Setup O2M trigger config: {o2m_trigger_val[o2m_field_name]}")
                        self.env.cr.execute(
                            f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {o2m_field_name} jsonb;")
                        _logger.info(f"Added JSONB column {o2m_field_name} to {table_name}")
            if 'state' in model_fields and model_fields['state']['type'] == 'selection':
                state_default = self._get_dynamic_state_default(model, model_fields['state'])
                _logger.info(f"Setting state field default to: {state_default}")
                if 'state' not in data.columns:
                    data = data.copy()
                    data.loc[:, 'state'] = [state_default] * len(data)
                    imported_fields.add('state')
                else:
                    state_values = []
                    for val in data['state']:
                        if pd.isna(val) or str(val).strip() == '' or str(val).strip().lower() in ['none', 'null',
                                                                                                  'nan']:
                            state_values.append(state_default)
                        else:
                            state_values.append(str(val).strip())
                    data = data.copy()
                    data.loc[:, 'state'] = state_values
            date_fields = [f for f, info in model_fields.items() if info['type'] in ['date', 'datetime']]
            for date_field in date_fields:
                if date_field not in data.columns and date_field in required_field_names:
                    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    data = data.copy()
                    data.loc[:, date_field] = [current_datetime] * len(data)
                    imported_fields.add(date_field)
            for field in missing_required:
                if field not in data.columns and field in defaults:
                    data = data.copy()
                    data.loc[:, field] = [defaults[field]] * len(data)
            many2one_fields = {}
            for column in data.columns:
                if column in model_fields and model_fields[column]['type'] == 'many2one':
                    comodel = model_fields[column]['relation']
                    many2one_fields[column] = comodel
                    self._build_reference_cache(comodel, data[column], reference_cache)
            for column, comodel in many2one_fields.items():
                resolved_values = []
                for value in data[column]:
                    if pd.notna(value):
                        resolved_id = self._resolve_reference(comodel, value, reference_cache)
                        resolved_values.append(resolved_id)
                    else:
                        resolved_values.append(None)
                data = data.copy()
                data.loc[:, column] = resolved_values
            if ('partner_id' in data.columns and
                    any(f in model_fields for f in ['partner_invoice_id', 'partner_shipping_id'])):
                partner_ids = []
                for pid in data['partner_id']:
                    try:
                        if pd.notna(pid) and int(pid) not in partner_ids:
                            partner_ids.append(int(pid))
                    except Exception:
                        continue
                address_cache = {}
                if partner_ids:
                    partner_model = model_fields.get('partner_id', {}).get('relation', 'res.partner')
                    partners = self.env[partner_model].browse(partner_ids)
                    for partner in partners:
                        try:
                            addresses = partner.address_get(['invoice', 'delivery'])
                            address_cache[partner.id] = {
                                'invoice': addresses.get('invoice', partner.id),
                                'delivery': addresses.get('delivery', partner.id)
                            }
                        except Exception:
                            address_cache[partner.id] = {'invoice': partner.id, 'delivery': partner.id}
                if 'partner_invoice_id' in model_fields:
                    data = data.copy()
                    data.loc[:, 'partner_invoice_id'] = [
                        address_cache.get(int(pid), {}).get('invoice') if pd.notna(pid) else None
                        for pid in data['partner_id']
                    ]
                if 'partner_shipping_id' in model_fields:
                    data = data.copy()
                    data.loc[:, 'partner_shipping_id'] = [
                        address_cache.get(int(pid), {}).get('delivery') if pd.notna(pid) else None
                        for pid in data['partner_id']
                    ]
            fields_to_import = list(imported_fields.union(missing_required))
            available_fields = [f for f in fields_to_import if f in data.columns]
            for field in fields_to_import:
                if field not in available_fields and (field in defaults or field in data.columns):
                    if field in data.columns:
                        available_fields.append(field)
                    else:
                        data = data.copy()
                        data.loc[:, field] = defaults[field]
                        available_fields.append(field)
            for o2m_col in o2m_columns:
                if o2m_col not in available_fields:
                    available_fields.append(o2m_col)
            for m2m_col in m2m_columns:
                if m2m_col not in available_fields:
                    available_fields.append(m2m_col)
            for parent_field in o2m_field_mappings.keys():
                imported_fields.add(parent_field)
                if parent_field not in fields_to_import:
                    fields_to_import.append(parent_field)
            final_fields = [f for f in available_fields if (
                    f in model_fields or f == 'id' or f.startswith('o2m__') or f.startswith('m2m__')
            )]
            if not final_fields:
                raise UserError("No valid fields found for import")
            try:
                self.env.cr.execute("SAVEPOINT trigger_setup;")
                self.env.cr.execute(f"""
                    DROP TRIGGER IF EXISTS trg_process_m2m_mapping ON {table_name};
                    DROP TRIGGER IF EXISTS trg_process_o2m_mapping ON {table_name};
                """)
                self.env.cr.execute("RELEASE SAVEPOINT trigger_setup;")
                _logger.info("Dropped existing triggers successfully")
            except Exception as e:
                self.env.cr.execute("ROLLBACK TO SAVEPOINT trigger_setup;")
                self.env.cr.execute("RELEASE SAVEPOINT trigger_setup;")
                self.env.cr.warning(f"Failed to drop triggers (isolated): {e}. Continuing import...")
            # Use enhanced bulk import that handles both M2M and O2M
            result = self._postgres_bulk_import_enhanced(
                data, model, final_fields,
                m2m_trigger_val, o2m_trigger_val,
                m2m_columns, o2m_columns,
                table_name, model_fields,
                initial_count, model_record,
                has_complex_fields, reference_cache
            )
            return result
        except UserError:
            raise
        except Exception as e:
            _logger.error(f"Import failed with exception: {str(e)}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            raise UserError(f"Import failed: {str(e)}")

    def remove_m2m_temp_columns(self, table, m2m_columns):
        """
           Removes temporary many2many helper columns from the specified table and
           drops the related processing triggers. This cleanup is typically performed
           after bulk import operations to restore the table structure and avoid
           leaving behind intermediate metadata used during import.
        """
        for column in m2m_columns:
            self.env.cr.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column};")
        self.env.cr.execute(f"""
            DROP TRIGGER IF EXISTS trg_process_m2m_mapping ON {table};
            DROP TRIGGER IF EXISTS trg_process_o2m_mapping ON {table};
        """)

    def get_m2m_details(self, model_name, field_name):
        """
           Retrieves metadata for a many2many field, including the relation table and
           the linking column names. This information is used during bulk import to
           correctly populate the M2M intermediate table.
        """
        model = self.env[model_name]
        field = model._fields[field_name]
        return {
            'relation_table': field.relation,
            'column1': field.column1,
            'column2': field.column2
        }

    @api.model
    def validate_columns(self, res_id, model, columns):
        """
            Validates the imported column definitions before processing an Excel import.
            It checks for invalid or unmapped columns, ensures required fields are
            present, and performs special validation for models such as res.partner that
            require specific fields (e.g., name or complete_name). The method returns a
            structured result indicating whether validation succeeded or providing
            details about any missing or invalid columns.
        """
        try:
            uploaded_columns = [item['fieldInfo']['id'] for item in columns if 'fieldInfo' in item]
            if len(uploaded_columns) < len(columns):
                invalid_columns = [col.get('name', 'Unknown') for col in columns if 'fieldInfo' not in col]
                return {
                    'is_valid': False,
                    'invalid_columns': invalid_columns,
                    'error_type': 'invalid_columns'
                }
            # Special validation for res.partner model
            if model == 'res.partner':
                # Extract all field names that will be imported
                imported_field_names = set()
                for item in columns:
                    if 'fieldInfo' in item:
                        field_info = item['fieldInfo']
                        field_name = field_info['id']
                        # If it's a field path (contains '/'), get the first part
                        if '/' in field_name:
                            field_name = field_name.split('/')[0]
                        imported_field_names.add(field_name)
                # Check if neither 'name' nor 'complete_name' is present
                if 'name' not in imported_field_names and 'complete_name' not in imported_field_names:
                    return {
                        'is_valid': False,
                        'error_type': 'missing_required_fields',
                        'error_message': "For Contact/Partner import, either 'Name' or 'Complete Name' field is required. Please add at least one of these columns to your Excel file."
                    }
            missing_required = self._check_missing_required_fields_for_validation(model, columns)
            if missing_required:
                return {
                    'is_valid': False,
                    'missing_required_fields': missing_required,
                    'error_type': 'missing_required_fields',
                    'error_message': f"Required fields missing: {', '.join(missing_required)}. Please add these columns to your Excel file."
                }
            return {'is_valid': True}
        except Exception as e:
            _logger.error(f"Validation error for model {model}: {str(e)}")
            return {
                'is_valid': False,
                'error_type': 'validation_error',
                'error_message': f"Validation failed: {str(e)}"
            }

    def get_required_fields(self, model_name):
        """
            Returns a list of required, stored, and non-deprecated fields for the given
            model. Each returned item includes the field name and its type, allowing the
            importer to identify mandatory fields that must be provided or filled during
            data processing.
        """
        Model = self.env[model_name]
        model_fields = Model.fields_get()
        required_fields = []
        for field_name, field in model_fields.items():
            if field.get('required') and field.get('store') and not field.get('deprecated', False):
                required_fields.append({
                    'name': field_name,
                    'type': field['type']
                })
        return required_fields

    def _check_missing_required_fields_for_validation(self, model_name, columns):
        """
            Identifies required fields that are missing during the initial validation
            phase of an import. It determines which fields the user has mapped, checks
            the model's true required fields (excluding deprecated, auto-generated,
            audit, and defaulted fields), and ensures each required field is either
            provided in the uploaded columns or has a fallback value. Returns a list of
            required fields that cannot be automatically filled and must be added to the
            import file.
        """
        try:
            imported_fields = set()
            for item in columns:
                if 'fieldInfo' in item:
                    field_name = item['fieldInfo']['id']
                    if '/' in field_name:
                        field_name = field_name.split('/')[0]
                    imported_fields.add(field_name)
            Model = self.env[model_name]
            model_fields = Model.fields_get()
            # Get actual field objects for better property checking
            field_objects = Model._fields
            required_fields = []
            for field_name, field_info in model_fields.items():
                field_obj = field_objects.get(field_name)
                # Skip deprecated fields
                if field_info.get('deprecated', False):
                    continue
                # Check if field is really required
                is_required = field_info.get('required', False)
                # Skip if field has a default value in the model
                has_default = False
                if field_obj and hasattr(field_obj, 'default'):
                    if field_obj.default is not None:
                        has_default = True
                # Skip automatic/audit fields
                if field_name in ['create_date', 'write_date', 'create_uid', 'write_uid']:
                    continue
                # Skip alias_id specifically since it's not actually required for import
                if field_name in ['alias_id', 'resource_id']:
                    continue
                # Only add if truly required and not having a default
                if is_required and not has_default:
                    # Double-check that field is stored and not computed
                    if field_info.get('store', True) and not field_info.get('compute', False):
                        required_fields.append(field_name)
            defaults = Model.default_get(list(model_fields.keys()))
            odoo_defaults = {k: v for k, v in defaults.items() if v is not None}
            auto_generated_fields = self._get_auto_generated_fields(model_name , required_fields)
            missing_without_fallback = []
            for field in set(required_fields) - imported_fields:
                if field not in odoo_defaults and field not in auto_generated_fields:
                    missing_without_fallback.append(field)
            return missing_without_fallback
        except Exception as e:
            _logger.error(f"Error checking required fields for {model_name}: {str(e)}")
            return []

    def _get_auto_generated_fields(self, model_name, required_fields):
        """
            Determines which required fields of a model can be automatically generated
            during import. This includes computed fields, related fields, fields with
            default values, audit fields, and any fields that Odoo inherently populates
            on record creation. These fields do not need to be provided in the import
            file, and identifying them helps avoid false validation errors.
        """
        auto_generated_fields = set()
        try:
            model_obj = self.env[model_name]
            all_field_names = list(model_obj.fields_get().keys())
            defaults = model_obj.default_get(all_field_names)
            fields_with_defaults = {k for k, v in defaults.items() if v is not None}
            for field_name in required_fields:
                if field_name in model_obj._fields:
                    field_obj = model_obj._fields[field_name]
                    if hasattr(field_obj, 'compute') and field_obj.compute:
                        auto_generated_fields.add(field_name)
                    elif hasattr(field_obj, 'related') and field_obj.related:
                        auto_generated_fields.add(field_name)
                    elif hasattr(field_obj, 'default') and callable(field_obj.default):
                        auto_generated_fields.add(field_name)
                    elif field_name in fields_with_defaults:
                        auto_generated_fields.add(field_name)
                    elif field_name in ['create_date', 'write_date', 'create_uid', 'write_uid']:
                        auto_generated_fields.add(field_name)
                    elif self._field_has_automatic_value(model_name, field_name):
                        auto_generated_fields.add(field_name)
        except Exception as e:
            _logger.warning(f"Error detecting auto-generated fields for {model_name}: {e}")
        return auto_generated_fields

    def _field_has_automatic_value(self, model_name, field_name):
        """
            Checks whether a given field is automatically populated by Odoo during
            record creation. This includes fields with default methods, sequence-based
            name generation, or defaults provided through the model's context. The
            result helps determine whether a required field must be present in the
            import file or can be safely omitted.
        """
        try:
            model_obj = self.env[model_name]
            field_obj = model_obj._fields.get(field_name)
            if not field_obj:
                return False
            if hasattr(field_obj, 'default') and field_obj.default:
                return True
            if field_name == 'name' and self._get_sequence_for_model(model_name):
                return True
            context_defaults = model_obj.with_context({}).default_get([field_name])
            if field_name in context_defaults and context_defaults[field_name]:
                return True
            return False
        except Exception as e:
            _logger.warning(f"Error checking automatic value for {field_name}: {e}")
            return False

    def _handle_missing_required_fields(self, data, model_name, missing_required):
        """
            Fills required fields that were not provided in the import data by generating
            appropriate default values dynamically. For each missing required field, the
            method retrieves a model-specific fallback value and inserts it into the
            dataset, ensuring the import can proceed without errors. Returns the updated
            DataFrame with all necessary fields populated.
        """
        try:
            Model = self.env[model_name]
            for field_name in missing_required:
                if field_name not in data.columns:
                    field_value = self._get_dynamic_default_value(model_name, field_name, len(data))
                    if field_value is not None:
                        data = data.copy()
                        data.loc[:, field_name] = field_value
                        _logger.info(f"Dynamically set {field_name} for {model_name}")
            return data
        except Exception as e:
            _logger.warning(f"Error dynamically handling required fields: {e}")
            return data

    def _get_dynamic_default_value(self, model_name, field_name, record_count):
        """
           Generates a suitable default value for a required field that was not
           provided in the import file. The method checks Odoo's built-in defaults,
           field-level default methods, and falls back to intelligent type-based
           defaults for common field types (char, numeric, boolean, date, datetime,
           many2one, selection). The returned value is repeated for the number of
           records being imported. Returns None if no reasonable fallback can be
           determined.
        """
        try:
            Model = self.env[model_name]
            field_obj = Model._fields.get(field_name)
            if not field_obj:
                return None
            defaults = Model.default_get([field_name])
            if field_name in defaults and defaults[field_name] is not None:
                return [defaults[field_name]] * record_count
            if hasattr(field_obj, 'default') and callable(field_obj.default):
                default_val = field_obj.default(Model)
                if default_val is not None:
                    return [default_val] * record_count
            field_type = field_obj.type
            if field_type in ['char', 'text']:
                return [f"Auto-{field_name}"] * record_count
            elif field_type in ['integer', 'float', 'monetary']:
                return [0] * record_count
            elif field_type == 'boolean':
                return [False] * record_count
            elif field_type == 'date':
                return [datetime.now().strftime('%Y-%m-%d')] * record_count
            elif field_type == 'datetime':
                return [datetime.now().strftime('%Y-%m-%d %H:%M:%S')] * record_count
            elif field_type == 'many2one':
                comodel = field_obj.comodel_name
                if comodel:
                    default_record = self.env[comodel].search([], limit=1)
                    if default_record:
                        return [default_record.id] * record_count
            elif field_type == 'selection':
                if field_obj.selection:
                    selection_values = field_obj.selection
                    if callable(selection_values):
                        selection_values = selection_values(Model)
                    if selection_values and len(selection_values) > 0:
                        return [selection_values[0][0]] * record_count
            return None
        except Exception as e:
            _logger.warning(f"Error getting dynamic default for {field_name}: {e}")
            return None

    def _build_reference_cache(self, model, values, reference_cache):
        """
            Builds a lookup cache for resolving many2one references during import.
            It analyzes the provided column values, extracts valid IDs, searches for
            matching records by common identifier fields (such as default_code, barcode,
            name, code, or complete_name), and maps each recognized value to its
            corresponding record ID. This cache significantly speeds up reference
            resolution and avoids repeated database searches during bulk imports.
        """
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
            except:
                pass
        if id_values:
            records = Model.browse(id_values).exists()
            for record in records:
                reference_cache[cache_key][str(record.id)] = record.id
        search_candidates = []
        for candidate in ['default_code', 'barcode', 'name', 'code', 'reference', 'complete_name']:
            if candidate in Model._fields and Model._fields[candidate].store:
                search_candidates.append(candidate)
        if 'default_code' in search_candidates:
            codes = []
            for val in unique_values:
                if '[' in val and ']' in val:
                    try:
                        start = val.index('[') + 1
                        end = val.index(']')
                        codes.append(val[start:end])
                    except Exception:
                        pass
            if codes:
                records = Model.search([('default_code', 'in', codes)])
                for record in records:
                    if record.default_code:
                        reference_cache[cache_key][record.default_code] = record.id
                        for val in unique_values:
                            if f'[{record.default_code}]' in val:
                                reference_cache[cache_key][val] = record.id
        for field_name in search_candidates:
            try:
                records = Model.search([(field_name, 'in', unique_values)])
                for record in records:
                    field_value = getattr(record, field_name, None)
                    if field_value:
                        reference_cache[cache_key][str(field_value)] = record.id
                        for val in unique_values:
                            if str(field_value) in val:
                                reference_cache[cache_key][val] = record.id
            except Exception:
                continue

    def _resolve_reference(self, model, value, reference_cache):
        """
            Resolves a many2one reference value dynamically by checking multiple possible
            identifiers. It first looks up the value in the reference cache, then
            attempts ID-based lookup, XML ID resolution, and finally searches common
            textual identifier fields (such as name, code, or default_code). When a
            match is found, it is cached for future lookups. Returns the resolved record
            ID or None if no matching record can be identified.
        """
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
        except:
            pass
        try:
            return self.env.ref(str_val).id
        except Exception:
            pass
        searchable_fields = []
        model_fields = Model.fields_get()
        for field_name, info in model_fields.items():
            if (info.get('store') and info.get('type') in ['char', 'text'] and not info.get('deprecated', False)):
                searchable_fields.append(field_name)
        for field in ['name', 'code', 'reference', 'display_name', 'complete_name', 'default_code', 'barcode']:
            if field in model_fields and field not in searchable_fields:
                searchable_fields.append(field)
        for field_name in searchable_fields:
            try:
                record = Model.search([(field_name, '=ilike', str_val)], limit=1)
                if record:
                    if cache_key not in reference_cache:
                        reference_cache[cache_key] = {}
                    reference_cache[cache_key][str_val] = record.id
                    return record.id
            except Exception:
                continue
        _logger.warning(f"Could not resolve {model} reference: {str_val}")
        return None

    def _generate_bulk_sequences(self, sequence, count):
        """
            Generates a list of sequence values in bulk for the given sequence record.
            It supports both modern and legacy sequence methods (_next_do and _next),
            returning the requested number of sequence values. If no valid sequence is
            provided or the count is zero, an empty list is returned.
        """
        if not sequence or count <= 0:
            return []
        if hasattr(sequence, '_next_do'):
            return [sequence._next_do() for i in range(count)]
        else:
            return [sequence._next() for i in range(count)]

    def _check_missing_required_fields(self, model_name, imported_fields, defaults):
        """
           Determines which required fields of a model are still missing after initial
           import mapping and default assignment. It compares the model’s true required
           fields against the fields imported, filters out fields that have defaults or
           can be auto-generated by Odoo, and returns only those required fields that
           have no available fallback and must be explicitly provided in the import
           data.
        """
        Model = self.env[model_name]
        model_fields = Model.fields_get()
        required_fields = []
        for field_name, field_info in model_fields.items():
            if (field_info.get('required') and
                    field_info.get('store') and
                    not field_info.get('deprecated', False)):
                required_fields.append(field_name)
        missing_required = set(required_fields) - imported_fields
        auto_generated_fields = self._get_auto_generated_fields(model_name, list(missing_required))
        missing_without_fallback = []
        for field in missing_required:
            if field not in defaults and field not in auto_generated_fields:
                missing_without_fallback.append(field)
        return missing_without_fallback

    def _get_next_sequence_values(self, table_name, count):
        """
            Generates a list of new sequential IDs for direct PostgreSQL bulk inserts.
            It calculates the next available IDs based on the current maximum ID in the
            target table, adjusts the underlying sequence to prevent conflicts, and
            returns the reserved ID range. If sequence adjustment fails, it falls back
            to a simpler max-ID-based generation, raising an error only if both
            strategies fail.
        """
        try:
            self.env.cr.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
            max_id = self.env.cr.fetchone()[0]
            ids_to_use = list(range(max_id + 1, max_id + count + 1))
            sequence_name = f"{table_name}_id_seq"
            new_seq_val = max_id + count + 100
            self.env.cr.execute(f"SELECT setval('{sequence_name}', %s, false)", (new_seq_val,))
            return ids_to_use
        except Exception as e:
            _logger.error(f"Error generating sequence values for {table_name}: {e}")
            try:
                self.env.cr.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
                max_id = self.env.cr.fetchone()[0]
                return list(range(max_id + 1, max_id + count + 1))
            except Exception as fallback_error:
                _logger.error(f"Fallback ID generation failed: {fallback_error}")
                raise UserError(f"Unable to generate unique IDs: {str(e)}")

    def _sync_sequence_after_import(self, table_name):
        """
            Synchronizes the PostgreSQL sequence associated with a table's ID column
            after a bulk import. It updates the sequence to a value safely beyond the
            current maximum ID, preventing future insert conflicts. If the update
            fails, a fallback attempt resets the sequence directly above the maximum
            existing ID.
        """
        try:
            self.env.cr.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
            max_id = self.env.cr.fetchone()[0]
            sequence_name = f"{table_name}_id_seq"
            new_seq_val = max_id + 1000
            self.env.cr.execute(f"SELECT setval('{sequence_name}', %s)", (new_seq_val,))
        except Exception as e:
            _logger.error(f"Error syncing sequence for {table_name}: {e}")
            try:
                self.env.cr.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
                max_id = self.env.cr.fetchone()[0]
                sequence_name = f"{table_name}_id_seq"
                self.env.cr.execute(f"SELECT setval('{sequence_name}', %s)", (max_id + 1,))
            except Exception as fallback_error:
                _logger.error(f"Fallback sequence sync failed for {table_name}: {fallback_error}")

    def _handle_sql_constraints_for_child_records(self, comodel_name, row_data, reference_cache):
        """
           Inspects SQL-level NOT NULL constraints on child models and ensures the
           imported row data satisfies them. Missing fields required by SQL constraints
           are automatically filled using model defaults or intelligent type-based
           fallback values. This helps prevent database constraint violations during
           bulk creation of one2many child records.
        """
        try:
            ChildModel = self.env[comodel_name]
            if not hasattr(ChildModel, "_sql_constraints"):
                return row_data
            child_fields = ChildModel.fields_get()
            model_defaults = ChildModel.default_get(list(child_fields.keys()))
            for _, constraint_sql, _ in getattr(ChildModel, "_sql_constraints", []):
                required_fields = re.findall(r'"?([a-zA-Z0-9_]+)"?\s+is\s+not\s+null', constraint_sql.lower())
                for field in required_fields:
                    if field not in row_data:
                        field_type = child_fields[field]["type"]
                        if field in model_defaults and model_defaults[field] is not None:
                            row_data[field] = model_defaults[field]
                            continue
                        if field_type in ("char", "text"):
                            row_data[field] = f"Auto {field.replace('_', ' ').title()}"
                        elif field_type in ("integer", "float", "monetary"):
                            row_data[field] = 0.0
                        elif field_type == "boolean":
                            row_data[field] = False
                        elif field_type == "date":
                            row_data[field] = datetime.now().strftime("%Y-%m-%d")
                        elif field_type == "datetime":
                            row_data[field] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        elif field_type == "many2one":
                            rel_model = child_fields[field].get("relation")
                            if rel_model:
                                rec = self.env[rel_model].search([('company_id', '=', self.env.company.id)], limit=1)
                                if not rec:
                                    rec = self.env[rel_model].search([], limit=1)
                                if rec:
                                    row_data[field] = rec.id
            return row_data
        except Exception as e:
            _logger.warning(f"Dynamic constraint handling failed for {comodel_name}: {e}")
            return row_data

    def _group_o2m_records(self, data, model_name, o2m_field_mappings, reference_cache):
        """
           Groups rows of imported data into parent–child structures for one2many
           fields. It detects a parent identifier, groups corresponding rows, extracts
           child field values, resolves many2one references, applies defaults, and
           assembles a clean parent dataset where each parent row contains a JSON-like
           list of child dictionaries. This function enables accurate reconstruction of
           hierarchical data during bulk imports.
        """
        if data is None or len(data) == 0:
            _logger.warning(f"No data received for grouping in model {model_name}")
            return pd.DataFrame()
        Model = self.env[model_name]
        model_fields = Model.fields_get()
        cleaned_o2m_field_mappings = {}
        parent_field_infos = {}
        for parent_field, field_mappings in o2m_field_mappings.items():
            field_info = Model._fields.get(parent_field)
            if field_info and getattr(field_info, "type", None) == "one2many":
                cleaned_o2m_field_mappings[parent_field] = field_mappings
                parent_field_infos[parent_field] = field_info
                _logger.info(f"O2M field kept for grouping: {parent_field} -> {field_info.comodel_name}")
            else:
                _logger.warning(f"Skipping '{parent_field}' in O2M mapping: not a one2many on model {model_name}")
        if not cleaned_o2m_field_mappings:
            _logger.info("No valid O2M mappings after cleanup; skipping grouping.")
            return data
        o2m_field_mappings = cleaned_o2m_field_mappings
        identifier_fields = ["name", "reference", "code", "number"]
        parent_id_series = pd.Series([None] * len(data), index=data.index, dtype=object)
        for field in identifier_fields:
            if field in data.columns:
                col = data[field]
                mask = col.notna() & (col.astype(str).str.strip() != "")
                set_mask = mask & parent_id_series.isna()
                if set_mask.any():
                    parent_id_series.loc[set_mask] = col.astype(str).str.strip().loc[set_mask]
                    _logger.info(f"Using field '{field}' as parent identifier for some rows")
        parent_id_series = parent_id_series.ffill()
        if parent_id_series.isna().all():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            synth = f"{model_name}_{timestamp}_0"
            parent_id_series[:] = synth
            _logger.info(f"No identifier fields found or all empty; using synthetic parent id '{synth}' for all rows")
        elif parent_id_series.isna().any():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            synth = f"{model_name}_{timestamp}_0"
            parent_id_series = parent_id_series.fillna(synth)
            _logger.info(f"Some rows had no identifier; filled them with synthetic parent id '{synth}'")
        for parent_field, field_mappings in o2m_field_mappings.items():
            field_info = parent_field_infos[parent_field]
            comodel_name = field_info.comodel_name
            all_values = []
            for mapping in field_mappings:
                excel_col = mapping["excel_column"]
                if excel_col in data.columns:
                    col_vals = data[excel_col].dropna().astype(str)
                    col_vals = col_vals[col_vals.str.strip() != ""]
                    if not col_vals.empty:
                        all_values.extend(col_vals.unique().tolist())
            if all_values:
                _logger.info(
                    f"Pre-building reference cache for O2M comodel {comodel_name} ({len(all_values)} potential values)")
                try:
                    self._build_reference_cache(comodel_name, all_values, reference_cache)
                except Exception as e:
                    _logger.warning(f"Failed pre-building reference cache for {comodel_name}: {e}")
        grouped = data.groupby(parent_id_series, sort=False, dropna=False)
        parent_data_list = []
        o2m_data_mapping = {parent_field: [] for parent_field in o2m_field_mappings.keys()}
        current_parent_data = {}
        non_o2m_cols = [c for c in data.columns if not c.startswith("o2m__")]
        default_context = self._get_common_default_context(model_name)
        for parent_identifier, group_df in grouped:
            if group_df.empty:
                continue
            first_row = group_df.iloc[0]
            parent_data = {}
            for col in non_o2m_cols:
                if col not in group_df.columns:
                    continue
                val = first_row.get(col, None)
                if pd.notna(val) and str(val).strip():
                    parent_data[col] = val
                    current_parent_data[col] = val
                elif col in current_parent_data and current_parent_data[col]:
                    parent_data[col] = current_parent_data[col]
            if not parent_data.get("name"):
                parent_data["name"] = parent_identifier
                current_parent_data["name"] = parent_identifier
            parent_data = self._apply_parent_defaults(parent_data, model_name)
            parent_data_list.append(parent_data)
            group_columns = list(group_df.columns)
            col_pos = {name: idx for idx, name in enumerate(group_columns)}
            for parent_field, field_mappings in o2m_field_mappings.items():
                field_info = parent_field_infos.get(parent_field)
                if not field_info:
                    o2m_data_mapping[parent_field].append([])
                    continue
                comodel_name = field_info.comodel_name
                inverse_name = getattr(field_info, "inverse_name", None)
                excel_cols = [
                    m["excel_column"]
                    for m in field_mappings
                    if m["excel_column"] in group_df.columns
                ]
                if not excel_cols:
                    o2m_data_mapping[parent_field].append([])
                    continue
                sub = group_df[excel_cols]
                non_empty = sub.notna() & (sub.astype(str).apply(lambda s: s.str.strip() != ""))
                row_mask = non_empty.any(axis=1)
                if not row_mask.any():
                    o2m_data_mapping[parent_field].append([])
                    continue
                child_chunk = group_df.loc[row_mask, :]
                child_records = []
                for row_tuple in child_chunk.itertuples(index=False, name=None):
                    child_record = {}
                    has_child_data = False
                    for mapping in field_mappings:
                        excel_col = mapping["excel_column"]
                        child_field = mapping["child_field"]
                        pos = col_pos.get(excel_col)
                        if pos is None:
                            continue
                        cell_value = row_tuple[pos]
                        if pd.isna(cell_value) or str(cell_value).strip() == "":
                            continue
                        processed_value = self._process_child_field_value(child_field, cell_value, comodel_name,
                                                                          reference_cache)
                        if processed_value is not None:
                            child_record[child_field] = processed_value
                            has_child_data = True
                    if has_child_data:
                        child_record = self._apply_child_defaults(child_record, comodel_name, reference_cache,
                                                                  default_context=default_context)
                        if inverse_name and inverse_name in child_record:
                            del child_record[inverse_name]
                        child_records.append(child_record)
                o2m_data_mapping[parent_field].append(child_records)
        if not parent_data_list:
            _logger.warning(f"No parent data found after grouping for {model_name}")
            return pd.DataFrame()
        result_df = pd.DataFrame(parent_data_list)
        for parent_field in o2m_field_mappings.keys():
            o2m_column_name = f"o2m__{parent_field}"
            if parent_field in o2m_data_mapping:
                result_df.loc[:, o2m_column_name] = o2m_data_mapping[parent_field]
        return result_df

    def _process_child_field_value(self, child_field, cell_value, comodel_name, reference_cache):
        """
            Processes and converts a raw Excel cell value into a valid value for a
            child (one2many) field. It handles many2one fields by resolving references,
            numeric fields by safely converting to floats, and fallback text fields by
            cleaning string values. Missing or invalid data is normalized to safe
            defaults to ensure child record creation does not fail.
        """
        try:
            comodel = self.env[comodel_name]
            child_field_obj = comodel._fields.get(child_field)
            if child_field.endswith('_id') or (
                    child_field_obj and getattr(child_field_obj, 'type', None) == 'many2one'):
                field_model = None
                if child_field_obj and getattr(child_field_obj, 'comodel_name', None):
                    field_model = child_field_obj.comodel_name
                else:
                    field_model = child_field.replace('_id', '').replace('_', '.')
                resolved_id = self._resolve_reference(field_model, cell_value, reference_cache)
                return resolved_id
            numeric_field_names = ['qty', 'quantity', 'product_qty', 'price_unit', 'amount', 'purchase_price',
                                   'cost_price', 'product_uom_qty']
            if child_field in numeric_field_names:
                try:
                    if pd.isna(cell_value) or cell_value in ['', None, 'nan', 'None']:
                        return 0.0
                    return float(cell_value)
                except (ValueError, TypeError):
                    return 0.0
            if pd.isna(cell_value) or cell_value in ['', None, 'nan', 'None']:
                return ""
            return str(cell_value).strip()
        except Exception as e:
            _logger.warning(f"Error processing child field {child_field}: {e}")
            if child_field in ['product_qty', 'price_unit', 'quantity', 'qty']:
                return 0.0
            else:
                return ""

    def _apply_child_defaults(self, child_record, comodel_name, reference_cache, default_context=None):
        """
           Applies default values and normalization rules to a one2many child record
           during import. This method ensures every required field is populated using
           model defaults, dynamic fallbacks, product-based UoM assignment, and
           context-driven values. It also interprets special line types (sections and
           notes), cleans invalid values, assigns proper display_type logic, and
           resolves many2one fields when possible. SQL constraint-based defaults are
           applied at the end to guarantee child records are valid before creation.
        """
        try:
            ChildModel = self.env[comodel_name]
            child_fields = ChildModel.fields_get()
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if default_context:
                for field, value in default_context.items():
                    if field in child_fields and not child_record.get(field):
                        child_record[field] = value
            model_defaults = ChildModel.default_get(list(child_fields.keys()))
            for field, val in model_defaults.items():
                if field in child_fields and field not in child_record and val is not None:
                    child_record[field] = val
            for candidate in ['product_id']:
                if candidate in child_fields and not child_record.get(candidate):
                    field_obj = ChildModel._fields.get(candidate)
                    if field_obj and getattr(field_obj, 'comodel_name', None):
                        try:
                            rec = self.env[field_obj.comodel_name].search([], limit=1)
                            if rec:
                                child_record[candidate] = rec.id
                        except Exception:
                            pass
            uom_fields = [f for f, finfo in child_fields.items() if
                          finfo.get('type') == 'many2one' and finfo.get('relation') == 'uom.uom']
            for uom_field in uom_fields:
                if uom_field not in child_record:
                    if 'product_id' in child_record and child_record['product_id']:
                        try:
                            product = self.env['product.product'].browse(child_record['product_id'])
                            if product.exists() and getattr(product, 'uom_id', False):
                                child_record[uom_field] = product.uom_id.id
                        except Exception:
                            pass
                    if uom_field not in child_record:
                        try:
                            uom = self.env['uom.uom'].search([], limit=1)
                            if uom:
                                child_record[uom_field] = uom.id
                        except Exception:
                            pass
            if 'date_planned' in child_fields and not child_record.get('date_planned'):
                child_record['date_planned'] = now_str
            for field, finfo in child_fields.items():
                if finfo.get('required') and field not in child_record:
                    ftype = finfo['type']
                    if ftype in ['integer', 'float', 'monetary']:
                        child_record[field] = 0.0
                    elif ftype in ['char', 'text']:
                        child_record[field] = f"Auto {field.replace('_', ' ').title()}"
                    elif ftype in ['date', 'datetime']:
                        child_record[field] = now_str
                    elif ftype == 'many2one':
                        rel_model = finfo.get('relation')
                        if rel_model:
                            record = self.env[rel_model].search([], limit=1)
                            if record:
                                child_record[field] = record.id
            if 'name' in child_record and isinstance(child_record['name'], str):
                lower_name = child_record['name'].strip().lower()
                if lower_name.startswith('note:'):
                    child_record['display_type'] = 'line_note'
                elif lower_name.startswith('section:'):
                    child_record['display_type'] = 'line_section'
            if 'display_type' in child_record:
                display_type = child_record['display_type']
                if isinstance(display_type, bool) or isinstance(display_type, (int, float)):
                    display_type = None
                elif isinstance(display_type, str):
                    display_type = display_type.strip().lower()
                    if display_type in ('line_section', 'section'):
                        display_type = 'line_section'
                    elif display_type in ('line_note', 'note'):
                        display_type = 'line_note'
                    else:
                        display_type = 'product'
                else:
                    display_type = 'product'
                child_record['display_type'] = display_type
                if display_type in ('line_section', 'line_note'):
                    for f in ['product_id', 'product_uom', 'product_qty', 'price_unit', 'date_planned']:
                        if f in child_record:
                            child_record[f] = None
            else:
                child_record['display_type'] = 'product'
            child_record = self._handle_sql_constraints_for_child_records(comodel_name, child_record, reference_cache)
            return child_record
        except Exception as e:
            _logger.error(f"Error applying child defaults for {comodel_name}: {e}")
            import traceback
            _logger.error(traceback.format_exc())
            return child_record

    def _apply_parent_defaults(self, parent_record, model_name):
        """
            Applies default and contextual values to a parent record before import.
            It fills essential fields such as state, dates, company, and currency when
            missing, merges defaults from the model’s computed context, and ensures
            critical many2one fields like company_id are populated. The method prepares
            the parent record to be structurally complete and ready for database
            insertion without altering values explicitly provided by the user.
        """
        try:
            Model = self.env[model_name]
            model_fields = Model.fields_get()
            defaults = {
                'state': 'draft',
                'date_order': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'company_id': self.env.company.id,
                'currency_id': getattr(self.env.company, 'currency_id',
                                       False) and self.env.company.currency_id.id or None,
            }
            for field, default_value in defaults.items():
                if field in model_fields and (field not in parent_record or not parent_record[field]):
                    parent_record[field] = default_value
            context_defaults = self._get_common_default_context(model_name)
            for field, value in context_defaults.items():
                if field in model_fields and not parent_record.get(field) and value:
                    parent_record[field] = value
            for field_name, field_info in model_fields.items():
                if field_info['type'] == 'many2one' and field_name not in parent_record:
                    # Leave it empty - will be NULL in database
                    # Or only set if it's a truly required field with a logical default
                    if field_name in ['company_id']:  # Only for essential fields
                        parent_record[field_name] = self.env.company.id
        except Exception as e:
            _logger.warning(f"Error applying parent defaults for {model_name}: {e}")
        return parent_record

    def _postgres_bulk_import_enhanced(self, data, model, final_fields, m2m_trigger_val, o2m_trigger_val,
                                       m2m_columns, o2m_columns, table_name, model_fields,
                                       initial_count, model_record, has_complex_fields, reference_cache):
        """
            Performs a high-performance PostgreSQL bulk import that supports complex
            Odoo models, including many2many (M2M) and one2many (O2M) relationships.
            The method prepares data for direct SQL insertion, validates table columns,
            applies sequences, audit fields, default values, and handles translation
            fields. Regular fields are imported using optimized INSERT operations, while
            O2M values are stored as JSON and later expanded into actual child records.
            M2M relationships are processed after inserting the parent rows, creating
            link-table entries while resolving references dynamically.

            The method isolates each row insert using savepoints to ensure partial
            recovery, logs failures, updates sequences, cleans up temporary columns, and
            returns a structured summary of import counts and warnings.
        """
        try:
            env = self.env
            Model = env[model]
            odoo_fields = getattr(Model, "_fields", {}) or model_fields or {}

            if not table_name:
                table_name = Model._table
            # First, verify the table structure
            env.cr.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                ORDER BY ordinal_position
            """)
            existing_columns = [row[0] for row in env.cr.fetchall()]
            # Clean regular_final_fields to only include existing columns
            cleaned_regular_fields = []
            for field in final_fields:
                # Remove m2m and o2m prefixes for checking
                clean_field = field.replace('m2m__', '').replace('o2m__', '')
                if field in existing_columns or clean_field in odoo_fields:
                    cleaned_regular_fields.append(field)
            # Separate M2M fields from regular fields
            original_data = data.copy()
            regular_final_fields = []
            m2m_field_mapping = {}
            for column in data.columns:
                if column.startswith("m2m__"):
                    real_field_name = column.replace("m2m__", "", 1)
                    m2m_field_mapping[real_field_name] = original_data[column].copy()
                elif column in m2m_columns:
                    real_field_name = column.replace("m2m__", "", 1) if column.startswith("m2m__") else column
                    m2m_field_mapping[real_field_name] = original_data[column].copy()
                else:
                    field_obj = odoo_fields.get(column)
                    if field_obj:
                        field_type = getattr(field_obj, "type", None)
                        if field_type == 'many2many':
                            m2m_field_mapping[column] = original_data[column].copy()
                        elif column in existing_columns:  # Check if column exists in table
                            regular_final_fields.append(column)
                    elif column in existing_columns:  # Check if column exists in table
                        regular_final_fields.append(column)
            # Clean fields - remove computed fields that are not stored
            model_fields = self.env[model]._fields
            clean_fields = []
            for f in regular_final_fields:
                field = model_fields.get(f)
                if not field:
                    # If not a model field, check if it exists in table
                    if f in existing_columns:
                        clean_fields.append(f)
                    continue
                if getattr(field, 'compute', False) and not field.store and not field.required:
                    continue
                if f in existing_columns:  # Only add if column exists
                    clean_fields.append(f)
            regular_final_fields = clean_fields
            # Add O2M fields to regular fields for processing
            for o2m_col in o2m_columns:
                if o2m_col not in regular_final_fields and o2m_col in data.columns and o2m_col in existing_columns:
                    regular_final_fields.append(o2m_col)
            if not regular_final_fields:
                _logger.warning("No regular fields detected to insert; aborting bulk import.")
                return {
                    "name": model_record.name,
                    "record_count": 0,
                    "duration": 0.0,
                    "warnings": "No regular fields detected for main insert.",
                }
            # Only keep columns that exist in the table
            available_columns = [col for col in regular_final_fields if col in existing_columns]
            insert_data = data[available_columns].copy()
            # Handle sequence for name field
            if 'name' in model_fields:
                sequence = self._get_sequence_for_model(model)
                needs_sequence = False
                name_in_data = 'name' in insert_data.columns
                if not name_in_data:
                    needs_sequence = True
                else:
                    non_null_names = insert_data['name'].dropna()
                    if len(non_null_names) == 0:
                        needs_sequence = True
                    else:
                        name_check_results = []
                        for val in non_null_names:
                            str_val = str(val).strip().lower()
                            name_check_results.append(str_val in ['new', '', 'false'])
                        needs_sequence = all(name_check_results)
                if sequence and needs_sequence:
                    record_count = len(insert_data)
                    if record_count > 0:
                        try:
                            sequence_values = self._generate_bulk_sequences(sequence, record_count)
                            insert_data = insert_data.copy()
                            insert_data.loc[:, 'name'] = sequence_values
                            if 'name' not in available_columns:
                                available_columns.append('name')
                        except Exception as e:
                            _logger.error(f"Failed to generate sequences: {e}")
            # Add audit fields - only if they exist in the table
            audit_values = self._prepare_audit_fields()
            if 'active' in model_fields and 'active' not in available_columns and 'active' in existing_columns:
                insert_data['active'] = [True] * len(insert_data)
                available_columns.append('active')
            for audit_field, value in audit_values.items():
                field_obj = odoo_fields.get(audit_field)
                if not field_obj:
                    continue
                if not getattr(field_obj, "store", False):
                    continue
                if getattr(field_obj, "compute", False):
                    continue
                if getattr(field_obj, "related", False):
                    continue
                if audit_field not in existing_columns:
                    continue  # Skip if column doesn't exist in table
                if audit_field not in insert_data.columns:
                    insert_data[audit_field] = value
                if audit_field not in available_columns:
                    available_columns.append(audit_field)
            # Generate IDs if needed
            if 'id' not in available_columns and 'id' in existing_columns:
                record_count = len(insert_data)
                if record_count > 0:
                    try:
                        next_ids = self._get_next_sequence_values(table_name, record_count)
                        insert_data = insert_data.copy()
                        insert_data.loc[:, 'id'] = next_ids
                        available_columns.insert(0, 'id')
                    except Exception as e:
                        if 'id' in available_columns:
                            available_columns.remove('id')
                        if 'id' in insert_data.columns:
                            insert_data = insert_data.drop(columns=['id'])
            # Process O2M JSON fields
            for o2m_col in o2m_columns:
                if o2m_col in insert_data.columns and o2m_col in existing_columns:
                    json_values = []
                    for val in insert_data[o2m_col]:
                        if isinstance(val, list):
                            json_values.append(json.dumps(val, ensure_ascii=False))
                        else:
                            json_values.append(val)
                    insert_data = insert_data.copy()
                    insert_data.loc[:, o2m_col] = json_values
            # Insert records using COPY for better performance
            inserted_count = 0
            failed_records = []
            inserted_row_ids = {}
            # Final check: ensure all columns exist in table
            final_insert_columns = [col for col in available_columns if col in existing_columns]
            columns_str = ",".join(f'"{col}"' for col in final_insert_columns)
            placeholders = ",".join(["%s"] * len(final_insert_columns))
            insert_sql = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders}) RETURNING id'
            for row_index, row in insert_data.iterrows():
                savepoint_name = f"import_record_{row_index}".replace('-', '_')
                try:
                    env.cr.execute(f"SAVEPOINT {savepoint_name}")
                    values = []
                    for field_name in final_insert_columns:
                        raw_value = row.get(field_name, None)
                        field_obj = odoo_fields.get(field_name)
                        if field_obj and getattr(field_obj, "translate", False):
                            default_lang = env.context.get('lang', 'en_US')
                            if pd.isna(raw_value) or raw_value in (None, '', 'nan', 'None'):
                                values.append(None)
                            else:
                                values.append(json.dumps({default_lang: str(raw_value)}))
                            continue
                        if pd.isna(raw_value):
                            values.append(None)
                            continue
                        if field_obj is None:
                            values.append(raw_value)
                            continue
                        ftype = getattr(field_obj, "type", None)
                        try:
                            if ftype in ("char", "text", "html", "selection"):
                                values.append(str(raw_value))
                            elif ftype == "many2one":
                                if pd.isna(raw_value) or raw_value in (None, '', 'nan', 'None'):
                                    values.append(None)
                                else:
                                    comodel = field_obj.comodel_name
                                    if str(raw_value).isdigit():
                                        values.append(int(raw_value))
                                    else:
                                        record = env[comodel].search([('name', '=', str(raw_value).strip())], limit=1)
                                        if record:
                                            values.append(record.id)
                                        else:
                                            new_rec = env[comodel].create({'name': raw_value})
                                            values.append(new_rec.id)
                            elif ftype in ("float", "monetary"):
                                values.append(float(raw_value))
                            elif ftype == "boolean":
                                if pd.isna(raw_value):
                                    values.append(None)
                                else:
                                    v = str(raw_value).strip().lower()
                                    values.append(v in ("1", "true", "yes", "y", "t"))
                            elif ftype in ("date", "datetime"):
                                try:
                                    parsed = pd.to_datetime(raw_value, errors='coerce')
                                    values.append(parsed.strftime('%Y-%m-%d %H:%M:%S') if parsed else None)
                                except:
                                    values.append(None)
                            else:
                                values.append(raw_value)
                        except Exception as conv_err:
                            values.append(raw_value)
                    values_tuple = tuple(values)
                    _logger.info(f"Inserting record index {row_index} into {table_name}")
                    env.cr.execute(insert_sql, values_tuple)
                    result = env.cr.fetchone()
                    if result:
                        new_id = result[0]
                        inserted_row_ids[row_index] = new_id
                        inserted_count += 1
                        env.cr.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                    else:
                        env.cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                        failed_records.append((row_index, "No ID returned after INSERT"))
                except Exception as row_error:
                    env.cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                    failed_records.append((row_index, str(row_error)))
            env.cr.commit()
            # Initialize counters for relationships
            m2m_processed = 0
            m2m_failed = 0
            o2m_processed = 0
            o2m_failed = 0
            # Process M2M relationships
            if m2m_field_mapping and inserted_row_ids:
                for row_index, record_id in inserted_row_ids.items():
                    for m2m_field_name, series in m2m_field_mapping.items():
                        if row_index not in series.index:
                            continue
                        m2m_values = series.loc[row_index]
                        if pd.isna(m2m_values) or m2m_values in ("", "nan", "None", None):
                            continue
                        field_obj = odoo_fields.get(m2m_field_name)
                        if not field_obj or getattr(field_obj, "type", None) != "many2many":
                            continue
                        relation_table = field_obj.relation
                        column1 = field_obj.column1
                        column2 = field_obj.column2
                        comodel_name = field_obj.comodel_name
                        # Parse the M2M values
                        if isinstance(m2m_values, str):
                            tokens = []
                            for token in m2m_values.replace(";", ",").split(","):
                                token = token.strip()
                                if token:
                                    tokens.append(token)
                        else:
                            tokens = [str(m2m_values).strip()]
                        for token in tokens:
                            if not token:
                                continue
                            try:
                                safe_token = str(hash(token)).replace('-', '_')
                                savepoint_name = f"m2m_{record_id}_{m2m_field_name}_{safe_token}"
                                env.cr.execute(f"SAVEPOINT {savepoint_name}")
                                related_id = None
                                if token.isdigit():
                                    related_id = int(token)
                                    if env[comodel_name].browse(related_id).exists():
                                        _logger.info(f"Token '{token}' resolved as direct ID: {related_id}")
                                    else:
                                        _logger.warning(
                                            f"Token '{token}' is numeric but ID {related_id} doesn't exist in {comodel_name}")
                                        related_id = None
                                if not related_id:
                                    try:
                                        related_id = env.ref(token).id
                                    except ValueError:
                                        pass
                                if not related_id:
                                    comodel_fields = env[comodel_name].fields_get()
                                    if 'name' in comodel_fields and comodel_fields['name'].get('store'):
                                        related_rec = env[comodel_name].search([("name", "=ilike", token)], limit=1)
                                        if related_rec:
                                            related_id = related_rec.id
                                if not related_id and 'code' in env[comodel_name]._fields:
                                    code_field = env[comodel_name]._fields['code']
                                    if getattr(code_field, 'store', False):
                                        related_rec = env[comodel_name].search([("code", "=ilike", token)], limit=1)
                                        if related_rec:
                                            related_id = related_rec.id
                                if not related_id:
                                    models_not_to_auto_create = ['res.groups', 'ir.model.fields', 'ir.model', 'ir.rule',
                                                                 'ir.ui.menu', 'ir.actions.actions',
                                                                 'ir.actions.server']
                                    if comodel_name not in models_not_to_auto_create:
                                        try:
                                            create_vals = {'name': token}
                                            new_rec = env[comodel_name].create(create_vals)
                                            related_id = new_rec.id
                                        except Exception as create_error:
                                            related_id = None
                                if not related_id:
                                    env.cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                                    m2m_failed += 1
                                    continue
                                # Check if relationship already exists
                                check_sql = f'''
                                    SELECT 1 FROM "{relation_table}" 
                                    WHERE "{column1}" = %s AND "{column2}" = %s
                                    LIMIT 1
                                '''
                                env.cr.execute(check_sql, (record_id, related_id))
                                exists = env.cr.fetchone()
                                if not exists:
                                    insert_m2m_sql = (
                                        f'INSERT INTO "{relation_table}" ("{column1}", "{column2}") '
                                        f"VALUES (%s, %s)"
                                    )
                                    env.cr.execute(insert_m2m_sql, (record_id, related_id))
                                    m2m_processed += 1
                                env.cr.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                            except Exception as m2m_error:
                                env.cr.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                                m2m_failed += 1
                env.cr.commit()
            # Process O2M relationships if any
            if o2m_columns and inserted_row_ids:
                for row_index, record_id in inserted_row_ids.items():
                    for o2m_col in o2m_columns:
                        if o2m_col not in insert_data.columns or row_index not in insert_data.index:
                            continue
                        o2m_data = insert_data.loc[row_index, o2m_col]
                        if pd.isna(o2m_data) or not o2m_data:
                            continue
                        try:
                            # Parse O2M JSON data
                            if isinstance(o2m_data, str):
                                child_records = json.loads(o2m_data)
                            else:
                                child_records = o2m_data
                            if not isinstance(child_records, list):
                                continue
                            real_field_name = o2m_col.replace("o2m__", "")
                            field_obj = odoo_fields.get(real_field_name)
                            if not field_obj or getattr(field_obj, "type", None) != "one2many":
                                continue
                            comodel_name = field_obj.comodel_name
                            inverse_name = getattr(field_obj, "inverse_name", None)
                            for child_data in child_records:
                                if not isinstance(child_data, dict):
                                    continue
                                try:
                                    # Set the inverse field to link to parent
                                    if inverse_name:
                                        child_data[inverse_name] = record_id
                                    # Create child record
                                    child_record = env[comodel_name].create(child_data)
                                    o2m_processed += 1
                                except Exception as child_error:
                                    o2m_failed += 1
                                    _logger.warning(f"Failed to create O2M child record: {child_error}")
                        except Exception as o2m_error:
                            o2m_failed += 1
                            _logger.warning(f"Failed to process O2M data: {o2m_error}")
                env.cr.commit()
            # Final count and cleanup
            try:
                env.cr.commit()
                with env.registry.cursor() as new_cr:
                    new_cr.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                    final_count = new_cr.fetchone()[0]
                actual_imported_count = inserted_count
            except Exception as count_error:
                actual_imported_count = inserted_count
                final_count = initial_count + inserted_count
            imported_count = actual_imported_count
            # Clean up temporary columns
            try:
                self.remove_m2m_temp_columns(table_name, m2m_columns + o2m_columns)
            except Exception as cleanup_error:
                _logger.warning(f"Failed to clean up temporary columns: {cleanup_error}")
            warnings = None
            if failed_records:
                warnings = f"Failed to import {len(failed_records)} records."
            if m2m_failed > 0:
                warnings = f"{warnings} {m2m_failed} M2M relationships failed." if warnings else f"{m2m_failed} M2M relationships failed."
            if o2m_failed > 0:
                warnings = f"{warnings} {o2m_failed} O2M relationships failed." if warnings else f"{o2m_failed} O2M relationships failed."
            return {
                "name": model_record.name,
                "record_count": imported_count,
                "duration": 0.1,
                "warnings": warnings,
            }
        except Exception as e:
            self.env.cr.rollback()
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
            elif field['type'] == 'one2many':
                field_value['fields'] = self.get_fields_tree(field['relation'], depth=depth - 1)
                if self.user_has_groups('base.group_no_one'):
                    field_value['fields'].append(
                        {'id': '.id', 'name': '.id', 'string': _("Database ID"),
                         'required': False, 'fields': [], 'type': 'id'})
                field_value['comodel_name'] = field['relation']
            importable_fields.append(field_value)
        return importable_fields