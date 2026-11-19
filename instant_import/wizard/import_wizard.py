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
import logging
import time

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.base_import.models.base_import import LANGUAGE_SEPARATOR

_logger = logging.getLogger(__name__)

# Options used when the client sends none (e.g. an RPC call or a test).
DEFAULT_OPTIONS = {
    'quoting': '"',
    'separator': '',
    'encoding': '',
    'has_headers': True,
    'date_format': '',
    'datetime_format': '',
    'float_thousand_separator': ',',
    'float_decimal_separator': '.',
    'sheet': '',
    'import_skip_records': [],
    'import_set_empty_fields': [],
    'fallback_values': {},
    'name_create_enabled_fields': {},
}
# Activity column values mapped to the names of the default activity types.
ACTIVITY_TYPE_ALIASES = {
    'todo': 'To-Do',
    'to do': 'To-Do',
    'to-do': 'To-Do',
}


class ImportWizard(models.TransientModel):
    _name = 'custom.import.wizard'
    _description = 'Custom Import Wizard'

    model_id = fields.Many2one('ir.model', required=True,
                               domain=[('transient', '=', False)])

    @api.model
    def copy_import(self, res_id, model, columns, options=None):
        """Import the uploaded file into ``model`` in one step.

        The rows go through ``base_import.import.execute_import``, i.e.
        ``Model.load()``: access rights, record rules, defaults, computed
        fields, constraints, sequences and external IDs are all handled by
        the ORM. Any error rolls the whole file back.

        :param int res_id: id of the ``base_import.import`` record holding the file
        :param str model: technical name of the target model
        :param list columns: the import columns as sent by the import screen
        :param dict options: the import options of the import screen
        :return: dict with ``record_count``, ``name`` and ``inserted_row_ids``
        """
        start_time = time.time()
        import_rec, field_paths, column_names, options = self._prepare_import(res_id, model, columns, options)
        validation = self.validate_columns(res_id, model, columns)
        if not validation.get('is_valid'):
            raise UserError(validation.get('error_message') or self.env._("Validation failed"))
        rows = self._read_rows(import_rec, options)
        for index, path in enumerate(field_paths):
            if path and self._record_key(model, path) == 'id':
                self._check_external_ids(row[index] for row in rows if index < len(row))
        activity_index = self._activity_column(columns)
        result = import_rec.execute_import(field_paths, column_names, options)
        self._raise_on_errors(result)
        record_ids = result.get('ids') or []
        if activity_index is not None and record_ids:
            self._create_activities(model, record_ids, field_paths, rows, activity_index)
        _logger.info("Instant Import: %d %s records imported in %.2f s",
                     len(record_ids), model, time.time() - start_time)
        return {
            'record_count': len(record_ids),
            'name': self.env[model]._description,
            'inserted_row_ids': record_ids,
        }

    @api.model
    def validate_columns(self, res_id, model, columns, options=None):
        """Check the column mapping, then dry-run the import to report errors.

        :return: dict with ``is_valid`` and, when invalid, ``error_message``
        """
        mapped = [item['fieldInfo'] for item in columns if item.get('fieldInfo')]
        if not mapped:
            return {
                'is_valid': False,
                'error_type': 'no_fields_mapped',
                'error_message': self.env._(
                    "No fields mapped for import. Please select a field for at least one column."),
            }
        imported = {self._field_path(info).split('/')[0] for info in mapped}
        missing = self._missing_required_fields(model, imported)
        if missing:
            return {
                'is_valid': False,
                'missing_required_fields': missing,
                'error_type': 'missing_required_fields',
                'error_message': self.env._(
                    "Required fields missing: %s. Please add these columns to your file.",
                    ', '.join(missing)),
            }
        if options is None:
            return {'is_valid': True}
        import_rec, field_paths, column_names, options = self._prepare_import(res_id, model, columns, options)
        result = import_rec.execute_import(field_paths, column_names, options, dryrun=True)
        errors = self._error_messages(result)
        if errors:
            return {'is_valid': False, 'error_type': 'import_error', 'error_message': '\n'.join(errors)}
        return {'is_valid': True}

    def _prepare_import(self, res_id, model, columns, options):
        """Return the import record, field paths, column names and options."""
        self.env[model].check_access('create')
        import_rec = self.env['base_import.import'].browse(int(res_id or 0)).exists()
        if not import_rec or not import_rec.file:
            raise UserError(self.env._("No import file found. Please upload a file first."))
        if import_rec.res_model != model:
            raise UserError(self.env._("The uploaded file was not prepared for this model."))
        field_paths = []
        for item in columns:
            info = item.get('fieldInfo')
            path = self._field_path(info) if info else False
            if path and self._record_key(model, path) == '.id':
                raise UserError(self.env._(
                    "Instant Import only creates records: database ID (.id) columns cannot be imported."))
            if path == 'activity_ids':
                path = False
            elif path and item.get('language'):
                path += LANGUAGE_SEPARATOR + item['language']
            field_paths.append(path)
        column_names = [(item.get('name') or '').strip().lower() for item in columns]
        import_options = dict(DEFAULT_OPTIONS, **(options or {}))
        # The whole file is imported at once.
        import_options.pop('limit', None)
        import_options['skip'] = 0
        return import_rec, field_paths, column_names, import_options

    def _record_key(self, model, path):
        """``'id'`` or ``'.id'`` when the column identifies the records ``load()`` writes.

        The external ID (``id``) or database ID (``.id``) of the imported
        record, or of a one2many line, selects the record to create or
        update; under a many2one or many2many it only links a record.
        """
        Model = self.env[model]
        for part in path.split('/'):
            if Model is None:
                return None
            if part in ('id', '.id'):
                return part
            field = Model._fields.get(part)
            Model = self.env[field.comodel_name] if field and field.type == 'one2many' else None
        return None

    @staticmethod
    def _field_path(info):
        return info.get('fieldPath') or info['id']

    @staticmethod
    def _activity_column(columns):
        for index, item in enumerate(columns):
            info = item.get('fieldInfo')
            if info and (info.get('fieldPath') or info.get('id')) == 'activity_ids':
                return index
        return None

    @staticmethod
    def _read_rows(import_rec, options):
        """Data rows of the file, without the header line."""
        _length, rows = import_rec._read_file(options)
        return rows[1:] if options.get('has_headers') else rows

    def _error_messages(self, result):
        """Readable text of the import errors returned by ``execute_import``."""
        errors = []
        for message in result.get('messages') or []:
            if message.get('type') != 'error':
                continue
            rows = message.get('rows') or {}
            if rows.get('from') is not None:
                errors.append(self.env._("Row %(row)s: %(message)s",
                                         row=rows['from'] + 1, message=message.get('message')))
            else:
                errors.append(message.get('message') or '')
        return errors

    def _raise_on_errors(self, result):
        errors = self._error_messages(result)
        if errors or not result.get('ids'):
            raise UserError('\n'.join(errors) or self.env._("No records were imported."))

    @staticmethod
    def _split_xml_id(xml_id):
        """Split an external ID into (module, name); a bare name goes to ``__import__``."""
        if '.' in xml_id:
            return tuple(xml_id.split('.', 1))
        return '__import__', xml_id

    def _check_external_ids(self, values):
        """Refuse external IDs that belong to a module or already exist.

        Instant Import only creates records: pointing an existing external ID
        (e.g. ``base.main_partner``) at the file's data would overwrite that
        record instead.
        """
        xml_ids = {str(value).strip() for value in values if value and str(value).strip()}
        if not xml_ids:
            return
        foreign = sorted(x for x in xml_ids if self._split_xml_id(x)[0] != '__import__')
        if foreign:
            raise UserError(self.env._(
                "External IDs of other modules cannot be imported: %s", ', '.join(foreign)))
        existing = self.env['ir.model.data'].sudo().search([
            ('module', '=', '__import__'),
            ('name', 'in', [self._split_xml_id(x)[1] for x in xml_ids]),
        ])
        if existing:
            raise UserError(self.env._(
                "These external IDs already exist and Instant Import only creates records: %s",
                ', '.join(sorted(existing.mapped('complete_name')))))

    def _missing_required_fields(self, model_name, imported_fields):
        """Required stored fields that are not imported and get no value from Odoo."""
        Model = self.env[model_name]
        candidates = [
            name for name, field in Model._fields.items()
            if field.required and field.store and not field.compute and not field.related
            and field.default is None and name not in imported_fields
            and name not in models.MAGIC_COLUMNS
        ]
        if not candidates:
            return []
        defaults = Model.default_get(candidates)
        return sorted(name for name in candidates if defaults.get(name) in (None, False))

    def _create_activities(self, model, record_ids, field_paths, rows, activity_index):
        """Schedule one activity per imported record from the activity column.

        A row starts a new record when one of its main (non one2many) columns
        has a value, as in ``Model.load()``; the activity is read from that row.
        """
        Model = self.env[model]
        if not hasattr(Model, 'activity_schedule'):
            return
        main_indexes = [i for i, path in enumerate(field_paths) if path and '/' not in path]
        start_rows = [row for row in rows if any(i < len(row) and row[i] for i in main_indexes)]
        ActivityType = self.env['mail.activity.type']
        for record, row in zip(Model.browse(record_ids), start_rows):
            value = str(row[activity_index]).strip() if activity_index < len(row) else ''
            if not value:
                continue
            type_name = ACTIVITY_TYPE_ALIASES.get(value.lower(), value)
            activity_type = ActivityType.search(
                [('name', '=ilike', type_name), ('res_model', 'in', (False, model))], limit=1,
            ) or ActivityType.search([('res_model', 'in', (False, model))], limit=1)
            if activity_type:
                record.activity_schedule(activity_type_id=activity_type.id,
                                         summary=activity_type.name, user_id=self.env.uid)
