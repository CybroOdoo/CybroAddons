# -*- coding: utf-8 -*-
#############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Sreerag PM(odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU LESSER
# GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
# You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
# (LGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class CustomReportFields(models.Model):
    """
    Custom report fields model.
    Used to define custom fields associated with custom reports."""

    _name = 'custom.report.fields'
    _description = 'Custom Report Fields'

    custom_field_id = fields.Many2one('ir.model.fields',
                                      string='Custom Report Field',
                                      required=True, ondelete='cascade',
                                      help="Select the custom field from the "
                                           "model to add to the report.")
    report_id = fields.Many2one('custom.report',
                                string='Parent Report', ondelete='cascade',
                                help="The parent custom report to which "
                                     "this field belongs.")
    label = fields.Char(string='Label',
                        help="The label for the custom field in the report.")
    row = fields.Boolean(string='Row',
                         help="Check this box if this field should be used "
                              "for rows in the report.")
    measure = fields.Boolean(string='Measure',
                             help="Check this box if this field should be "
                                  "used as a measure in the report.")
    measurable = fields.Boolean(string='Measurable',
                                help="Check this box if this field is "
                                     "measurable.")
    rowable = fields.Boolean(string='Rowable',
                             help="Check this box if this field is rowable "
                                  "('one2many' and 'many2many' fields).")

    @api.onchange('custom_field_id')
    def onchange_custom_field_id(self):
        """
        Update field values based on the selected custom field."""

        model_id = self.env.context.get('parent_id')
        self.label = self.custom_field_id.field_description
        self.report_id = model_id
        if self.custom_field_id.ttype in ['float', 'integer', 'many2one',
                                          'monetary']:
            self.measurable = True
        if self.custom_field_id.ttype in ['many2many', 'one2many']:
            self.rowable = True
        return {'domain': {'custom_field_id': [('model_id.id', '=', model_id)]}}
