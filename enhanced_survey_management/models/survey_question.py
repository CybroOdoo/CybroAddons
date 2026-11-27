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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SurveyQuestion(models.Model):
    """Inherited survey.question to add custom question types."""

    _inherit = 'survey.question'

    selection_ids = fields.One2many(
        'question.selection',
        'question_id',
        string='Select',
        help="Options displayed for selection-type questions.",
    )
    question_type = fields.Selection(
        selection_add=[
            ('time', 'Time'),
            ('month', 'Month'),
            ('name', 'Name'),
            ('address', 'Address'),
            ('email', 'Email'),
            ('password', 'Password'),
            ('qr', 'QR Code'),
            ('url', 'URL'),
            ('week', 'Week'),
            ('color', 'Color'),
            ('range', 'Range'),
            ('many2one', 'Many2one'),
            ('file', 'Upload File'),
            ('many2many', 'Many2many'),
            ('selection', 'Selection'),
            ('barcode', 'Barcode'),
        ],
        help="Survey supported question types.",
    )
    matrix_subtype = fields.Selection(
        selection_add=[('custom', 'Custom Matrix')],
        help="Matrix selection type for the question.",
    )
    model_id = fields.Many2one(
        'ir.model',
        domain=[('transient', '=', False)],
        help="Target model for Many2one and Many2many questions.",
    )
    range_min = fields.Integer(
        string='Min',
        help="Minimum range value for range questions.",
    )
    range_max = fields.Integer(
        string='Max',
        help="Maximum range value for range questions.",
    )
    qrcode = fields.Text(help="Value encoded into the survey QR code.")
    barcode = fields.Char(help="12-digit EAN-13 barcode number.")

    @api.constrains('barcode')
    def _check_barcode(self):
        """Restrict barcode to exactly 12 numeric digits."""
        for record in self:
            if record.barcode:
                if len(record.barcode) < 12:
                    raise ValidationError(
                        self.env._("Barcode must be at least 12 digits."),
                    )
                if len(record.barcode) > 12:
                    raise ValidationError(
                        self.env._("Barcode cannot exceed 12 digits."),
                    )
                if not record.barcode.isdigit():
                    raise ValidationError(
                        self.env._("Only digits are allowed."),
                    )

    def _onchange_barcode(self):
        """Compatibility method for barcode validation."""
        self._check_barcode()

    def get_selection_values(self):
        """Return options for selection-type questions."""
        return self.selection_ids

    def prepare_model_id(self, model):
        """Return selectable record options for Many2one and Many2many questions."""
        target_model_name = model.model if model else (
            self.model_id.model if self.model_id else False
        )
        if not target_model_name or target_model_name not in self.env:
            return []

        target_model = self.env[target_model_name]
        if target_model._abstract:
            return []

        rec_field = (
            target_model._rec_name
            if target_model._rec_name in target_model._fields
            else 'display_name'
        )
        records = target_model.sudo().search_read([], [rec_field], limit=100)
        return [{'id': rec['id'], 'name': rec[rec_field]} for rec in records]
