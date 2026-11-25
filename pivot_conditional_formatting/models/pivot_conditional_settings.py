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
#############################################################################
"""Models for setting conditional formatting rules in settings"""
from odoo import api, fields, models


class PivotConditionalSetting(models.Model):
    """Model Class for choosing the model and view to set the default rules"""
    _name = 'pivot.conditional.settings'
    _description = 'Pivot conditional setting'
    _rec_name = "model_id"

    model_id = fields.Many2one('ir.model',
                               help="The model to set the rules for")
    view_id = fields.Many2one('ir.ui.view',
                              help="Pivot view of the model")
    rules_ids = fields.One2many(
        'conditional.rules', 'conditional_id',
        help="List View Showing details of different rules")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 help="Company id related to the Pivot "
                                      "Condition setting")
    view_id_domain = fields.Json(compute="_compute_view_id_domain")

    @api.depends('model_id')
    def _compute_view_id_domain(self):
        """
        This method updates the domain of the 'view_id' field to filter
        records based on the selected model and view type as 'pivot'.
        """
        for rec in self:
            model_name = rec.model_id.model if rec.model_id else False
            rec.view_id_domain = [
                ('model', '=', model_name),
                ('type', '=', 'pivot'),
            ]
