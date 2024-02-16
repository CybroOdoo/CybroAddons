# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class CustomReportFields(models.Model):
    """Custom report fields model.
    Used to define custom fields associated with custom reports."""
    _name = 'custom.report.fields'
    _description = 'Custom Report Fields'

    custom_field_id = fields.Many2one('ir.model.fields',
                                      string='Custom Report',
                                      required=True, ondelete='cascade',
                                      domain="[('model_id', '=', model_id)]",
                                      help="Field adding to the report")
    report_id = fields.Many2one('custom.report', string='Parent',
                                ondelete='cascade')
    model_id = fields.Many2one('ir.model',
                               related='report_id.model_id',
                               help="Model for the report")
    label = fields.Char(string='Label',
                        help="Label of the column in the report")
    row = fields.Boolean(string='Row', default=0,
                         help="Define is the field is row")
    measure = fields.Boolean(string='Measure', default=0,
                             help="Define is the field is measure")
    measurable = fields.Boolean(string='Measurable', default=0,
                                help="Define is the field is row")
    rowable = fields.Boolean(string='Row able', default=0,
                             help="Define is the field is measure")

    @api.onchange('custom_field_id')
    def onchange_custom_field_id(self):
        """Update field values based on the selected custom field."""
        self.label = self.custom_field_id.field_description
        if self.custom_field_id.ttype in ['float', 'integer', 'many2one', 'monetary']:
            self.measurable = True
        if self.custom_field_id.ttype in ['many2many', 'one2many']:
            self.rowable = True
