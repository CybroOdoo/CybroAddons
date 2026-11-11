# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys (odoo@cybrosys.com)
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
###############################################################################
import base64
import binascii
import csv
import io
import logging

import openpyxl

from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ImportMeetingChecklist(models.TransientModel):
    """To import calendar meeting checklist,
      here we can upload the files in csv or xlsx format."""
    _name = 'import.meeting.checklist'
    _description = 'Import Meeting checklist from excel and csv.'

    file_type = fields.Selection(
        [('csv', 'CSV File'), ('xls', 'EXCEL File')],
        string='Import File Type', default='csv',
        help="Choose the type of the file.")
    file_content = fields.Binary(attachment=True,
                                 help="Upload the file.")
    filename = fields.Char(string='File Name', required=True,
                           help="File name of uploaded file content.")

    def _get_decoded_file_content(self):
        """Return the uploaded file as bytes, whatever form the binary
        value comes in (attachment value, base64 text or data URI)."""
        if not self.file_content:
            raise UserError(self.env._('Please upload a file to import.'))
        content = self.file_content
        # Odoo BinaryValue / BinaryValueAttachment objects hold the raw bytes.
        if hasattr(content, 'content'):
            return content.content
        if isinstance(content, str):
            content = content.encode('utf-8')
        if isinstance(content, bytes):
            # Strip a data URI prefix (e.g. 'data:text/csv;base64,').
            if b';base64,' in content:
                content = content.split(b';base64,')[-1]
            elif b',' in content and content.startswith(b'data:'):
                content = content.split(b',', 1)[1]
            content = content.strip()
            missing_padding = len(content) % 4
            if missing_padding:
                content += b'=' * (4 - missing_padding)
            try:
                return base64.b64decode(content)
            except (binascii.Error, ValueError):
                _logger.debug("Uploaded checklist file is not base64; using it as is")
                return content
        return content

    def _has_header(self, first_row):
        """Check if the first row contains field header names using exact cell matching."""
        if not first_row:
            return False
        clean = [str(c).strip().lower() for c in first_row if c is not None]
        candidates = {'id', 'external id', 'external_id', 'id/id', 'name', 'description', 'desc', 'title', 'checklist', 'details'}
        return any(cell in candidates for cell in clean)

    def _get_field_indices(self, header_row):
        """Determine the index of 'name' and 'description' columns based on header row."""
        if not header_row:
            return 0, 1
        clean_header = [str(col).strip().lower() if col is not None else '' for col in header_row]

        name_idx = None
        desc_idx = None

        for idx, col in enumerate(clean_header):
            if col in ('name', 'title', 'checklist name', 'checklist'):
                name_idx = idx
                break

        for idx, col in enumerate(clean_header):
            if col in ('description', 'desc', 'details', 'detail'):
                desc_idx = idx
                break

        is_id_header = clean_header[0] in ('id', 'external id', 'external_id', 'id/id') if clean_header else False

        if name_idx is None:
            name_idx = 1 if is_id_header and len(clean_header) > 1 else 0

        if desc_idx is None:
            desc_idx = name_idx + 1 if len(clean_header) > name_idx + 1 else None

        return name_idx, desc_idx

    def _extract_row_data(self, row, name_idx, desc_idx):
        """Extract name and description from a row, handling external IDs if present."""
        if not row:
            return False, False

        first_col = str(row[0]).strip() if row[0] is not None else ''
        if first_col.startswith(('__export__', '__import__')):
            n_idx = 1 if len(row) > 1 and str(row[1]).strip() else 0
            d_idx = 2 if len(row) > 2 else (1 if n_idx == 2 else (1 if n_idx == 0 else None))
        else:
            n_idx = name_idx
            d_idx = desc_idx

        name = row[n_idx] if n_idx is not None and len(row) > n_idx and row[n_idx] is not None else False
        description = row[d_idx] if d_idx is not None and len(row) > d_idx and row[d_idx] is not None else False

        if not name and first_col:
            name = first_col

        if name:
            name = str(name).strip()
        if description:
            description = str(description).strip()

        return name, description

    def _import_rows(self, rows):
        """Create or update one meeting checklist per row and return the
        notification to show. Runs with the user's own rights."""
        if not rows:
            return self._notify(self.env._("File is empty!"), 'warning')
        header = rows[0]
        has_header = self._has_header(header)
        name_idx, desc_idx = self._get_field_indices(header if has_header else [])
        Checklist = self.env['meeting.checklist']
        for row in rows[1:] if has_header else rows:
            name, description = self._extract_row_data(row, name_idx, desc_idx)
            if not name:
                continue
            existing = Checklist.search([('name', '=', name)], limit=1)
            if not existing:
                Checklist.create({'name': name, 'description': description or ''})
            elif description:
                existing.write({'description': description})
        return self._notify(self.env._("Successfully Imported!"), 'success', reload=True)

    def _notify(self, message, notification_type, reload=False):
        """Client action showing a notification, optionally reloading after it."""
        params = {'message': message, 'type': notification_type, 'sticky': False}
        if reload:
            params['next'] = {'type': 'ir.actions.client', 'tag': 'reload'}
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': params}

    def action_import_meeting_checklist_xlsx(self):
        """To import meeting checklist in xlsx format,
         it will create a new checklist from this file."""
        file_data = self._get_decoded_file_content()
        try:
            book = openpyxl.load_workbook(filename=io.BytesIO(file_data), data_only=True)
        except Exception as exc:
            raise UserError(self.env._('Only excel files are supported.')) from exc
        rows = [[cell.value for cell in row] for row in book.active.rows]
        # Skip blank rows, as the csv import does.
        rows = [row for row in rows if any(value not in (None, '') for value in row)]
        return self._import_rows(rows)

    def action_import_meeting_checklist_csv(self):
        """To import task checklist in csv format,
         it will create a new checklist from this file"""
        file_data = self._get_decoded_file_content()
        try:
            reader = csv.reader(io.StringIO(file_data.decode("utf-8-sig")), delimiter=',')
            rows = [row for row in reader if any(cell.strip() for cell in row if cell)]
        except (UnicodeDecodeError, csv.Error) as exc:
            raise UserError(self.env._('Only csv files are supported.')) from exc
        return self._import_rows(rows)
