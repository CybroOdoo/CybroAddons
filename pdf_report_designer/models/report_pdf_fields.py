# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReportPdfFields(models.Model):
    """Class to handle fields of selected model in report form"""
    _name = 'report.pdf.field'
    _description = 'PDF Reports Fields'

    report_field_id = fields.Many2one('ir.model.fields',
                                      string="Field", help="Choose fields",
                                      domain="[('id', 'in', field_value_ids)]")
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
    field_value_ids = fields.Many2many('ir.model.fields',
                                       string='Fields',
                                       help="Storing Values",
                                       compute='_compute_field_value_ids')
    one2many_model_field_ids = fields.Many2many('ir.model.fields',
                                                'ir_model_fields_report_'
                                                'pdf_field_rel',
                                                'one2many_id',
                                                'many2many_ids',
                                                string="Model Fields",
                                                help="One2many model fields",
                                                )

    @api.depends('report_id.model_id')
    def _compute_field_value_ids(self):
        """
        Compute method to populate `field_value_ids` based on the model
        specified in `report_id`.

        This method searches for fields in the `ir.model.fields` model
        that belong to the specified `model_id` in the report and are
        stored in the database. The resulting field IDs are assigned to
        the `field_value_ids` field of the current record.
        """
        for rec in self:
            if rec.report_id.model_id:
                model_field_ids = self.env['ir.model.fields'].search([
                    ('model_id', '=', rec.report_id.model_id.id),
                    ('store', '=', True)
                ]).ids
                rec.field_value_ids = [(6, 0, model_field_ids)]

    @api.onchange('report_field_id')
    def _onchange_report_field_id(self):
        """
        Onchange method to ensure the model is set in the report before
        allowing selection of a report field.
        """
        if not self.report_id.model_id:
            raise (UserError
                   (_("Please set the model in the report before selecting a "
                      "report field.")))
