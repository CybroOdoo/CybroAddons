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
import json
import textwrap
from datetime import datetime

from odoo import api, fields, models


class SurveyUserInputLine(models.Model):
    """Inherited user input line to add custom answer types."""

    _inherit = 'survey.user_input.line'

    answer_type = fields.Selection(
        selection_add=[
            ('url', 'URL'),
            ('many2one', 'Many2one'),
            ('many2many', 'Many2many'),
            ('week', 'Week'),
            ('color', 'Color'),
            ('month', 'Month'),
            ('name', 'Name'),
            ('matrix', 'Matrix'),
            ('address', 'Address'),
            ('selection', 'Selection'),
            ('time', 'Time'),
            ('password', 'Password'),
            ('email', 'Email'),
            ('range', 'Range'),
            ('file', 'File'),
            ('qr', 'QR Code'),
            ('barcode', 'Barcode'),
        ],
        help="Custom answer types.",
    )
    value_url = fields.Char(
        string='User URL',
        help="Answer for URL question.",
    )
    value_email = fields.Char(
        string='User Email',
        help="Answer for Email question.",
    )
    value_week = fields.Char(
        string='User Week',
        help="Answer for Week question.",
    )
    value_color = fields.Char(
        string='User Color',
        help="Answer for Color question.",
    )
    value_many2one = fields.Char(
        string='Survey Many2one',
        help="Stored record ID for Many2one question.",
    )
    value_many2one_option = fields.Char(
        string='Many2one Selected',
        help="Selected display value for Many2one question.",
    )
    value_many2many = fields.Char(
        string='Survey Many2many',
        help="Answer for Many2many question.",
    )
    value_time = fields.Float(
        string='Time Value',
        help="Answer for Time question.",
    )
    value_matrix = fields.Text(
        string='Custom Matrix Values',
        help="Answer for Custom Matrix question.",
    )
    value_selection = fields.Char(
        string='User Selection',
        help="Answer for Selection question.",
    )
    value_password = fields.Char(
        string='Password Value',
        help="Answer for Password question.",
    )
    value_range = fields.Char(
        string='Range Value',
        help="Answer for Range question.",
    )
    value_file = fields.Many2one(
        'ir.attachment',
        string='Survey File',
        help="Attachment uploaded for File question.",
    )
    filename = fields.Char(string='File', help="Attachment file name.")
    file_data = fields.Binary(
        help="Attachment file data.",
        related="value_file.raw",
    )
    value_month = fields.Char(
        string='Month Value',
        help="Answer for Month question.",
    )
    value_address = fields.Text(
        string='Address Value',
        help="Answer for Address question.",
    )
    value_name = fields.Text(
        string='Name Values',
        help="Answer for Full Name question.",
    )
    value_qr = fields.Char(
        string='QR Values',
        help="Answer for QR Code question.",
    )
    value_barcode = fields.Char(
        string='Barcode Values',
        help="Answer for Barcode question.",
    )

    def get_value_time(self):
        """Return formatted HH:MM answer for time-type questions."""
        line = self[:1]
        if line and line.value_time:
            time_str = f"{line.value_time:.2f}".replace('.', ':')
            return datetime.strptime(time_str, "%H:%M").strftime("%H:%M")
        return None

    def get_value_address(self, field):
        """Return requested address sub-field value for address questions."""
        line = self[:1]
        if not line or not line.value_address:
            return ''
        try:
            data = json.loads(line.value_address.replace("'", "\""))
        except (json.JSONDecodeError, TypeError):
            return ''
        if data:
            return data.get(f'{line.question_id.id}-{field}', '')
        return ''

    def get_value_matrix(self, item):
        """Return cell value for custom matrix questions."""
        line = self[:1]
        if not line or not line.value_matrix:
            return None
        try:
            data = json.loads(line.value_matrix)
        except (json.JSONDecodeError, TypeError):
            return None
        if data:
            return data.get(f'{item}-{line.question_id.id}')
        return None

    def get_value_name(self, field):
        """Return requested name component for full name questions."""
        line = self[:1]
        if not line or not line.value_name:
            return ''
        try:
            data = json.loads(line.value_name)
        except (json.JSONDecodeError, TypeError):
            return ''
        if data:
            return data.get(f'{line.question_id.id}-{field}', '')
        return ''

    @api.depends('answer_type')
    def _compute_display_name(self):
        """Compute display name across standard and custom answer types."""
        for line in self:
            if line.answer_type == 'char_box':
                line.display_name = line.value_char_box
            elif line.answer_type == 'text_box' and line.value_text_box:
                line.display_name = textwrap.shorten(
                    line.value_text_box,
                    width=50,
                    placeholder=" [...]",
                )
            elif line.answer_type == 'numerical_box':
                line.display_name = line.value_numerical_box
            elif line.answer_type == 'date':
                line.display_name = fields.Date.to_string(line.value_date)
            elif line.answer_type == 'datetime':
                line.display_name = fields.Datetime.to_string(line.value_datetime)
            elif line.answer_type == 'time':
                line.display_name = line.value_time
            elif line.answer_type == 'month':
                line.display_name = line.value_month
            elif line.answer_type == 'address':
                line.display_name = line.value_address
            elif line.answer_type == 'name':
                line.display_name = line.value_name
            elif line.answer_type == 'url':
                line.display_name = line.value_url
            elif line.answer_type == 'many2one':
                line.display_name = line.value_many2one_option
            elif line.answer_type == 'many2many':
                line.display_name = line.value_many2many
            elif line.answer_type == 'week':
                line.display_name = line.value_week
            elif line.answer_type == 'email':
                line.display_name = line.value_email
            elif line.answer_type == 'range':
                line.display_name = line.value_range
            elif line.answer_type == 'matrix':
                line.display_name = line.value_matrix
            elif line.answer_type == 'password':
                line.display_name = line.value_password
            elif line.answer_type == 'color':
                line.display_name = line.value_color
            elif line.answer_type == 'selection':
                line.display_name = line.value_selection
            elif line.answer_type == 'barcode':
                line.display_name = line.value_barcode
            elif line.answer_type == 'qr':
                line.display_name = line.value_qr
            elif line.answer_type == 'file':
                line.display_name = line.filename
            elif line.answer_type == 'suggestion':
                if line.matrix_row_id:
                    line.display_name = (
                        f'{line.suggested_answer_id.value}: '
                        f'{line.matrix_row_id.value}'
                    )
                else:
                    line.display_name = line.suggested_answer_id.value
            if not line.display_name:
                line.display_name = line.env._('Skipped')
