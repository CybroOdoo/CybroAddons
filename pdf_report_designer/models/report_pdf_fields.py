# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prasanna Kumara B (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class ReportPdfFields(models.Model):
    """Class to handle fields of selected model in report form"""
    _name = 'report.pdf.field'
    _description = 'PDF Reports Fields'

    report_field_id = fields.Many2one('ir.model.fields',
                                      string="Field", help="Choose fields")
    report_id = fields.Many2one('report.pdf',
                                string="Relation Field",
                                help="Relational Field")
    field_label = fields.Char(string="Field Label",
                              related='report_field_id.field_description',
                              help="Label for field")
    field_type = fields.Selection(string="Field Type",
                                  related='report_field_id.ttype',
                                  help="Type of the field")
    field_model = fields.Char(string="Field Type",
                              related='report_field_id.model', help="Model")
    field_relation = fields.Char(string="Field Type",
                                 related='report_field_id.relation',
                                 help="Field relation")
    one2many_model_field_ids = fields.Many2many('ir.model.fields',
                                                'ir_model_fields_report_'
                                                'pdf_field_rel',
                                                'one2many_id',
                                                'many2many_ids',
                                                string="Model Fields",
                                                help="One2many model fields")

    @api.onchange('report_field_id')
    def _onchange_report_field_id(self):
        """
        Returns a domain on change of report_field_id to itself. @param self:
        object pointer. @return: returns a domain to report_field_id field
        based on selected model.
        """
        if self.report_id.model_id:
            return {
                'domain': {
                    'report_field_id': [
                        ('model_id', '=', self.report_id.model_id.id),
                        ('store', '=', True)],
                }
            }
